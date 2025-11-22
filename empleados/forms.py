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


class HTML5DateInput(forms.DateInput):
    """Widget que asegura el formateo ISO para <input type='date'>."""
    input_type = "date"
    format = "%Y-%m-%d"


# empleados/forms.py
from django import forms
from .models import Empleado, Titulo, TipoTitulo


class HTML5DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class EmpleadoForm(forms.ModelForm):
    # Campo auxiliar (NO es de BD): sirve para filtrar los títulos
    tipo_titulo = forms.ModelChoiceField(
        queryset=TipoTitulo.objects.all().order_by("descripcion"),
        required=False,
        label="Tipo de título",
    )

    class Meta:
        model = Empleado
        # ¡OJO!: NO incluir 'tipo_titulo' acá (no es campo del modelo)
        fields = [
            "nombre", "apellido", "dni", "cuil", "numero_cuenta",
            "situacion", "estado",
            "fecha_ingreso", "fecha_salida",
            "categoria", "oficina",
            "titulo",
        ]
        labels = {
            
            "categoria": "Categoría",
            "oficina": "Oficina",
            "titulo": "Título",
            "fecha_ingreso": "Fecha de ingreso",
            "fecha_salida": "Fecha de salida",
        }
        widgets = {
            "fecha_ingreso": HTML5DateInput(format="%Y-%m-%d"),
            "fecha_salida": HTML5DateInput(format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aceptar formato ISO del input y dd/mm/aaaa si lo escriben a mano
        self.fields["fecha_ingreso"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        self.fields["fecha_salida"].input_formats  = ["%Y-%m-%d", "%d/%m/%Y"]

        # Etiquetas más claras
        self.fields["situacion"].label = "Situación (P=Perm., C=Contr.)"
        self.fields["estado"].label    = "Estado (1=Activo, 0=Inactivo)"
        self.fields["numero_cuenta"].label = "N° de cuenta"

        # --- Filtro de títulos según tipo elegido ---
        tipo = None

        # Si viene en POST el tipo de título, usamos eso para filtrar
        if self.data.get("tipo_titulo"):
            try:
                tipo = TipoTitulo.objects.get(pk=int(self.data["tipo_titulo"]))
            except (ValueError, TypeError, TipoTitulo.DoesNotExist):
                tipo = None

        # Si estamos editando y no viene en POST, usamos el tipo del título actual
        if not tipo and self.instance and getattr(self.instance, "titulo", None):
            tipo = self.instance.titulo.tipo
            self.fields["tipo_titulo"].initial = tipo

        if tipo:
            self.fields["titulo"].queryset = (
                Titulo.objects.filter(tipo=tipo).order_by("titulo_completo")
            )
        else:
            self.fields["titulo"].queryset = Titulo.objects.all().order_by("titulo_completo")

    def clean(self):
        cleaned = super().clean()

        estado        = cleaned.get("estado")
        fecha_ingreso = cleaned.get("fecha_ingreso")
        fecha_salida  = cleaned.get("fecha_salida")

        # Normalizamos estado a 0/1
        try:
            estado_val = int(estado)
        except Exception:
            estado_val = 1 if str(estado).lower() in ("1", "true", "t", "activo") else 0

        # Si INACTIVO: fecha_salida obligatoria y coherente
        if estado_val == 0:
            if not fecha_salida:
                self.add_error("fecha_salida", "Si el empleado está INACTIVO, la fecha de salida es obligatoria.")
            elif fecha_ingreso and fecha_salida < fecha_ingreso:
                self.add_error("fecha_salida", "La fecha de salida no puede ser anterior a la fecha de ingreso.")
        else:
            # Si ACTIVO, limpiamos fecha_salida para evitar inconsistencias
            cleaned["fecha_salida"] = None

        # Recordatorio: el nivel básico depende de la categoría
        if not cleaned.get("categoria"):
            self.add_error("categoria", "Elegí la categoría (de allí saldrá el nivel básico).")

        # Si eligieron tipo_titulo pero no título
        if cleaned.get("tipo_titulo") and not cleaned.get("titulo"):
            self.add_error("titulo", "Elegí el título específico para el tipo seleccionado.")

        return cleaned

from decimal import Decimal, InvalidOperation
from django import forms
from .models import Categoria, NivelBasico

class CategoriaForm(forms.ModelForm):
    
    class Meta:
        model = Categoria
        fields = [
            'nombre', 'nivel',  # ← SIN basico_manual
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
            'nivel':  'Nivel',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campo nivel obligatorio
        self.fields['nivel'].required = True
        self.fields['nivel'].help_text = "Seleccione el nivel de la categoría."

    def clean(self):
        cleaned = super().clean()
        
        # Validar que haya nivel
        nivel = cleaned.get('nivel')
        
        if not nivel:
            raise forms.ValidationError('Debe seleccionar un nivel.')
        
        # Limpiar basico_manual (no se usa desde web)
        cleaned['basico_manual'] = None
                        
        # Aceptar coma como separador decimal en sup*
        for f in ['sup1', 'sup2', 'sup3', 'sup4', 'sup6', 'sup8', 'sup12']:
            v = cleaned.get(f)
            if isinstance(v, str):
                v = v.strip()
                if v:
                    try:
                        cleaned[f] = Decimal(v.replace(',', '.'))
                    except (InvalidOperation, ValueError):
                        self.add_error(f, 'Ingrese un número válido (use punto o coma para decimales).')
                        
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Limpiar basico_manual (solo se edita desde admin)
        obj.basico_manual = None

        # tipo_sup*: 1 por defecto; 6 y 12 suelen ser monto fijo (2)
        defaults_tipo = {1: 1, 2: 1, 3: 1, 4: 1, 6: 2, 8: 1, 12: 2}
        for i in [1, 2, 3, 4, 6, 8, 12]:
            if getattr(obj, f"tipo_sup{i}") is None:
                setattr(obj, f"tipo_sup{i}", defaults_tipo[i])

        # sup*: 0 por defecto para evitar NULL
        for f in ['sup1', 'sup2', 'sup3', 'sup4', 'sup6', 'sup8', 'sup12']:
            if getattr(obj, f) is None:
                setattr(obj, f, Decimal('0'))

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
        fields = [
            'empleado', 'anio', 'mes', 'tipo', 
            'monto_descontar', 'porcentaje_descontar',
            'codigo_mutual', 'numero_cuota', 'novedad'  # ← NUEVOS CAMPOS
        ]
        widgets = {
            'anio': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
            'mes':  forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'monto_descontar': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            'porcentaje_descontar': forms.NumberInput(attrs={'step': '0.01', 'inputmode': 'decimal'}),
            # Widgets para los campos nuevos
            'codigo_mutual': forms.TextInput(attrs={
                'maxlength': 3, 
                'placeholder': '001',
                'class': 'form-control'
            }),
            'numero_cuota': forms.NumberInput(attrs={
                'min': 1, 
                'max': 99,
                'placeholder': '1',
                'class': 'form-control'
            }),
            'novedad': forms.Select(attrs={
                'class': 'form-control'
            }),
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

