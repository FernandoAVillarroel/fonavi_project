from django.db import models
from django.conf import settings
from django.db import models, transaction

from decimal import Decimal
from django.db import models
from django.apps import apps
from django.db import models

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)

    AREAS = [
        ('PRESIDENCIA', 'Presidencia'),
        ('SECRET. TÉCNICA CONTABLE', 'Secret. Técnica Contable'),
        ('PLANES DE EMERGENCIA', 'Planes de Emergencia'),
        ('SECRETARÍA TEC. SOCIAL', 'Secretaría Tec. Social'),
    ]
    area = models.CharField(max_length=60, choices=AREAS, default='PRESIDENCIA')

    nivel = models.ForeignKey(
        'NivelBasico',
        on_delete=models.PROTECT,
        db_column='id_nivel',
        null=True, blank=True,
    )

    # Valores monetarios: default=0
    sup1  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sup2  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sup3  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sup4  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sup6  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sup8  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    sup12 = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # Tipos de suplemento: Porcentaje (1) o Monto fijo (2)
    TIPO_SUP_CHOICES = [(1, 'Porcentaje (%)'), (2, 'Monto fijo ($)')]

    tipo_sup1  = models.PositiveSmallIntegerField(db_column='tipo_sup1',  default=1, choices=TIPO_SUP_CHOICES)
    tipo_sup2  = models.PositiveSmallIntegerField(db_column='tipo_sup2',  default=1, choices=TIPO_SUP_CHOICES)
    tipo_sup3  = models.PositiveSmallIntegerField(db_column='tipo_sup3',  default=1, choices=TIPO_SUP_CHOICES)
    tipo_sup4  = models.PositiveSmallIntegerField(db_column='tipo_sup4',  default=1, choices=TIPO_SUP_CHOICES)
    tipo_sup6  = models.PositiveSmallIntegerField(db_column='tipo_sup6',  default=2, choices=TIPO_SUP_CHOICES)  # monto fijo
    tipo_sup8  = models.PositiveSmallIntegerField(db_column='tipo_sup8',  default=1, choices=TIPO_SUP_CHOICES)
    tipo_sup12 = models.PositiveSmallIntegerField(db_column='tipo_sup12', default=2, choices=TIPO_SUP_CHOICES)  # monto fijo

    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nombre




class Oficina(models.Model):
    id_oficina = models.AutoField(primary_key=True)  # Si tu tabla tiene PK manual
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'oficinas'  



class NivelBasico(models.Model):
    id_nivel = models.AutoField(primary_key=True)

    nivel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column="monto",          
        verbose_name="Monto",        
        unique=True,
    )
    descripcion = models.CharField(
        "Descripción",
        max_length=100,
        blank=True,
    )

    def __str__(self):
        # Muestra solo el ID para claridad en las FKs
        return str(self.id_nivel)

    class Meta:
        db_table = "nivel_basico"
        verbose_name = "Nivel básico"
        verbose_name_plural = "Niveles básicos"


class Titulo(models.Model):
    id_titulo = models.AutoField(primary_key=True)
    titulo_completo = models.CharField(max_length=100, db_column='titulo_completo')
    tipo = models.ForeignKey('TipoTitulo', on_delete=models.PROTECT, db_column='id_tipo')

    def __str__(self):
        return self.titulo_completo

    class Meta:
        db_table = 'titulos'
        managed = False


