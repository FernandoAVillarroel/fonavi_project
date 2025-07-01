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
