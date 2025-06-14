from django.urls import path
from . import views

urlpatterns = [
    path('liquidaciones/',               views.LiquidacionList.as_view(), name='liq_list'),
    path('liquidaciones/nueva/',         views.crear_preliq_y_liq,         name='crear_preliq_liq'),
    path('liquidaciones/<int:pk>/edit/', views.liq_edit,                  name='liq_edit'),
]