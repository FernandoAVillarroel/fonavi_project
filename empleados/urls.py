# empleados/urls.py
from django.urls import path

from .views import (
    EmpleadoListView, EmpleadoCreateView, EmpleadoUpdateView, EmpleadoDeleteView,
    empleado_toggle_estado,
    CalificacionListView, CalificacionCreateView, CalificacionUpdateView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView,
    OficioJudicialListView, OficioJudicialCreateView, OficioJudicialUpdateView, OficioJudicialDeleteView,
    OficioJudicialEmpleadoListView,
    LiquidacionListView, crear_preliq_y_liq, liq_edit,
    antiguedad_actualizar,
    preliquidacion_overview,
    generar_preliquidacion,  
    
)


from .views_liquidacion import confirmar_liquidacion  # 👈 ESTA sí está en views_liquidacion.py

from .views_periodo import seleccionar_periodo
from .views_novedades import novedades_mensuales_list
from .views_planillas import (
    ver_liquidaciones_confirmadas, 
    exportar_liquidaciones_pdf,
    contribuciones_patronales,
    exportar_contribuciones_pdf,
    generar_txt_banco,
)

app_name = "empleados"

urlpatterns = [
    
    # ───────── Empleados ─────────
    path("", EmpleadoListView.as_view(), name="empleado-list"),
    path("nuevo/", EmpleadoCreateView.as_view(), name="empleado-create"),
    path("<int:pk>/editar/", EmpleadoUpdateView.as_view(), name="empleado-update"),
    path("<int:pk>/borrar/", EmpleadoDeleteView.as_view(), name="empleado-delete"),
    path("estado/<int:pk>/toggle/", empleado_toggle_estado, name="empleado-toggle-estado"),

    # Antigüedad
    path("antiguedad/actualizar/", antiguedad_actualizar, name="antiguedad-actualizar"),

    # Período (sesión)
    path("seleccionar-periodo/", seleccionar_periodo, name="seleccionar_periodo"),

    # ───────── Calificaciones ─────────
    path("calificaciones/", CalificacionListView.as_view(), name="calificacion-list"),
    path("calificaciones/nueva/", CalificacionCreateView.as_view(), name="calificacion-create"),
    path("calificaciones/<int:pk>/editar/", CalificacionUpdateView.as_view(), name="calificacion-update"),

    # ───────── Categorías ─────────
    path("categorias/", CategoriaListView.as_view(), name="categoria-list"),
    path("categorias/nueva/", CategoriaCreateView.as_view(), name="categoria-create"),
    path("categorias/<int:pk>/editar/", CategoriaUpdateView.as_view(), name="categoria-update"),

    # ───────── Oficios ─────────
    path("oficios/", OficioJudicialListView.as_view(), name="oficiojudicial-list"),
    path("oficios/nuevo/", OficioJudicialCreateView.as_view(), name="oficiojudicial-create"),
    path("oficios/<int:pk>/editar/", OficioJudicialUpdateView.as_view(), name="oficiojudicial-update"),
    path("oficios/<int:pk>/eliminar/", OficioJudicialDeleteView.as_view(), name="oficiojudicial-delete"),
    path("oficios/empleado/<int:empleado_id>/", OficioJudicialEmpleadoListView.as_view(), name="oficiojudicial-empleado"),

    # ───────── Liquidaciones (CRUD) ─────────
    path("liquidaciones/", LiquidacionListView.as_view(), name="liquidacion-list"),
    path("preliquidacion-overview/", preliquidacion_overview, name="preliquidacion_overview"),
    path("liquidaciones/nueva/", crear_preliq_y_liq, name="liquidacion-create"),
    path("liquidaciones/<int:pk>/editar/", liq_edit, name="liquidacion-update"),

    # ───────── Presidencia (acciones) ─────────
    path("presidencia/generar-preliq/", generar_preliquidacion, name="generar_preliquidacion"),
    path("presidencia/confirmar_liquidacion/", confirmar_liquidacion, name="confirmar_liquidacion"),

    # Planillas confirmadas + PDF
    path("presidencia/planillas/", ver_liquidaciones_confirmadas, name="planillas_confirmadas"),
    path('generar-txt-banco/', generar_txt_banco, name='generar_txt_banco'),
    path("presidencia/exportar-pdf/", exportar_liquidaciones_pdf, name="liquidacion-exportar-pdf"),
    
    # Contribuciones patronales
    path("presidencia/contribuciones/", contribuciones_patronales, name="contribuciones_patronales"),
    path("presidencia/contribuciones-pdf/", exportar_contribuciones_pdf, name="exportar_contribuciones_pdf"),
    
    
    
    
    

    # ───────── Novedades Mensuales ─────────
    path("novedades/", novedades_mensuales_list, name="novedades_mensuales_list"),
]
