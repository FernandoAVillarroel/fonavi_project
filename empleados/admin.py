from django.contrib import admin

# Branding global
admin.site.site_header  = "Panel IPVU / FONAVI"
admin.site.site_title   = "Administración IPVU"
admin.site.index_title  = "Resumen de Liquidaciones"
from .models import (
    Categoria, Oficina, NivelBasico, Titulo, TipoTitulo,
    Empleado, Preliquidacion, Liquidacion, Calificacion
)

# --------------------------------------------------
#  Maestros: Categoria, Oficina y Titulo con código
# --------------------------------------------------

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('id_categoria', 'nombre')

    def codigo(self, obj):
        return f"CAT-{obj.id_categoria}"
    codigo.short_description = 'Código'

    def get_search_results(self, request, queryset, search_term):
        """
        Si el término empieza con 'CAT-', quitamos ese prefijo y
        buscamos por id_categoria como número; si no, usamos el
        comportamiento por defecto (busca en id_categoria y nombre).
        """
        qs = queryset
        if search_term.upper().startswith('CAT-'):
            # Extraemos la parte numérica
            num = search_term.upper().replace('CAT-', '')
            if num.isdigit():
                qs = qs.filter(id_categoria=int(num))
                # `use_distinct=False` porque no necesitamos DISTINCT aquí
                return qs, False
        # Comportamiento estándar: LIKE '%term%' en id_categoria o nombre
        return super().get_search_results(request, qs, search_term)

@admin.register(Oficina)
class OficinaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    def codigo(self, obj):
        return f"OF-{obj.id_oficina}"
    codigo.short_description = 'Código'


@admin.register(Titulo)
class TituloAdmin(admin.ModelAdmin):
    # Asumo ahora que el campo descriptivo en Titulo es 'titulo_completo'
    list_display = ('codigo', 'titulo_completo')  
    def codigo(self, obj):
        return f"TIT-{obj.id_titulo}"
    codigo.short_description = 'Código'


@admin.register(TipoTitulo)
class TipoTituloAdmin(admin.ModelAdmin):
    list_display = ('id_tipo', 'porcentaje', 'descripcion')


# --------------------
#  Otros catálogos
# --------------------

@admin.register(NivelBasico)
class NivelBasicoAdmin(admin.ModelAdmin):
    list_display = ('id_nivel', 'nivel', 'descripcion')
    list_display_links = ('id_nivel', 'nivel')


# --------------------
#  Operacionales
# --------------------

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'año',
        'mes',
        'empleado',
        'empleado_dni',      # <-- nueva columna
        'empleado_cuil',     # <-- nueva columna
        'calificacion',
    )
    list_filter   = ('año', 'mes')
    search_fields = (
        'empleado__nombre',
        'empleado__apellido',
        'empleado__dni',
        'empleado__cuil',
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
    
    # Agrega aquí los campos para el buscador
    search_fields = (
        'id_empleado',   # busca por ID interno
        'nombre',        # busca dentro del nombre
        'apellido',      # busca dentro del apellido
        'dni',           # busca por número de DNI
    )


from datetime import date
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect

from empleados.models import Empleado, Preliquidacion

# empleados/admin.py

from datetime import date
from decimal import Decimal
from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect

from empleados.models import Empleado, Preliquidacion


from .models import Empleado, Preliquidacion, Liquidacion


from decimal import Decimal
from datetime import date

from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect

from .models import Empleado, Preliquidacion


from decimal import Decimal
from datetime import date

from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect

from .models import Empleado, Preliquidacion


@admin.register(Preliquidacion)
class PreliquidacionAdmin(admin.ModelAdmin):
    list_display = (
        'empleado',
        'categoria_codigo',
        'categoria_nombre',
        'año',
        'mostrar_mes',
        'calificacion',
        'situacion',
        'bruto',
        'jubilacion',
        'obra_social',
        'oficio_descuento',   # <-- ahora sale también en la lista
        'liquido',
    )
    list_filter   = ('categoria', 'situacion', 'año', 'mes')
    search_fields = ('empleado__nombre', 'empleado__apellido', 'empleado__dni')

    change_list_template = "admin/empleados/preliquidacion/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'generar-preliquidacion/',
                self.admin_site.admin_view(self.generar_preliquidacion),
                name="preliquidacion-generar"
            ),
        ]
        return custom + urls

    def generar_preliquidacion(self, request):
        hoy       = date.today()
        año       = hoy.year
        mes       = hoy.month
        empleados = Empleado.objects.all()
        total     = empleados.count()

        for emp in empleados:
            defaults = {
                'categoria'       : emp.categoria,
                'oficina'         : emp.oficina,
                'titulo'          : emp.titulo,
                'nivel'           : emp.categoria.nivel,
                'basico'          : emp.categoria.nivel.nivel or Decimal('0'),
                'calificacion'    : Decimal('100'),
                'situacion'       : emp.situacion,
                'categoria_nombre': emp.categoria.nombre if emp.categoria else '',
                'oficina_nombre'  : emp.oficina.nombre   if emp.oficina   else '',
                'titulo_completo' : emp.titulo.titulo_completo if emp.titulo else '',
            }
            pl, created = Preliquidacion.objects.update_or_create(
                empleado=emp, año=año, mes=mes,
                defaults=defaults
            )
            # Aquí forzamos el save() para que se vuelva a ejecutar
            # tu lógica en save() y aplique el descuento en liquido
            pl.save()

        self.message_user(
            request,
            f"✅ Se (re)generaron {total} preliquidaciones para {mes}/{año}.",
            level=messages.SUCCESS
        )
        return redirect(reverse('admin:empleados_preliquidacion_changelist'))

    def mostrar_mes(self, obj):
        return obj.mes
    mostrar_mes.short_description = 'Mes'

    @admin.display(description='Categoría')
    def categoria_codigo(self, obj):
        return f"CAT-{obj.categoria.id_categoria:02d}"



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
        'oficio_descuento',   # <-- nuevo
        'liquido'
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



from django.contrib import admin
from django.contrib.auth.models import User, Group

# Desregistra los modelos de auth para que no aparezcan en el Admin
admin.site.unregister(User)
admin.site.unregister(Group)


from django.contrib import admin
from .models import OficioJudicial

# empleados/admin.py

@admin.register(OficioJudicial)
class OficioJudicialAdmin(admin.ModelAdmin):
    list_display = ('empleado','anio','mes','monto_descontar')
    # …

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # forzamos recálculo tras crear/editar:
        filtros = {'año': obj.anio, 'mes': obj.mes, 'empleado': obj.empleado}
        for pl in Preliquidacion.objects.filter(**filtros):
            pl.save()
        for liq in Liquidacion.objects.filter(**filtros):
            liq.save()
