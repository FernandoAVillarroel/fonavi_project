from django import forms
from .models import Preliquidacion, Liquidacion

class PreliquidacionForm(forms.ModelForm):
    class Meta:
        model  = Preliquidacion
        fields = ['empleado','categoria','año','mes','calificacion','fecha','salario_base','total_por_titulos']
        widgets = {'fecha': forms.DateInput(attrs={'type':'date'})}

class LiquidacionForm(forms.ModelForm):
    class Meta:
        model  = Liquidacion
        fields = ['total']