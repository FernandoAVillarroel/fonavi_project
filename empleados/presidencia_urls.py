# empleados/presidencia_urls.py
from django.urls import path
from .views import (
    presidencia_dashboard,
    generar_preliquidacion,
    preliquidacion_overview,
    actualizar_antiguedad,
    exportar_liquidaciones_pdf,
)

urlpatterns = [
    # Dashboard
    path("", presidencia_dashboard, name="presidencia_dashboard"),

    # Preliquidaciones
    path("preliquidaciones/generar/", generar_preliquidacion, name="generar_preliquidacion"),
    path("preliquidaciones/", preliquidacion_overview, name="preliquidacion_overview"),

    # Utilidades
    path("antiguedad/", actualizar_antiguedad, name="antiguedad-actualizar"),
    path("exportar-pdf/", exportar_liquidaciones_pdf, name="liquidacion-exportar-pdf"),
]
