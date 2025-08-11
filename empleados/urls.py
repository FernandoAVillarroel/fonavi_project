# empleados/urls.py
from django.urls import path
from . import views
from .views import (
    # Empleados
    EmpleadoListView, EmpleadoCreateView, EmpleadoUpdateView, EmpleadoDeleteView,
    empleado_toggle_estado,  # <-- NUEVO: toggle estado (AJAX)

    # Calificaciones
    CalificacionListView, CalificacionCreateView, CalificacionUpdateView,

    # Categorías
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView,

    # Oficios Judiciales
    OficioJudicialListView,
    OficioJudicialCreateView,
    OficioJudicialUpdateView,
    OficioJudicialDeleteView,

    # Liquidaciones
    LiquidacionListView, crear_preliq_y_liq, liq_edit,

    # Presidencia
    confirmar_liquidacion,
)

app_name = 'empleados'

urlpatterns = [
    # — Empleados —
    path('', EmpleadoListView.as_view(), name='empleado-list'),
    path('nuevo/', EmpleadoCreateView.as_view(), name='empleado-create'),
    path('<int:pk>/editar/', EmpleadoUpdateView.as_view(), name='empleado-update'),
    path('<int:pk>/borrar/', EmpleadoDeleteView.as_view(), name='empleado-delete'),
    path('estado/<int:pk>/toggle/', empleado_toggle_estado, name='empleado-toggle-estado'),  # <-- NUEVO

    # — Calificaciones —
    path('calificaciones/', CalificacionListView.as_view(), name='calificacion-list'),
    path('calificaciones/nueva/', CalificacionCreateView.as_view(), name='calificacion-create'),
    path('calificaciones/<int:pk>/editar/', CalificacionUpdateView.as_view(), name='calificacion-update'),

    # — Categorías —
    path('categorias/', CategoriaListView.as_view(), name='categoria-list'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='categoria-create'),
    path('categorias/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria-update'),

    # — Oficios Judiciales —
    path('oficios/', OficioJudicialListView.as_view(), name='oficiojudicial-list'),
    path('oficios/nuevo/', OficioJudicialCreateView.as_view(), name='oficiojudicial-create'),
    path('oficios/<int:pk>/editar/', OficioJudicialUpdateView.as_view(), name='oficiojudicial-update'),
    path('oficios/<int:pk>/eliminar/', OficioJudicialDeleteView.as_view(), name='oficiojudicial-delete'),

    # — Liquidaciones (CRUD) —
    path('liquidaciones/', LiquidacionListView.as_view(), name='liquidacion-list'),
    path('liquidaciones/nueva/', crear_preliq_y_liq, name='liquidacion-create'),
    path('liquidaciones/<int:pk>/editar/', liq_edit, name='liquidacion-update'),

    # — Confirmar Liquidación (desde Presidencia) —
    path('presidencia/confirmar_liquidacion/', confirmar_liquidacion, name='confirmar_liquidacion'),
]
