from django.contrib import admin
from .models import Calificacion  # ← ahora sí va a funcionar
from .models import Categoria, Oficina, NivelBasico, Titulo, Empleado, Preliquidacion, Liquidacion, Calificacion

admin.site.register([Categoria, Oficina, NivelBasico, Titulo, Calificacion])



@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id_empleado', 'nombre', 'apellido', 'dni', 'categoria', 'oficina', 'titulo')

@admin.register(Preliquidacion)
class PreliquidacionAdmin(admin.ModelAdmin):
    list_display  = ('empleado','categoria','año','mes','calificacion','fecha')
    list_filter   = ('categoria','año','mes')
    search_fields = ('empleado__nombre',)

@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    list_display = ('preliquidacion','fecha_liquidacion','total')
    list_filter  = ('fecha_liquidacion',)