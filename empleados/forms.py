from django import forms
from .models import Preliquidacion, Liquidacion

class PreliquidacionForm(forms.ModelForm):
    class Meta:
        model = Preliquidacion
        fields = [
            'empleado', 'categoria', 'oficina', 'titulo', 'nivel', 'año', 'mes',
            'basico', 'situacion', 'categoria_nombre', 'oficina_nombre',
            'titulo_completo', 'calificacion', 'antiguedad', 'supl1', 'supl2',
            'supl3', 'supl4', 'supl6', 'supl8', 'supl12', 'bruto',
            'jubilacion', 'obra_social', 'liquido'
        ]

class LiquidacionForm(forms.ModelForm):
    class Meta:
        model = Liquidacion
        fields = [
            'empleado', 'categoria', 'oficina', 'titulo', 'nivel', 'año', 'mes',
            'basico', 'situacion', 'categoria_nombre', 'oficina_nombre',
            'titulo_completo', 'calificacion', 'antiguedad', 'supl1', 'supl2',
            'supl3', 'supl4', 'supl6', 'supl8', 'supl12', 'bruto',
            'jubilacion', 'obra_social', 'liquido'
        ]

from django import forms
from .models import Titulo

class TituloForm(forms.ModelForm):
    class Meta:
        model = Titulo
        fields = ['titulo_completo', 'tipo']
        labels = {
            'titulo_completo': 'Nombre del título',
            'tipo': 'Tipo de título',
        }

from django import forms
from .models import Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = [
            'nombre', 'nivel', 
            'sup1', 'tipo_sup1',
            'sup2', 'tipo_sup2',
            'sup3', 'tipo_sup3',
            'sup4', 'tipo_sup4',
            'sup6', 'tipo_sup6',
            'sup8', 'tipo_sup8',
            'sup12', 'tipo_sup12',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'sup1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup1': forms.NumberInput(attrs={'class': 'form-control'}),
            'sup2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup2': forms.NumberInput(attrs={'class': 'form-control'}),
            'sup3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup3': forms.NumberInput(attrs={'class': 'form-control'}),
            'sup4': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup4': forms.NumberInput(attrs={'class': 'form-control'}),
            'sup6': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup6': forms.NumberInput(attrs={'class': 'form-control'}),
            'sup8': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup8': forms.NumberInput(attrs={'class': 'form-control'}),
            'sup12': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_sup12': forms.NumberInput(attrs={'class': 'form-control'}),
        }
