from django.urls import path
from . import views

urlpatterns = [
    path('liquidaciones/',               views.LiquidacionList.as_view(), name='liq_list'),
    path('liquidaciones/nueva/',         views.crear_preliq_y_liq,         name='crear_preliq_liq'),
    path('liquidaciones/<int:pk>/edit/', views.liq_edit,                  name='liq_edit'),

     # Títulos
    path('titulos/', views.listar_titulos, name='listar_titulos'),
    path('titulos/nuevo/', views.crear_titulo, name='crear_titulo'),
    path('titulos/editar/<int:pk>/', views.editar_titulo, name='editar_titulo'),
    path('titulos/eliminar/<int:pk>/', views.eliminar_titulo, name='eliminar_titulo'),

    # Categorías    
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/nueva/', views.crear_categoria, name='crear_categoria'),   
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
         

]