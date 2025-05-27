from django.db import models
from django.utils import timezone

# Create your models here.

class Paciente(models.Model):
    nombre_completo = models.CharField(max_length=200)

    def __str__(self):
        return self.nombre_completo
    
    class Meta:
        #managed = False
        #db_table = 'Paciente'
        pass
    
class Medico(models.Model):
    nombre_completo = models.CharField(max_length=200)
    especialidad_texto = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nombre_completo
    
    class Meta:
        #managed = False
        #db_table = 'Medico'
        pass
    
class HistorialCita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historiales_cita')
    estado_consulta = models.CharField(max_length=100, null=True, blank=True)
    fecha_de_inicio = models.DateTimeField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Historial para {self.paciente} - Consulta iniciada: {self.fecha_de_inicio}"

    class Meta:
        #managed = False
        #db_table = 'Historial_Cita'
        pass


class Cita(models.Model):
    # nombre Varchar2(60) - Nombre del paciente para citas sin login
    nombre_paciente_temporal = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        help_text="Nombre del paciente si la cita es sin registro previo."
    )

    # estado varchar2(100)
    ESTADO_CITA_CHOICES = [
        ('PROGRAMADA', 'Programada'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
        # Puedes añadir más si los valores de Oracle son diferentes
    ]
    estado = models.CharField(max_length=100, choices=ESTADO_CITA_CHOICES, default='PROGRAMADA')

    # pro_veri_cita varchar2(100)
    PRO_VERI_CITA_CHOICES = [
        ('SOLICITADA', 'Cita solicitada'),
        ('CONFIRMACION_PENDIENTE', 'Confirmación pendiente'),
        ('RESPUESTA_OBTENIDA', 'Respuesta obtenida'),
    ]
    pro_veri_cita = models.CharField(
        max_length=100,
        choices=PRO_VERI_CITA_CHOICES,
        null=True, blank=True # O un default si siempre tiene valor
    )

    # fecha DATE
    fecha_hora_cita = models.DateTimeField(db_column='fecha')

    # id_med
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='citas', db_column='id_med')

    # id_historial
    historial_cita = models.ForeignKey(
        HistorialCita,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cita_asociada',
        db_column='id_historial'
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    duracion_minutos = models.IntegerField(default=30)

    motivo = models.TextField(blank=True, null=True)

    def __str__(self):
        paciente_display = self.nombre_paciente_temporal or str(self.historial_cita.paciente if self.historial_cita else "Paciente no especificado")
        return f"Cita para {paciente_display} con {self.medico} el {self.fecha_hora_cita.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['fecha_hora_cita']
        #managed =  False
        #db_table = 'CITA'

        pass

class Disponibilidad(models.Model):
    # En Oracle, el ID de esta tabla es 'id'. Django lo crea automáticamente.
    # Para mapear a Oracle, si el ID se llama 'id_disponibilidad' y es PK:
    # id_disponibilidad = models.AutoField(primary_key=True, db_column='id_disponibilidad_oracle') # Ejemplo
    # O si el 'id' autogenerado por Django debe mapear a 'id' en Oracle:
    # id = models.AutoField(primary_key=True, db_column='id')

    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='disponibilidades') # Mapea a 'id_med'
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    creado_en = models.DateTimeField(auto_now_add=True) # Opcional, si quieres auditoría
    actualizado_en = models.DateTimeField(auto_now=True) # Opcional

    def __str__(self):
        return f"Dr. {self.medico.nombre_completo if self.medico else 'N/A'} disponible el {self.fecha.strftime('%Y-%m-%d')} de {self.hora_inicio.strftime('%H:%M')} a {self.hora_fin.strftime('%H:%M')}"

    class Meta:
        verbose_name_plural = "Disponibilidades"
        unique_together = ('medico', 'fecha', 'hora_inicio') # Un médico no puede tener el mismo slot de inicio dos veces
        #db_table = 'DISPONIBILIDAD'
        #managed = False 
        pass