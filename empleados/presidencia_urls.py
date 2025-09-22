# empleados/presidencia_urls.py
from django.urls import path
from . import views   # 👈 importá el módulo, no los nombres

urlpatterns = [
    # Dashboard
    path("", views.presidencia_dashboard, name="presidencia_dashboard"),

    # Preliquidaciones
    path("preliquidaciones/generar/", views.generar_preliquidacion, name="generar_preliquidacion"),
    path("preliquidaciones/", views.preliquidacion_overview, name="preliquidacion_overview"),

    # Utilidades
    path("antiguedad/", views.actualizar_antiguedad, name="antiguedad-actualizar"),
    path("exportar-pdf/", views.exportar_liquidaciones_pdf, name="liquidacion-exportar-pdf"),
]
