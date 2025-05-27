from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.utils import timezone
import pytz
from rest_framework import viewsets
from .models import Paciente, Medico, Cita, HistorialCita, Disponibilidad
from .serializers import PacienteSerializer, MedicoSerializer, CitaSerializer, HistorialCitaSerializer 
from django.views.generic import TemplateView
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta, time 
from django_filters.rest_framework import DjangoFilterBackend

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer

class MedicoViewSet(viewsets.ModelViewSet):
    queryset = Medico.objects.all()
    serializer_class = MedicoSerializer

class HistorialCitaViewSet(viewsets.ModelViewSet):
    queryset = HistorialCita.objects.all()
    serializer_class = HistorialCitaSerializer

class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.all().order_by('-fecha_hora_cita') 
    serializer_class = CitaSerializer
    filter_backends = [DjangoFilterBackend] 
    filterset_fields = ['estado', 'medico']

def vista_historial_paciente(request):
    paciente_buscado = None
    historial_con_citas = []
    paciente_id = request.GET.get('id_paciente_form')

    if paciente_id:
        try:
            paciente_id_int = int(paciente_id)
            paciente_buscado = get_object_or_404(Paciente, pk=paciente_id_int)

            historiales = HistorialCita.objects.filter(paciente=paciente_buscado).order_by('-fecha_de_inicio','-creado_en')

            for x in historiales:
                cita_info = x.cita_asociada.first()
                historial_con_citas.append({
                    'historial': x,
                    'cita_asociada': cita_info
                })
        except ValueError:
            pass
        except Http404:
            paciente_buscado = None

    
    context = {
        'paciente': paciente_buscado,
        'historial_con_citas': historial_con_citas,
        'paciente_id_buscado': paciente_id if paciente_id else '',
        'titulo_pagina': 'Buscar Historial de Paciente'
    }

    return render(request,'citas/historial_paciente.html', context)

def vista_detalle_cita(request):
    cita_encontrada = None
    error_message = None
    cita_id_query = request.GET.get('id_cita_form')

    if cita_id_query:
        try:
            cita_id_int = int(cita_id_query)
            cita_encontrada = get_object_or_404(Cita, pk=cita_id_int)
        except ValueError:
            error_message = "El ID de la Cita debe ser un numero"
        except Http404:
            error_message = f"No se encontro una cita con el id {cita_id_query}"
    
    context = {
        'cita': cita_encontrada,
        'cita_id_buscada': cita_id_query if cita_id_query else '',
        'error_message': error_message,
        'titulo_pagina': 'Buscar Detalle de Cita'
    }

    return render(request, 'citas,detalle_cita.html', context)

class IndexView(TemplateView):
    template_name = "citas/principal.html"


class CalificarView(TemplateView):
    template_name = "citas/calificar.html"

class HabilitarHoraView(TemplateView):
    template_name = "citas/Habilitar_hora.html"

class DetalleCitaView(TemplateView):
    template_name = "citas/detalle_cita.html"

class AgendarCitaView(TemplateView):
    template_name = "citas/agendarCita.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Agendar Nueva Cita"
        return context
    
class ListarGestionarCitasView(TemplateView):
    template_name = "citas/listadoCita.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Gestionar Mis Citas"
        context['estados_cita'] = Cita.ESTADO_CITA_CHOICES 
        return context

class MedicoDisponibilidadView(APIView):
    def get(self, request, medico_id):
        try:
            medico = Medico.objects.get(pk=medico_id)
        except Medico.DoesNotExist:
            return Response({"error": "Médico no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        fecha_param = request.query_params.get('fecha_consulta')
        if not fecha_param:
            return Response({"error": "Parámetro 'fecha_consulta' (YYYY-MM-DD) es requerido"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha_consulta_date_obj = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Formato de 'fecha_consulta' inválido. Usar YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            CLINIC_LOCAL_TZ_STR = 'America/Santiago' # Podrías poner esto en settings.py de Django
            clinic_local_tz = pytz.timezone(CLINIC_LOCAL_TZ_STR)
        except pytz.UnknownTimeZoneError:
            print(f"ERROR: Zona horaria local desconocida: {CLINIC_LOCAL_TZ_STR}")
            return Response({"error": "Error interno del servidor (configuración de zona horaria)."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        slots_disponibles_final = []
        duracion_cita_minutos = Cita._meta.get_field('duracion_minutos').default
        
        bloques_disponibilidad = Disponibilidad.objects.filter(medico=medico, fecha=fecha_consulta_date_obj).order_by('hora_inicio')

        if not bloques_disponibilidad.exists():
            return Response([], status=status.HTTP_200_OK)

        local_day_start_naive = datetime.combine(fecha_consulta_date_obj, time.min)
        local_day_end_naive = datetime.combine(fecha_consulta_date_obj, time.max)
        
        aware_local_day_start = clinic_local_tz.localize(local_day_start_naive)
        aware_local_day_end = clinic_local_tz.localize(local_day_end_naive)

        # Usar pytz.utc para la zona horaria UTC
        utc_day_start = aware_local_day_start.astimezone(pytz.utc)
        utc_day_end = aware_local_day_end.astimezone(pytz.utc)
            
        citas_agendadas = Cita.objects.filter(
            medico=medico,
            fecha_hora_cita__gte=utc_day_start,
            fecha_hora_cita__lt=utc_day_end,
        ).exclude(estado='CANCELADA')

        for bloque in bloques_disponibilidad:
            naive_slot_inicio_dt = datetime.combine(bloque.fecha, bloque.hora_inicio)
            naive_slot_fin_dt = datetime.combine(bloque.fecha, bloque.hora_fin)

            aware_slot_inicio_local = clinic_local_tz.localize(naive_slot_inicio_dt)
            aware_slot_fin_local = clinic_local_tz.localize(naive_slot_fin_dt)

            # Usar pytz.utc para la zona horaria UTC
            slot_inicio_utc = aware_slot_inicio_local.astimezone(pytz.utc)
            slot_fin_utc = aware_slot_fin_local.astimezone(pytz.utc)
            
            current_potential_slot_start_utc = slot_inicio_utc

            while current_potential_slot_start_utc + timedelta(minutes=duracion_cita_minutos) <= slot_fin_utc:
                potential_slot_end_utc = current_potential_slot_start_utc + timedelta(minutes=duracion_cita_minutos)
                
                ocupado = False
                for cita in citas_agendadas:
                    cita_fin_existente_utc = cita.fecha_hora_cita + timedelta(minutes=cita.duracion_minutos)
                    
                    if cita.fecha_hora_cita < potential_slot_end_utc and \
                       cita_fin_existente_utc > current_potential_slot_start_utc:
                        ocupado = True
                        break 
                
                if not ocupado:
                    slot_disponible_local_start = current_potential_slot_start_utc.astimezone(clinic_local_tz)
                    slots_disponibles_final.append(slot_disponible_local_start.strftime('%H:%M'))
                
                current_potential_slot_start_utc += timedelta(minutes=duracion_cita_minutos)
        
        slots_time_obj = sorted(list(set(datetime.strptime(s, '%H:%M').time() for s in slots_disponibles_final)))
        slots_str_ordenados = [t.strftime('%H:%M') for t in slots_time_obj]
            
        return Response(slots_str_ordenados, status=status.HTTP_200_OK)