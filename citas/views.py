from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets
from .models import Paciente, Medico, Cita, HistorialCita
from .serializers import PacienteSerializer, MedicoSerializer, CitaSerializer, HistorialCitaSerializer 

class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer

class MedicoViewSet(viewsets.ModelViewSet):
    queryset = Medico.objects.all()
    serializer_class = MedicoSerializer

class HistorialCitaViewSet(viewsets.ModelViewSet): # Nuevo ViewSet
    queryset = HistorialCita.objects.all()
    serializer_class = HistorialCitaSerializer

class CitaViewSet(viewsets.ModelViewSet):
    queryset = Cita.objects.all().order_by('fecha_hora_cita')
    serializer_class = CitaSerializer