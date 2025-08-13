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


# empleados/forms.py
from django import forms
from .models import Empleado, Titulo, TipoTitulo, Categoria

class EmpleadoForm(forms.ModelForm):
    # Campo auxiliar para filtrar los títulos por tipo (NO se guarda en BD)
    tipo_titulo = forms.ModelChoiceField(
        queryset=TipoTitulo.objects.all().order_by('descripcion'),
        required=False,
        label="Tipo de título"
    )

    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'dni', 'cuil', 'numero_cuenta',
            'situacion', 'estado', 'fecha_ingreso',
            'area', 'categoria', 'oficina',
            # 'nivel_basico',  # <-- lo quitamos (depende de la categoría)
            'titulo',        # se guarda normalmente
        ]
        labels = {
            'area': 'Área',
            'categoria': 'Categoría',
            'oficina': 'Oficina',
            'titulo': 'Título',
        }
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # si edita, “preseleccionamos” el tipo del título existente
        if self.instance and self.instance.pk and self.instance.titulo:
            self.fields['tipo_titulo'].initial = self.instance.titulo.tipo

            # limitar la lista de títulos al tipo elegido del empleado
            self.fields['titulo'].queryset = (
                Titulo.objects.filter(tipo=self.instance.titulo.tipo)
                .order_by('titulo_completo')
            )
        else:
            # por defecto, mostrar todos los títulos (los filtramos en el front)
            self.fields['titulo'].queryset = Titulo.objects.all().order_by('titulo_completo')

        # UX: textos claros
        self.fields['situacion'].label = "Situación (P=Perm., C=Contr.)"
        self.fields['estado'].label = "Estado (1=Activo, 0=Inactivo)"
        self.fields['numero_cuenta'].label = "N° de cuenta"

    def clean(self):
        data = super().clean()

        # Recordatorio: nivel básico NO se elige; saldrá de la categoría en la preliquidación.
        if not data.get('categoria'):
            self.add_error('categoria', 'Elegí la categoría (de allí saldrá el nivel básico).')

        # Si eligieron tipo_titulo pero no título
        if data.get('tipo_titulo') and not data.get('titulo'):
            self.add_error('titulo', 'Elegí el título específico para el tipo seleccionado.')

        return data




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


# forms.py
from decimal import Decimal, InvalidOperation
from django import forms
from django.utils import timezone
from .models import OficioJudicial

CHOICES_TIPO = (
    (1, 'Monto fijo'),
    (2, 'Porcentaje'),
)

class OficioJudicialForm(forms.ModelForm):
    tipo = forms.TypedChoiceField(choices=CHOICES_TIPO, coerce=int)

    class Meta:
        model = OficioJudicial
        fields = ['empleado', 'anio', 'mes', 'tipo', 'monto_descontar', 'porcentaje_descontar']
        widgets = {
            'anio': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
            'mes':  forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'monto_descontar': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'porcentaje_descontar': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.now()
        if not self.instance.pk:
            self.fields['anio'].initial = hoy.year
            self.fields['mes'].initial = hoy.month

    def clean(self):
        data = super().clean()

        # coma -> punto si vino como string
        for f in ('monto_descontar', 'porcentaje_descontar'):
            raw = self.data.get(f)
            if isinstance(raw, str) and raw.strip():
                try:
                    data[f] = Decimal(raw.replace(',', '.'))
                except (InvalidOperation, TypeError):
                    self.add_error(f, 'Número inválido (use punto o coma).')

        tipo = data.get('tipo')
        monto = data.get('monto_descontar') or Decimal('0')
        porc  = data.get('porcentaje_descontar') or Decimal('0')

        if tipo == 1:  # MONTO
            if monto <= 0:
                self.add_error('monto_descontar', 'Ingrese un monto > 0.')
            data['porcentaje_descontar'] = Decimal('0')
        elif tipo == 2:  # PORCENTAJE
            if porc <= 0:
                self.add_error('porcentaje_descontar', 'Ingrese un % > 0.')
            data['monto_descontar'] = Decimal('0')
        else:
            self.add_error('tipo', 'Seleccione Monto o Porcentaje.')

        return data

