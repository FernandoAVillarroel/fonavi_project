# empleados/admin.py
from django.contrib import admin
from django.utils.html import format_html

# Branding global
admin.site.site_header  = "Panel IPVU / FONAVI"
admin.site.site_title   = "Administración IPVU"
admin.site.index_title  = "Resumen de Liquidaciones"

from .models import (
    Categoria, Oficina, NivelBasico, Titulo, TipoTitulo,
    Empleado, Preliquidacion, Liquidacion, Calificacion, OficioJudicial, NovedadMensual
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
    search_fields = ('id_empleado', 'nombre', 'apellido', 'dni')

@admin.register(Preliquidacion)
class PreliquidacionAdmin(admin.ModelAdmin):
    list_display = (
        'empleado', 'categoria_codigo', 'categoria_nombre', 'año', 'mostrar_mes',
        'calificacion', 'situacion', 'bruto', 'jubilacion', 'obra_social',
        'oficio_judicial', 'liquido'
    )
    list_filter = ('categoria', 'situacion', 'año', 'mes')
    search_fields = ('empleado__nombre', 'empleado__apellido', 'empleado__dni')
    # Evitar change_list_template si no existe un template custom.

    def mostrar_mes(self, obj):
        return obj.mes
    mostrar_mes.short_description = 'Mes'

    @admin.display(description='Categoría')
    def categoria_codigo(self, obj):
        # Proteger por si falta categoría
        if getattr(obj, "categoria", None) and getattr(obj.categoria, "id_categoria", None) is not None:
            return f"CAT-{obj.categoria.id_categoria:02d}"
        return "-"

    @admin.display(description='Oficio Judicial')
    def oficio_judicial(self, obj):
        return obj.oficio_judicial

@admin.register(Liquidacion)
class LiquidacionAdmin(admin.ModelAdmin):
    """
    Modelo de liquidación final (planilla) existente en tu proyecto,
    con campos como id_liquidacion, año, mes, etc.
    """
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

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    @admin.display(description='Categoría')
    def categoria_codigo(self, obj):
        if getattr(obj, "categoria", None) and getattr(obj.categoria, "id_categoria", None) is not None:
            return f"CAT-{obj.categoria.id_categoria:02d}"
        return "-"

    @admin.display(description='Oficina')
    def oficina_codigo(self, obj):
        if getattr(obj, "oficina", None) and getattr(obj.oficina, "id_oficina", None) is not None:
            return f"OF-{obj.oficina.id_oficina:02d}"
        return "-"

    @admin.display(description='Título')
    def titulo_codigo(self, obj):
        if getattr(obj, "titulo", None) and getattr(obj.titulo, "id_titulo", None) is not None:
            return f"TIT-{obj.titulo.id_titulo:02d}"
        return "-"

@admin.register(OficioJudicial)
class OficioJudicialAdmin(admin.ModelAdmin):
    list_display = ('empleado','anio','mes','monto_descontar','porcentaje_descontar','tipo')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Recalcular preliquidación/liquidación del mismo período y empleado:
        filtros = {'año': obj.anio, 'mes': obj.mes, 'empleado': obj.empleado}
        for pl in Preliquidacion.objects.filter(**filtros):
            pl.save()
        for liq in Liquidacion.objects.filter(**filtros):
            liq.save()

# ——— Opcional: remover modelos de auth del admin si no los usás ———
from django.contrib.auth.models import User, Group
try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# ----------------- OPCIONAL: modelo de estado por período -----------------
# Si tenés el modelo NUEVO de estado (ABIERTA/CERRADA/CONFIRMADA), que se llame LiquidacionPeriodo.
# Se registra solo si existe, para no romper si todavía no lo creaste.
try:
    from .models import LiquidacionPeriodo
except Exception:
    LiquidacionPeriodo = None

if LiquidacionPeriodo:
    @admin.register(LiquidacionPeriodo)
    class LiquidacionPeriodoAdmin(admin.ModelAdmin):
        list_display  = ("periodo", "estado", "fecha_creada", "fecha_cerrada", "fecha_confirmada")
        list_filter   = ("estado",)
        search_fields = ("periodo",)
        ordering      = ("-periodo",)


# ✅ -------------- NOVEDADES MENSUALES ------------------
@admin.register(NovedadMensual)
class NovedadMensualAdmin(admin.ModelAdmin):
    list_display = [
        'fecha_corta', 'periodo', 'tipo_badge', 'empleado_info', 
        'descripcion_corta', 'actor', 'area'
    ]
    list_filter = [
        'periodo', 'tipo', 'area', 'fecha'
    ]
    search_fields = [
        'descripcion', 'empleado__nombre', 'empleado__apellido', 
        'empleado__dni', 'actor__username', 'periodo'
    ]
    readonly_fields = ['fecha', 'periodo']
    date_hierarchy = 'fecha'
    ordering = ['-fecha', '-id']
    list_per_page = 50
    
    def fecha_corta(self, obj):
        return obj.fecha.strftime("%d/%m/%Y %H:%M")
    fecha_corta.short_description = 'Fecha'
    fecha_corta.admin_order_field = 'fecha'
    
    def tipo_badge(self, obj):
        colors = {
            'EMPLEADO_ALTA': '#28a745',
            'EMPLEADO_BAJA': '#dc3545', 
            'CAMBIO_CATEG': '#ffc107',
            'CAMBIO_CALIF': '#17a2b8',
            'OFICIO_CREADO': '#6c757d',
            'PRELIQ_GENERADA': '#007bff',
            'OTRO': '#343a40'
        }
        color = colors.get(obj.tipo, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'
    
    def empleado_info(self, obj):
        if obj.empleado:
            return f"{obj.empleado.apellido}, {obj.empleado.nombre}"
        return "—"
    empleado_info.short_description = 'Empleado'
    
    def descripcion_corta(self, obj):
        if len(obj.descripcion) > 80:
            return obj.descripcion[:80] + "..."
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'