class TipoTitulo(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    porcentaje = models.IntegerField()
    descripcion = models.CharField(max_length=100)

    def __str__(self):
        return self.descripcion

    class Meta:
        db_table = 'tipo_titulos'
        managed = False
        



AREAS = [
    ('PRESIDENCIA', 'Presidencia'),
    ('SECRET. TÉCNICA CONTABLE', 'Secret. Técnica Contable'),
    ('PLANES DE EMERGENCIA', 'Planes de Emergencia'),
    ('SECRETARÍA TEC. SOCIAL', 'Secretaría Tec. Social'),
]

from datetime import date
from django.db import models

# Asegurate de que estas clases estén definidas encima o importadas:
# from .models import Categoria, Oficina, Titulo, NivelBasico

# Helper histórico (lo podés dejar si lo usan otros lados, pero NO se usa para mostrar)
def antiguedad_al_31_diciembre(fecha_ingreso, hoy=None) -> int:
    """Antigüedad medida al 31 de diciembre del año anterior (compatible con IPVU)."""
    if not fecha_ingreso:
        return 0
    hoy = hoy or date.today()
    corte = date(hoy.year - 1, 12, 31)
    años = corte.year - fecha_ingreso.year - (
        (corte.month, corte.day) < (fecha_ingreso.month, fecha_ingreso.day)
    )
    return max(años, 0)

# Helper IPVU por PERÍODO (enero/julio). Ya lo tenés en utils.
try:
    from .utils import calcular_antiguedad_ipvu
except Exception:
    calcular_antiguedad_ipvu = None


# empleados/models.py
from datetime import date
from django.db import models

# Antigüedad IPVU (enero/julio) — si no existe el helper, dejamos un fallback
try:
    from .utils import calcular_antiguedad_ipvu
except Exception:
    calcular_antiguedad_ipvu = None


class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)

    dni = models.CharField(max_length=15, blank=True, default="")
    cuil = models.CharField(max_length=20, blank=True, default="")
    numero_cuenta = models.CharField(max_length=20, blank=True, default="")

    SITUACIONES = (("P", "PERMANENTE"), ("C", "CONTRATADO"))
    situacion = models.CharField(max_length=1, choices=SITUACIONES, default="P")

    # Usan estado=1 en las queries → numérico
    estado = models.PositiveSmallIntegerField(
        default=1, help_text="1=Activo / 0=Inactivo", db_index=True
    )

    # Permitimos null/blank para poder cargarla luego si hoy está vacía
    fecha_ingreso = models.DateField(null=True, blank=True)

    # Se mantiene para reportes/export; NO se recalcula automáticamente en save()
    antiguedad = models.PositiveSmallIntegerField(default=0, null=True, blank=True)

    # Debe existir Categoria.AREAS en tu modelo Categoria
    area = models.CharField(max_length=40, choices=Categoria.AREAS, default="PRESIDENCIA")

    fecha_salida = models.DateField(null=True, blank=True)

    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True,
        db_column="id_categoria", related_name="empleados"
    )
    oficina = models.ForeignKey(
        Oficina, on_delete=models.SET_NULL, null=True,
        db_column="id_oficina", related_name="empleados"
    )
    titulo = models.ForeignKey(
        Titulo, on_delete=models.SET_NULL, null=True,
        db_column="id_titulo", related_name="empleados"
    )
    nivel_basico = models.ForeignKey(
        NivelBasico, on_delete=models.SET_NULL, null=True,
        db_column="id_nivel", related_name="empleados"
    )

    class Meta:
        db_table = "empleados"
        ordering = ("apellido", "nombre")
        indexes = [
            models.Index(fields=["estado", "fecha_salida"]),
            models.Index(fields=["cuil"]),
            models.Index(fields=["dni"]),
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"

    # Antigüedad IPVU “en vivo” para mostrar en listados (no persiste en DB)
    @property
    def antiguedad_ipvu_actual(self) -> int:
        """
        Antigüedad según IPVU para el PERÍODO ACTUAL (hoy).
        Útil para mostrar; para persistir usá tu vista 'antiguedad_actualizar'.
        """
        if not self.fecha_ingreso:
            return 0
        hoy = date.today()
        if calcular_antiguedad_ipvu:
            return calcular_antiguedad_ipvu(self.fecha_ingreso, hoy.year, hoy.month)
        # Fallback simple si faltara el helper
        base = hoy.year - self.fecha_ingreso.year
        if hoy.month >= 7:
            base += 1
        return max(base, 0)



from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db import models
from django.apps import apps

class Preliquidacion(models.Model):
    id_preliquidacion = models.AutoField(primary_key=True)
    año = models.PositiveSmallIntegerField(verbose_name='Año')
    mes = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        verbose_name='Mes'
    )
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.CASCADE,
        db_column='id_empleado'
    )
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.PROTECT,
        db_column='id_categoria'
    )
    oficina = models.ForeignKey(
        'Oficina',
        on_delete=models.PROTECT,
        db_column='id_oficina',
        null=True,
        blank=True
    )
    titulo = models.ForeignKey(
        'Titulo',
        on_delete=models.PROTECT,
        db_column='id_titulo',
        null=True,
        blank=True
    )
    nivel = models.ForeignKey(
        'NivelBasico',
        on_delete=models.PROTECT,
        db_column='id_nivel',
        null=True,
        blank=True
    )
    basico = models.DecimalField(max_digits=10, decimal_places=2)

    SITUACION_CHOICES = [
        ('C', 'Contratado'),
        ('P', 'Permanente'),
    ]
    situacion = models.CharField(
        max_length=1,
        choices=SITUACION_CHOICES,
        null=True,
        blank=True
    )

    categoria_nombre = models.TextField(null=True, blank=True)
    oficina_nombre = models.TextField(null=True, blank=True)
    titulo_completo = models.TextField(null=True, blank=True)

    calificacion = models.DecimalField(max_digits=5, decimal_places=2)
    antiguedad = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Años de servicio (calculado por período con regla IPVU)"
    )

    supl1 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl3 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl4 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl6 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl8 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl12 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    bruto = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    jubilacion = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    obra_social = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    oficio_judicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Oficio Judicial',
        db_column='oficio_judicial',
    )
    liquido = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # --- COPIA AUTOMÁTICAMENTE LA SITUACIÓN DEL EMPLEADO ---
        if (not self.situacion or self.situacion == '') and self.empleado and hasattr(self.empleado, 'situacion'):
            self.situacion = self.empleado.situacion

        # --- BUSCA AUTOMÁTICAMENTE LA CALIFICACIÓN DEL MES ---
        from empleados.models import Calificacion  # evitar import circular
        try:
            self.calificacion = Calificacion.objects.get(
                empleado=self.empleado, año=self.año, mes=self.mes
            ).calificacion
        except Calificacion.DoesNotExist:
            self.calificacion = Decimal('100')  # Valor por defecto

        # 1) Básico calificado (bq)
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 2) Antigüedad por PERÍODO (regla IPVU: enero y julio)
        try:
            from empleados.utils import calcular_antiguedad_ipvu
            self.antiguedad = calcular_antiguedad_ipvu(
                getattr(self.empleado, 'fecha_ingreso', None),
                self.año, self.mes
            )
        except Exception:
            # Fallback defensivo si hubiera algún problema con la utilidad
            self.antiguedad = 0

        # 3) Bonificación por título (lee porcentaje desde FK)
        porcentaje = Decimal('0')
        if self.titulo and getattr(self.titulo, 'tipo', None) and getattr(self.titulo.tipo, 'porcentaje', None):
            porcentaje = Decimal(self.titulo.tipo.porcentaje) / Decimal('100')
        bonif = (bq * porcentaje).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 4) Importe de antigüedad
        ant_importe = (bq * Decimal('0.02') * Decimal(self.antiguedad or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 5) Subtotal (Total Básico)
        subtotal = (bq + ant_importe + bonif).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 6) Suplementos (si la categoría trae %)
        sup = self.categoria
        p1 = (getattr(sup, 'sup1', None) or Decimal('0')) / Decimal('100')
        p2 = (getattr(sup, 'sup2', None) or Decimal('0')) / Decimal('100')
        p3 = (getattr(sup, 'sup3', None) or Decimal('0')) / Decimal('100')
        p4 = (getattr(sup, 'sup4', None) or Decimal('0')) / Decimal('100')
        p6 = (getattr(sup, 'sup6', None) or Decimal('0')) / Decimal('100')
        p8 = (getattr(sup, 'sup8', None) or Decimal('0')) / Decimal('100')
        p12 = (getattr(sup, 'sup12', None) or Decimal('0')) / Decimal('100')

        self.supl1 = (subtotal * p1).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.supl2 = (subtotal * p2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.supl3 = (subtotal * p3).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.supl4 = (subtotal * p4).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.supl6 = (subtotal * p6).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.supl8 = (subtotal * p8).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.supl12 = (subtotal * p12).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        total_supl = sum(filter(None, [
            self.supl1, self.supl2, self.supl3,
            self.supl4, self.supl6, self.supl8,
            self.supl12
        ]))

        self.bruto = (subtotal + total_supl).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Descuentos ley
        self.jubilacion = (self.bruto * Decimal('0.11')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.obra_social = (self.bruto * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        neto = (self.bruto - self.jubilacion - self.obra_social).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # 7) Oficios Judiciales (múltiples oficios en el período)
        OficioJudicial = apps.get_model('empleados', 'OficioJudicial')
        oficios = OficioJudicial.objects.filter(
            anio=self.año,
            mes=self.mes,
            empleado=self.empleado
        )

        descuento = Decimal('0.00')
        for oj in oficios:
            if getattr(oj, 'tipo', 1) == 1:  # Monto fijo
                descuento += (oj.monto_descontar or Decimal('0.00'))
            else:  # Porcentaje
                pct = (oj.porcentaje_descontar or Decimal('0.00')) / Decimal('100')
                descuento += (neto * pct).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        self.oficio_judicial = descuento.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.liquido = (neto - self.oficio_judicial).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Copias “denormalizadas” para reportes
        self.categoria_nombre = self.categoria.nombre if self.categoria else None
        self.oficina_nombre = self.oficina.nombre if self.oficina else None
        self.titulo_completo = self.titulo.titulo_completo if self.titulo else None

        super().save(*args, **kwargs)

    @property
    def importe_titulo(self):
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        porcentaje = Decimal('0')
        if self.titulo and getattr(self.titulo, 'tipo', None) and getattr(self.titulo.tipo, 'porcentaje', None):
            porcentaje = Decimal(self.titulo.tipo.porcentaje) / Decimal('100')
        return (bq * porcentaje).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def importe_antiguedad(self):
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        años = Decimal(self.antiguedad or 0)
        return (bq * Decimal('0.02') * años).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if años else Decimal('0.00')

    @property
    def basico_total(self):
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        ant = self.importe_antiguedad
        bonif = self.importe_titulo
        return (bq + ant + bonif).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def total_suplementos(self):
        return sum(filter(None, [
            self.supl1, self.supl2, self.supl3,
            self.supl4, self.supl6, self.supl8,
            self.supl12
        ]))

    @property
    def total_descuentos(self):
        return (self.jubilacion or Decimal('0')) + (self.obra_social or Decimal('0')) + (self.oficio_judicial or Decimal('0'))

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.año}"

    class Meta:
        db_table = 'preliquidacion'
        verbose_name = "Preliquidación"
        verbose_name_plural = "Preliquidaciones"



# empleados/models.py

from decimal import Decimal
from django.db import models

class Liquidacion(models.Model):
    id_liquidacion       = models.AutoField(primary_key=True)
    año                  = models.PositiveSmallIntegerField(verbose_name='Año')
    mes                  = models.PositiveSmallIntegerField(
                              choices=[(i, i) for i in range(1, 13)],
                              verbose_name='Mes'
                           )
    empleado             = models.ForeignKey(
                              'Empleado',
                              on_delete=models.CASCADE,
                              db_column='id_empleado'
                           )
    categoria            = models.ForeignKey(
                              'Categoria',
                              on_delete=models.PROTECT,
                              db_column='id_categoria'
                           )
    oficina              = models.ForeignKey(
                              'Oficina',
                              on_delete=models.PROTECT,
                              db_column='id_oficina',
                              null=True,
                              blank=True
                           )
    titulo               = models.ForeignKey(
                              'Titulo',
                              on_delete=models.PROTECT,
                              db_column='id_titulo',
                              null=True,
                              blank=True
                           )
    nivel                = models.ForeignKey(
                              'NivelBasico',
                              on_delete=models.PROTECT,
                              db_column='id_nivel',
                              null=True,
                              blank=True
                           )

    basico               = models.DecimalField(
                              max_digits=10,
                              decimal_places=2,
                              null=True,
                              blank=True
                           )
    situacion            = models.CharField(
                              max_length=1,
                              choices=[('C','Contratado'), ('P','Permanente')],
                              null=True,
                              blank=True
                           )
    categoria_nombre     = models.TextField(null=True, blank=True)
    oficina_nombre       = models.TextField(null=True, blank=True)
    titulo_completo      = models.TextField(null=True, blank=True)

    calificacion         = models.DecimalField(
                              max_digits=5,
                              decimal_places=2,
                              null=True,
                              blank=True
                           )
    antiguedad           = models.PositiveSmallIntegerField(
                              null=True,
                              blank=True
                           )

    # Campos calculados en preliquidación, restaurados
    importe_titulo       = models.DecimalField(
                              max_digits=12,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )
    importe_antiguedad   = models.DecimalField(
                              max_digits=12,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )
    basico_total         = models.DecimalField(
                              max_digits=12,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )

    supl1                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl2                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl3                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl4                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl6                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl8                = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl12               = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    total_suplementos    = models.DecimalField(
                              max_digits=14,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )
    bruto                = models.DecimalField(
                              max_digits=14,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )

    jubilacion           = models.DecimalField(
                              max_digits=14,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )
    obra_social          = models.DecimalField(
                              max_digits=14,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )
    oficio_judicial      = models.DecimalField(
                              max_digits=12,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              verbose_name='Oficio Judicial',
                              db_column='oficio_judicial'
                           )
    total_descuentos     = models.DecimalField(
                              max_digits=14,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )
    liquido              = models.DecimalField(
                              max_digits=14,
                              decimal_places=2,
                              default=Decimal('0.00'),
                              null=True,
                              blank=True
                           )

    conformada           = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.año}"

    class Meta:
        db_table = 'liquidacion'
        verbose_name = "Liquidación"
        verbose_name_plural = "Liquidaciones"

        
        
# fonavi_project/apps/empleados/models.py

# empleados/models.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import models

def _q2(x: Decimal) -> Decimal:
    return (Decimal(x or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

class OficioJudicial(models.Model):
    anio = models.PositiveSmallIntegerField()
    mes  = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 13)])

    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.CASCADE,
        db_column='id_empleado',
        related_name='oficios_judiciales',
    )

    # Si tipo = MONTO -> usar este campo (en $)
    monto_descontar = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Monto a descontar"
    )
    # Si tipo = PORCENTAJE -> usar este campo (en %)
    porcentaje_descontar = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name="Porcentaje a descontar"
    )

    # 1=Monto, 2=Porcentaje
    TIPO_MONTO       = 1
    TIPO_PORCENTAJE  = 2
    TIPO_CHOICES = (
        (TIPO_MONTO,      'Monto fijo'),
        (TIPO_PORCENTAJE, 'Porcentaje'),
    )
    tipo = models.PositiveSmallIntegerField(
        choices=TIPO_CHOICES,
        default=TIPO_MONTO,
        verbose_name="Tipo de descuento"
    )

    class Meta:
        db_table  = 'oficio_judicial'
        # ❌ Quitamos la unicidad para permitir varios oficios en el mismo período
        # unique_together = (('anio', 'mes', 'empleado'),)
        indexes = [
            models.Index(fields=['empleado', 'anio', 'mes']),
        ]
        ordering = ['-id']  # más recientes primero

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.anio}"

    # --- Validación liviana para el admin/form ---
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.tipo == self.TIPO_MONTO:
            if self.monto_descontar is None and self.porcentaje_descontar in (None, 0, Decimal('0')):
                self.monto_descontar = Decimal('0.00')  # permitimos 0 pero no None
            self.porcentaje_descontar = None
        elif self.tipo == self.TIPO_PORCENTAJE:
            if self.porcentaje_descontar is None:
                self.porcentaje_descontar = Decimal('0.00')
            self.monto_descontar = None
        else:
            raise ValidationError("Tipo de oficio judicial inválido.")

    # --- Helper para calcular el importe a descontar sobre una base dada ---
    def calcular_descuento_sobre(self, importe_base: Decimal) -> Decimal:
        """
        Devuelve el descuento que corresponde aplicar sobre 'importe_base'.
        Si es MONTO, devuelve el monto. Si es PORCENTAJE, aplica el %.
        """
        if self.tipo == self.TIPO_MONTO:
            return _q2(self.monto_descontar or 0)
        pct = (Decimal(self.porcentaje_descontar or 0) / Decimal('100'))
        return _q2(Decimal(importe_base or 0) * pct)



