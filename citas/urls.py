from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PacienteViewSet, MedicoViewSet, CitaViewSet, HistorialCitaViewSet

router = DefaultRouter()
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'medicos', MedicoViewSet, basename='medico')
router.register(r'historiales-cita', HistorialCitaViewSet, basename='historialcita')
router.register(r'citas', CitaViewSet, basename='cita') # El endpoint para el modelo Cita se llamará 'citas'

urlpatterns = [
    path('', include(router.urls)),
]