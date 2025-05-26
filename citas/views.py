from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from .models import Paciente, Medico, Cita, HistorialCita
from .serializers import PacienteSerializer, MedicoSerializer, CitaSerializer, HistorialCitaSerializer 
from django.views.generic import TemplateView
from django.http import Http404

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
    queryset = Cita.objects.all().order_by('fecha_hora_cita')
    serializer_class = CitaSerializer

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

class IndexView(TemplateView):
    template_name = "citas/principal.html"

class CalificarView(TemplateView):
    template_name = "citas/calificar.html"

class HabilitarHoraView(TemplateView):
    template_name = "citas/Habilitar_hora.html"

class DetalleCitaView(TemplateView):
    template_name = "citas/detalle_cita.html"