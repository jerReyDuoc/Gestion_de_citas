from django.contrib import admin

# Register your models here.

from .models import Paciente, Medico, Cita, HistorialCita, Disponibilidad

admin.site.register(Paciente)
admin.site.register(Medico)
admin.site.register(Cita)
admin.site.register(HistorialCita)
admin.site.register(Disponibilidad)