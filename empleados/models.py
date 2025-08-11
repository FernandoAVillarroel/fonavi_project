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

class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=15)
    cuil = models.CharField(max_length=20)
    numero_cuenta = models.CharField(max_length=20)
    situacion = models.CharField(max_length=1)
    estado = models.CharField(max_length=1)
    fecha_ingreso = models.DateField()
    antiguedad = models.PositiveSmallIntegerField(null=True, blank=True)
    area = models.CharField(max_length=40, choices=AREAS, default='PRESIDENCIA')
    fecha_salida = models.DateField(null=True, blank=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, db_column='id_categoria')
    oficina = models.ForeignKey(Oficina, on_delete=models.SET_NULL, null=True, db_column='id_oficina')
    titulo = models.ForeignKey(Titulo, on_delete=models.SET_NULL, null=True, db_column='id_titulo')
    nivel_basico = models.ForeignKey(NivelBasico, on_delete=models.SET_NULL, null=True, db_column='id_nivel')

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = 'empleados'





from decimal import Decimal
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
        help_text="Años de servicio"
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
        from empleados.models import Calificacion  # Import para evitar problemas circulares
        try:
            self.calificacion = Calificacion.objects.get(
                empleado=self.empleado, año=self.año, mes=self.mes
            ).calificacion
        except Calificacion.DoesNotExist:
            self.calificacion = Decimal('100')  # Valor por defecto

        # 1) Básico calificado
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'))

        # 2) Antigüedad: años enteros de servicio
        ingreso = getattr(self.empleado, 'fecha_ingreso', None)
        if ingreso:
            años_servicio = (date.today() - ingreso).days // 365
        else:
            años_servicio = 0
        self.antiguedad = años_servicio

        # 3) Bonificación por título (lee porcentaje desde FK)
        porcentaje = Decimal('0')
        if self.titulo and self.titulo.tipo and self.titulo.tipo.porcentaje:
            porcentaje = Decimal(self.titulo.tipo.porcentaje) / Decimal('100')
        bonif = (bq * porcentaje).quantize(Decimal('0.01'))

        # 4) Importe antigüedad
        ant_importe = (bq * Decimal('0.02') * años_servicio).quantize(Decimal('0.01')) if años_servicio else Decimal('0.00')

        # 5) Subtotal (Total Básico)
        subtotal = (bq + ant_importe + bonif).quantize(Decimal('0.01'))

        # 6) Suplementos
        sup = self.categoria
        p1 = (sup.sup1 or Decimal('0')) / Decimal('100')
        p2 = (sup.sup2 or Decimal('0')) / Decimal('100')
        p3 = (sup.sup3 or Decimal('0')) / Decimal('100')
        p4 = (sup.sup4 or Decimal('0')) / Decimal('100')
        p6 = (sup.sup6 or Decimal('0')) / Decimal('100')
        p8 = (sup.sup8 or Decimal('0')) / Decimal('100')
        p12 = (sup.sup12 or Decimal('0')) / Decimal('100')

        self.supl1 = (subtotal * p1).quantize(Decimal('0.01'))
        self.supl2 = (subtotal * p2).quantize(Decimal('0.01'))
        self.supl3 = (subtotal * p3).quantize(Decimal('0.01'))
        self.supl4 = (subtotal * p4).quantize(Decimal('0.01'))
        self.supl6 = (subtotal * p6).quantize(Decimal('0.01'))
        self.supl8 = (subtotal * p8).quantize(Decimal('0.01'))
        self.supl12 = (subtotal * p12).quantize(Decimal('0.01'))

        total_supl = sum(filter(None, [
            self.supl1, self.supl2, self.supl3,
            self.supl4, self.supl6, self.supl8,
            self.supl12
        ]))
        self.bruto = (subtotal + total_supl).quantize(Decimal('0.01'))

        self.jubilacion = (self.bruto * Decimal('0.11')).quantize(Decimal('0.01'))
        self.obra_social = (self.bruto * Decimal('0.05')).quantize(Decimal('0.01'))

        neto = (self.bruto - self.jubilacion - self.obra_social).quantize(Decimal('0.01'))

        # 7) Oficio Judicial y líquido
        OficioJudicial = apps.get_model('empleados', 'OficioJudicial')
        try:
            oj = OficioJudicial.objects.get(
                anio=self.año,
                mes=self.mes,
                empleado=self.empleado
            )
        except OficioJudicial.DoesNotExist:
            descuento = Decimal('0.00')
        else:
            if oj.tipo == OficioJudicial.TIPO_MONTO:
                descuento = oj.monto_descontar or Decimal('0.00')
            else:
                pct = (oj.porcentaje_descontar or Decimal('0.00')) / Decimal('100')
                descuento = (neto * pct).quantize(Decimal('0.01'))

        self.oficio_judicial = descuento
        self.liquido = (neto - descuento).quantize(Decimal('0.01'))

        self.categoria_nombre = self.categoria.nombre if self.categoria else None
        self.oficina_nombre = self.oficina.nombre if self.oficina else None
        self.titulo_completo = self.titulo.titulo_completo if self.titulo else None

        super().save(*args, **kwargs)

    @property
    def importe_titulo(self):
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'))
        porcentaje = Decimal('0')
        if self.titulo and self.titulo.tipo and self.titulo.tipo.porcentaje:
            porcentaje = Decimal(self.titulo.tipo.porcentaje) / Decimal('100')
        return (bq * porcentaje).quantize(Decimal('0.01'))

    @property
    def importe_antiguedad(self):
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'))
        años = self.antiguedad or 0
        return (bq * Decimal('0.02') * años).quantize(Decimal('0.01')) if años else Decimal('0.00')

    @property
    def basico_total(self):
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'))
        ant = self.importe_antiguedad
        bonif = self.importe_titulo
        return (bq + ant + bonif).quantize(Decimal('0.01'))

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

from decimal import Decimal
from django.db import models

class OficioJudicial(models.Model):
    anio   = models.PositiveSmallIntegerField()
    mes    = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,13)])
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.CASCADE,
        db_column='id_empleado'
    )
    monto_descontar      = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name="Monto a descontar"
    )
    porcentaje_descontar = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        verbose_name="Porcentaje a descontar"
    )

    TIPO_PORCENTAJE = 1
    TIPO_MONTO      = 2
    TIPO_CHOICES    = (
        (TIPO_PORCENTAJE, 'Porcentaje'),
        (TIPO_MONTO,      'Monto fijo'),
    )
    tipo = models.PositiveSmallIntegerField(
        choices=TIPO_CHOICES,
        default=TIPO_MONTO,
        verbose_name="Tipo de descuento"
    )

    class Meta:
        db_table = 'oficio_judicial'
        unique_together = (('anio','mes','empleado'),)

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.anio}"

class Calificacion(models.Model):
    empleado     = models.ForeignKey(
        'Empleado',
        on_delete=models.CASCADE,
        db_column='id_empleado'
    )
    año          = models.PositiveSmallIntegerField()
    mes          = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)]
    )
    calificacion = models.DecimalField(max_digits=5, decimal_places=2)
    id_usuario   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        verbose_name="Usuario que registra"
    )

    class Meta:
        db_table = 'calificacion'
        unique_together = ('empleado', 'año', 'mes')

    def __str__(self):
        return f"{self.empleado} – {self.año}/{self.mes}: {self.calificacion}"