# empleados/models.py
from django.conf import settings
from django.db import models

class Calificacion(models.Model):
    empleado     = models.ForeignKey(
        'Empleado',
        on_delete=models.CASCADE,
        db_column='id_empleado'
    )
    año          = models.PositiveSmallIntegerField()
    mes          = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 13)])
    calificacion = models.DecimalField(max_digits=5, decimal_places=2)
    id_usuario   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        verbose_name="Usuario que registra"
    )

    class Meta:
        db_table = 'calificacion'
        unique_together = ('empleado', 'año', 'mes')

    def __str__(self):
        return f"{self.empleado} – {self.año}/{self.mes}: {self.calificacion}"


# empleados/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class LiquidacionPeriodo(models.Model):
    ESTADO_ABIERTA     = "ABIERTA"
    ESTADO_CERRADA     = "CERRADA"
    ESTADO_CONFIRMADA  = "CONFIRMADA"
    ESTADOS = [
        (ESTADO_ABIERTA,    "Abierta"),
        (ESTADO_CERRADA,    "Cerrada"),
        (ESTADO_CONFIRMADA, "Confirmada"),
    ]

    periodo = models.CharField(max_length=7, unique=True, db_index=True)  # "YYYY-MM"
    estado  = models.CharField(max_length=12, choices=ESTADOS, default=ESTADO_ABIERTA)

    fecha_creada     = models.DateTimeField(auto_now_add=True)
    fecha_cerrada    = models.DateTimeField(null=True, blank=True)
    fecha_confirmada = models.DateTimeField(null=True, blank=True)

    abierta_por    = models.ForeignKey(User, null=True, blank=True, related_name="liqs_abiertas",   on_delete=models.SET_NULL)
    cerrada_por    = models.ForeignKey(User, null=True, blank=True, related_name="liqs_cerradas",   on_delete=models.SET_NULL)
    confirmada_por = models.ForeignKey(User, null=True, blank=True, related_name="liqs_confirmadas", on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Liquidación por período"
        verbose_name_plural = "Liquidaciones por período"
        ordering = ["-periodo"]
        db_table = "empleados_liquidacion_periodo"  # evita colisión con tu tabla existente

    def __str__(self):
        return f"{self.periodo} - {self.get_estado_display()}"

    @property
    def editable(self):     return self.estado == self.ESTADO_ABIERTA
    @property
    def solo_lectura(self): return self.estado == self.ESTADO_CONFIRMADA



# empleados/models.py  (o app donde ya tengas LiquidacionPeriodo)
from django.conf import settings
from django.db import models

def periodo_yyyymm(dt=None):
    from datetime import date
    d = dt or date.today()
    return f"{d.year:04d}-{d.month:02d}"

# empleados/models.py
class NovedadMensual(models.Model):
    class Tipo(models.TextChoices):
        EMPLEADO_ALTA   = "EMPLEADO_ALTA", "Alta de empleado"
        EMPLEADO_BAJA   = "EMPLEADO_BAJA", "Baja de empleado"
        CAMBIO_CATEG    = "CAMBIO_CATEG", "Cambio de categoría"
        CAMBIO_CALIF    = "CAMBIO_CALIF", "Cambio de calificación"
        OFICIO_CREADO   = "OFICIO_CREADO", "Oficio judicial creado"
        PRELIQ_GENERADA = "PRELIQ_GENERADA", "Preliquidación generada"
        OTRO            = "OTRO", "Otro"

    periodo     = models.CharField(max_length=7, db_index=True)  # "YYYY-MM"
    fecha       = models.DateTimeField(auto_now_add=True, db_index=True)
    tipo        = models.CharField(max_length=32, choices=Tipo.choices)
    descripcion = models.TextField(blank=True)
    empleado    = models.ForeignKey("empleados.Empleado", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="novedades")
    url         = models.URLField(blank=True)
    actor       = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="novedades_realizadas")
    area        = models.CharField(max_length=120, blank=True)
    extra       = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'empleados_novedadmensual'  # ✅ Esto es importante
        ordering = ["-fecha", "-id"]

    def __str__(self):
        emp = f" - {self.empleado}" if self.empleado_id else ""
        return f"[{self.periodo}] {self.get_tipo_display()}{emp}"