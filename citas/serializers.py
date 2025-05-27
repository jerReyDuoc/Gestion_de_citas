from rest_framework import serializers
from .models import Paciente, Medico, Cita, HistorialCita, Disponibilidad
from django.utils import timezone
from datetime import timedelta, datetime

class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = '__all__'

class MedicoSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField(read_only=True)
    apellido = serializers.SerializerMethodField(read_only=True)
    especialidad = serializers.CharField(source='especialidad_texto', read_only=True) # Mapea a especialidad_texto
    id_med = serializers.IntegerField(source='id', read_only=True) # El JS usa id_med

    class Meta:
        model = Medico
        fields = ['id_med', 'nombre_completo', 'nombre', 'apellido', 'especialidad'] # Asegúrate que 'id' se mapea a 'id_med' para el JS

    def get_nombre(self, obj):
        parts = obj.nombre_completo.split(' ', 1)
        return parts[0] if parts else obj.nombre_completo

    def get_apellido(self, obj):
        parts = obj.nombre_completo.split(' ', 1)
        return parts[1] if len(parts) > 1 else ''


class HistorialCitaSerializer(serializers.ModelSerializer): 
    class Meta:
        model = HistorialCita
        fields = '__all__'

class CitaSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(source='medico.nombre_completo', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    pro_veri_cita_display = serializers.CharField(source='get_pro_veri_cita_display', read_only=True)
    medico_id_val = serializers.IntegerField(source='medico.id', read_only=True)

    class Meta:
        model = Cita
        # ... (tus fields y extra_kwargs como antes) ...
        fields = [
            'id', 'nombre_paciente_temporal', 'estado','estado_display', 'pro_veri_cita','pro_veri_cita_display',
            'fecha_hora_cita', 'medico','medico_id_val', 'medico_nombre', 'historial_cita',
            'duracion_minutos', 'motivo', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['creado_en', 'actualizado_en']
        extra_kwargs = {
            'medico': {'write_only': True,'required': True}
        }

    def validate_fecha_hora_cita(self, value):
        # Esta validación básica sigue siendo útil
        if value <= timezone.now(): # Usar timezone.now() si USE_TZ=True
            raise serializers.ValidationError("La fecha y hora de la cita debe ser en el futuro.")
        return value

    def validate(self, data):
        # Obtener los datos relevantes para la validación
        # Si es una actualización (self.instance existe), toma el valor del payload (data)
        # o, si no está en el payload, toma el valor existente de la instancia.
        medico = data.get('medico', getattr(self.instance, 'medico', None))
        fecha_hora_cita_propuesta = data.get('fecha_hora_cita', getattr(self.instance, 'fecha_hora_cita', None))
        # Usar el default del modelo (30) si no se provee y no es una actualización con valor existente
        duracion_minutos_propuesta = data.get('duracion_minutos', getattr(self.instance, 'duracion_minutos', Cita._meta.get_field('duracion_minutos').default))


        if not (medico and fecha_hora_cita_propuesta and duracion_minutos_propuesta):
            # Si faltan datos cruciales para estas validaciones y no es un PATCH parcial para otros campos
            return data # Dejar que las validaciones a nivel de campo manejen esto

        # --- REGLA 1: Cita debe caer dentro de un bloque de Disponibilidad del Médico ---
        fecha_propuesta_date_obj = fecha_hora_cita_propuesta.date()
        hora_propuesta_time_obj = fecha_hora_cita_propuesta.time()
        
        # Calcular la hora de fin de la cita propuesta
        # Necesitamos convertir fecha_hora_cita_propuesta a un objeto datetime si no lo es
        # para poder sumarle timedelta. Si viene de un DateTimeField de DRF, ya es un datetime.
        cita_fin_dt_propuesta = fecha_hora_cita_propuesta + timedelta(minutes=duracion_minutos_propuesta)
        hora_fin_propuesta_time_obj = cita_fin_dt_propuesta.time()

        # Consultar los bloques de disponibilidad del médico para la fecha de la cita
        disponibilidades_del_dia = Disponibilidad.objects.filter(
            medico=medico,
            fecha=fecha_propuesta_date_obj
        )

        slot_valido_encontrado = False
        for slot in disponibilidades_del_dia:
            # Comparamos solo las horas dentro del día correcto
            if slot.hora_inicio <= hora_propuesta_time_obj and \
               slot.hora_fin >= hora_fin_propuesta_time_obj:
                # Adicionalmente, si la cita termina justo en la hora_fin del slot Y
                # la cita no se pasa al día siguiente (ya cubierto si hora_fin >= hora_fin_propuesta)
                if slot.hora_fin == hora_fin_propuesta_time_obj or \
                   (fecha_propuesta_date_obj == cita_fin_dt_propuesta.date()): # Asegura que no cruce medianoche
                    slot_valido_encontrado = True
                    break
        
        if not slot_valido_encontrado:
            raise serializers.ValidationError(
                f"El médico no está disponible en la fecha y hora solicitadas ({fecha_hora_cita_propuesta.strftime('%Y-%m-%d %H:%M')}) "
                f"o la duración de {duracion_minutos_propuesta} minutos excede el bloque de disponibilidad registrado."
            )

        # --- REGLA 2: No solapamiento con OTRAS Citas (excluyendo citas canceladas) ---
        # (Esta lógica es similar a la que teníamos, pero ahora se ejecuta DESPUÉS de confirmar
        # que la cita está dentro de un bloque de disponibilidad general del médico)
        
        citas_existentes_conflictivas = Cita.objects.filter(
            medico=medico,
            # Filtro para citas cuya ventana de tiempo se solapa con la nueva cita
            # (InicioExistente < FinNueva) Y (FinExistente > InicioNueva)
            fecha_hora_cita__lt=cita_fin_dt_propuesta, # Inicio de cita existente es ANTES de que termine la nueva
            # Para calcular el fin de la cita existente, no podemos usar F() object directamente con timedelta en filter
            # por lo que este filtro puede ser más complejo o requerir iteración/anotación si hay muchas citas
            # Por ahora, vamos a simplificar o hacerlo en dos pasos:
        ).exclude(estado='CANCELADA')

        # Si estamos actualizando una cita, debemos excluirla de la comprobación de solapamiento
        if self.instance and self.instance.pk:
            citas_existentes_conflictivas = citas_existentes_conflictivas.exclude(pk=self.instance.pk)

        for cita_existente in citas_existentes_conflictivas:
            existente_fecha_fin = cita_existente.fecha_hora_cita + timedelta(minutes=cita_existente.duracion_minutos)
            # Comprobación de solapamiento: (Inicio1 < Fin2) y (Fin1 > Inicio2)
            if (fecha_hora_cita_propuesta < existente_fecha_fin and \
                cita_fin_dt_propuesta > cita_existente.fecha_hora_cita):
                raise serializers.ValidationError(
                    f"Conflicto: El médico ya tiene la cita {cita_existente.id} de "
                    f"{cita_existente.fecha_hora_cita.strftime('%H:%M')} a {existente_fecha_fin.strftime('%H:%M')} "
                    f"que se solapa con el horario solicitado."
                )

        return data