from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PacienteViewSet, MedicoViewSet, CitaViewSet, HistorialCitaViewSet, vista_historial_paciente, IndexView, CalificarView, HabilitarHoraView, DetalleCitaView, AgendarCitaView, MedicoDisponibilidadView, ListarGestionarCitasView

router = DefaultRouter()
router.register(r'pacientes', PacienteViewSet, basename='paciente')
router.register(r'medicos', MedicoViewSet, basename='medico')
router.register(r'historiales-cita', HistorialCitaViewSet, basename='historialcita')
router.register(r'citas', CitaViewSet, basename='cita') # El endpoint para el modelo Cita se llamará 'citas'

urlpatterns = [
    path('', include(router.urls)),
]

html_urlpatterns = [
    path('inicio/historial', vista_historial_paciente, name='vista_historial_paciente'),
    path('inicio/principal', IndexView.as_view(), name='principal'),
    path('inicio/calificar', CalificarView.as_view(), name='calificar'),
    path('inicio/habilitar', HabilitarHoraView.as_view(), name='habilitar'),
    path('inicio/detalle', DetalleCitaView.as_view(), name='detalle'),
    path('inicio/agendar-cita', AgendarCitaView.as_view(), name='agendar'),
    path('inicio/listado', ListarGestionarCitasView.as_view(), name='gestionar_citas'),
    path('medicos/<int:medico_id>/disponibilidad/', MedicoDisponibilidadView.as_view(), name='medico_disponibilidad'),
]

urlpatterns = urlpatterns + html_urlpatterns