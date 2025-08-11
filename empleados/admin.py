from django.contrib import admin

# Branding global
admin.site.site_header  = "Panel IPVU / FONAVI"
admin.site.site_title   = "Administración IPVU"
admin.site.index_title  = "Resumen de Liquidaciones"

from .models import (
    Categoria, Oficina, NivelBasico, Titulo, TipoTitulo,
    Empleado, Preliquidacion, Liquidacion, Calificacion, OficioJudicial
)

# -------------- Maestros ------------------

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('id_categoria', 'nombre')

    def codigo(self, obj):
        return f"CAT-{obj.id_categoria}"
    codigo.short_description = 'Código'

    def get_search_results(self, request, queryset, search_term):
        qs = queryset
        if search_term.upper().startswith('CAT-'):
            num = search_term.upper().replace('CAT-', '')
            if num.isdigit():
                qs = qs.filter(id_categoria=int(num))
                return qs, False
        return super().get_search_results(request, qs, search_term)

@admin.register(Oficina)
class OficinaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    def codigo(self, obj):
        return f"OF-{obj.id_oficina}"
    codigo.short_description = 'Código'

@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo_completo')
    def codigo(self, obj):
        return f"TIT-{obj.id_titulo}"
    codigo.short_description = 'Código'

@admin.register(TipoTitulo)
class TipoTituloAdmin(admin.ModelAdmin):
    list_display = ('id_tipo', 'porcentaje', 'descripcion')

@admin.register(NivelBasico)
class NivelBasicoAdmin(admin.ModelAdmin):
    list_display = ('id_nivel', 'nivel', 'descripcion')
    list_display_links = ('id_nivel', 'nivel')

# -------------- Operacionales --------------

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'año', 'mes', 'empleado',
        'empleado_dni', 'empleado_cuil', 'calificacion',
    )
    list_filter   = ('año', 'mes')
    search_fields = (
        'empleado__nombre', 'empleado__apellido', 'empleado__dni', 'empleado__cuil',
    )
    def empleado_dni(self, obj):
        return obj.empleado.dni
    empleado_dni.short_description = 'DNI'
    empleado_dni.admin_order_field = 'empleado__dni'
    def empleado_cuil(self, obj):
        return obj.empleado.cuil
    empleado_cuil.short_description = 'CUIL'
    empleado_cuil.admin_order_field = 'empleado__cuil'
    def save_model(self, request, obj, form, change):
        obj.id_usuario = request.user
        super().save_model(request, obj, form, change)
    def has_add_permission(self, request):
        return False

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id_empleado', 'nombre', 'apellido', 'dni', 'categoria', 'oficina', 'titulo')
    search_fields = (
        'id_empleado', 'nombre', 'apellido', 'dni'
    )

@admin.register(Preliquidacion)
class PreliquidacionAdmin(admin.ModelAdmin):
    list_display = (
        'empleado', 'categoria_codigo', 'categoria_nombre', 'año', 'mostrar_mes', 'calificacion', 'situacion',
        'bruto', 'jubilacion', 'obra_social', 'oficio_judicial', 'liquido'
    )
    list_filter = ('categoria', 'situacion', 'año', 'mes')
    search_fields = ('empleado__nombre', 'empleado__apellido', 'empleado__dni')
    # **Elimina esta línea** porque da error si no existe el archivo:
    # change_list_template = "admin/empleados/preliquidacion/change_list.html"

    def mostrar_mes(self, obj):
        return obj.mes
    mostrar_mes.short_description = 'Mes'

    @admin.display(description='Categoría')
    def categoria_codigo(self, obj):
        return f"CAT-{obj.categoria.id_categoria:02d}"

    @admin.display(description='Oficio Judicial')
    def oficio_judicial(self, obj):
        # Si quieres mostrar el oficio judicial relacionado
        return obj.oficio_judicial

@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    list_display = [
        'id_liquidacion', 'año', 'mes', 'empleado',
        'categoria_codigo', 'oficina_codigo', 'titulo_codigo',
        'nivel', 'basico', 'situacion',
        'categoria_nombre', 'oficina_nombre', 'titulo_completo',
        'calificacion', 'antiguedad',
        'supl1', 'supl2', 'supl3', 'supl4', 'supl6', 'supl8', 'supl12',
        'bruto', 'jubilacion', 'obra_social',
        'oficio_judicial', 'liquido'
    ]
    list_filter   = ['año', 'mes', 'categoria_nombre', 'situacion', 'oficina_nombre']
    search_fields = ['empleado__nombre', 'empleado__dni']
    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    @admin.display(description='Categoría')
    def categoria_codigo(self, obj):
        return f"CAT-{obj.categoria.id_categoria:02d}"

    @admin.display(description='Oficina')
    def oficina_codigo(self, obj):
        return f"OF-{obj.oficina.id_oficina:02d}"

    @admin.display(description='Título')
    def titulo_codigo(self, obj):
        return f"TIT-{obj.titulo.id_titulo:02d}"

@admin.register(OficioJudicial)
class OficioJudicialAdmin(admin.ModelAdmin):
    list_display = ('empleado','anio','mes','monto_descontar','porcentaje_descontar','tipo')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # forzamos recálculo tras crear/editar:
        filtros = {'año': obj.anio, 'mes': obj.mes, 'empleado': obj.empleado}
        for pl in Preliquidacion.objects.filter(**filtros):
            pl.save()
        for liq in Liquidacion.objects.filter(**filtros):
            liq.save()

# ——— Quita los modelos de auth si no los usas en el Admin ———
from django.contrib.auth.models import User, Group
admin.site.unregister(User)
admin.site.unregister(Group)
