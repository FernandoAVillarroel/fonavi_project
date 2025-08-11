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
from .models import Calificacion, Empleado
from datetime import date

class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['empleado', 'calificacion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = date.today()
        if not self.instance.pk:
            # SOLO para crear: mostrar solo empleados activos, sin calificación este mes, ingresados este mes
            ya_calificados = Calificacion.objects.filter(
                mes=hoy.month,
                año=hoy.year
            ).values_list('empleado_id', flat=True)
            nuevos = Empleado.objects.filter(
                estado=1,
                fecha_salida__isnull=True,
                fecha_ingreso__month=hoy.month,
                fecha_ingreso__year=hoy.year
            ).exclude(id_empleado__in=ya_calificados)
            self.fields['empleado'].queryset = nuevos
            self.fields['empleado'].label_from_instance = (
                lambda obj: f"{obj.apellido}, {obj.nombre} | DNI: {obj.dni} | CUIL: {obj.cuil}"
            )
        else:
            # EN EDICIÓN: eliminar el campo empleado
            self.fields.pop('empleado')


# forms.py
class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'dni', 'cuil', 'numero_cuenta',
            'situacion', 'estado', 'fecha_ingreso',
            'area',      # <-- Área, debe estar aquí
            'categoria', # <-- Categoría, debe estar aquí
            'oficina',
            'nivel_basico',
            'titulo'
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].label = "Categoría"
        self.fields['area'].label = "Área"
        self.fields['nivel_basico'].label = "Nivel Básico (Sueldo Base)"
        # Si querés: mostrar sólo categorías del área seleccionada, se hace con JS o lógica avanzada.



from decimal import Decimal
from django import forms
from .models import Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = [
            'nombre', 'area',
            'sup1', 'tipo_sup1',
            'sup2', 'tipo_sup2',
            'sup3', 'tipo_sup3',
            'sup4', 'tipo_sup4',
            'sup6', 'tipo_sup6',
            'sup8', 'tipo_sup8',
            'sup12', 'tipo_sup12',
        ]
        labels = {
            'nombre': 'Nombre de la Categoría',
            'area': 'Área',
        }
        widgets = {
            'sup1':  forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'sup2':  forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'sup3':  forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'sup4':  forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'sup6':  forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'sup8':  forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'sup12': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
        }
        # No hace falta definir widgets para tipo_sup*: el modelo ya tiene choices.

    def clean(self):
        cleaned = super().clean()
        # Aceptar coma como separador decimal en sup*
        for f in ['sup1', 'sup2', 'sup3', 'sup4', 'sup6', 'sup8', 'sup12']:
            v = cleaned.get(f)
            if isinstance(v, str):
                v = v.strip()
                if v:
                    try:
                        cleaned[f] = Decimal(v.replace(',', '.'))
                    except Exception:
                        self.add_error(f, 'Ingrese un número válido (use punto o coma para decimales).')
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        # tipo_sup*: 1 por defecto, excepto 6 y 12 que van en 2
        defaults_tipo = {1: 1, 2: 1, 3: 1, 4: 1, 6: 2, 8: 1, 12: 2}
        for i in [1, 2, 3, 4, 6, 8, 12]:
            if getattr(obj, f"tipo_sup{i}") is None:
                setattr(obj, f"tipo_sup{i}", defaults_tipo[i])

        # sup*: 0 por defecto para evitar NULL en columnas NOT NULL
        for f in ['sup1', 'sup2', 'sup3', 'sup4', 'sup6', 'sup8', 'sup12']:
            if getattr(obj, f) is None:
                setattr(obj, f, 0)

        if commit:
            obj.save()
        return obj


# empleados/forms.py
from decimal import Decimal, InvalidOperation
from django import forms
from django.utils import timezone
from .models import OficioJudicial


# Fallback por si el modelo no define choices en el campo "tipo"
TIPO_CHOICES = (
    (1, 'Monto fijo'),
    (2, 'Porcentaje'),
)


class OficioJudicialForm(forms.ModelForm):
    # Si tu modelo ya define choices en "tipo", podés omitir esta línea y
    # dejar que el ModelForm los tome del modelo.
    tipo = forms.ChoiceField(choices=TIPO_CHOICES)

    class Meta:
        model = OficioJudicial
        fields = ['empleado', 'anio', 'mes', 'tipo', 'monto_descontar', 'porcentaje_descontar']
        widgets = {
            'anio': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
            'mes':  forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'monto_descontar': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'porcentaje_descontar': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
        }
        labels = {
            'empleado': 'Empleado',
            'anio': 'Año',
            'mes': 'Mes',
            'tipo': 'Tipo de descuento',
            'monto_descontar': 'Monto a descontar ($)',
            'porcentaje_descontar': 'Porcentaje a descontar (%)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.now()
        if not self.instance.pk:
            self.fields['anio'].initial = hoy.year
            self.fields['mes'].initial = hoy.month

    def clean(self):
        data = super().clean()

        # Normalizar coma -> punto para los numéricos si vinieron como string
        for f in ('monto_descontar', 'porcentaje_descontar'):
            raw = self.data.get(f)
            if isinstance(raw, str) and raw.strip():
                txt = raw.replace(',', '.')
                try:
                    data[f] = Decimal(txt)
                except (InvalidOperation, TypeError):
                    self.add_error(f, 'Número inválido (use punto o coma).')

        anio = data.get('anio')
        mes  = data.get('mes')
        if anio and (anio < 2000 or anio > 2100):
            self.add_error('anio', 'Año fuera de rango (2000–2100).')
        if mes and (mes < 1 or mes > 12):
            self.add_error('mes', 'Mes debe ser entre 1 y 12.')

        # Validación según tipo (entero: 1=Monto, 2=Porcentaje)
        tipo = data.get('tipo')
        try:
            tipo = int(tipo) if tipo is not None else None
        except (TypeError, ValueError):
            tipo = None

        monto = data.get('monto_descontar') or Decimal('0')
        porc  = data.get('porcentaje_descontar') or Decimal('0')

        if tipo == 1:  # MONTO
            if monto <= 0:
                self.add_error('monto_descontar', 'Ingrese un monto > 0.')
            # Apagar el porcentaje
            data['porcentaje_descontar'] = Decimal('0.00')

        elif tipo == 2:  # PORCENTAJE
            if porc <= 0:
                self.add_error('porcentaje_descontar', 'Ingrese un % > 0.')
            # Apagar el monto
            data['monto_descontar'] = Decimal('0.00')

        else:
            self.add_error('tipo', 'Seleccione el tipo de descuento (Monto o Porcentaje).')

        return data
