from django.db import models
from django.conf import settings
from django.db import models, transaction

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre       = models.CharField(max_length=100)

    nivel = models.ForeignKey(
        'NivelBasico',
        on_delete=models.PROTECT,
        db_column='id_nivel',
        null=True,
        blank=True,       
    )

    sup1       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup1  = models.IntegerField(db_column='tipo_sup1', null=True, blank=True)

    sup2       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup2  = models.IntegerField(db_column='tipo_sup2', null=True, blank=True)

    sup3       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup3  = models.IntegerField(db_column='tipo_sup3', null=True, blank=True)

    sup4       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup4  = models.IntegerField(db_column='tipo_sup4', null=True, blank=True)

    sup6       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup6  = models.IntegerField(db_column='tipo_sup6', null=True, blank=True)

    sup8       = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup8  = models.IntegerField(db_column='tipo_sup8', null=True, blank=True)

    sup12      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_sup12 = models.IntegerField(db_column='tipo_sup12', null=True, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'categorias'



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
    fecha_salida = models.DateField(null=True, blank=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, db_column='id_categoria')
    oficina = models.ForeignKey(Oficina, on_delete=models.SET_NULL, null=True, db_column='id_oficina')
    titulo = models.ForeignKey(Titulo, on_delete=models.SET_NULL, null=True, db_column='id_titulo')


    def __str__(self):
        # muestra “Nombre Apellido (DNI)”
        return f"{self.nombre} {self.apellido}" 
    
    class Meta:
        db_table = 'empleados'


from decimal import Decimal
from django.db import models

from decimal import Decimal
from django.db import models


class Preliquidacion(models.Model):
    id_preliquidacion = models.AutoField(primary_key=True)
    año = models.PositiveSmallIntegerField(verbose_name='Año')
    mes = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        verbose_name='Mes'
    )
    empleado = models.ForeignKey(
        'Empleado', on_delete=models.CASCADE, db_column='id_empleado'
    )
    categoria = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, db_column='id_categoria'
    )
    oficina = models.ForeignKey(
        'Oficina', on_delete=models.PROTECT, db_column='id_oficina',
        null=True, blank=True
    )
    titulo = models.ForeignKey(
        'Titulo', on_delete=models.PROTECT, db_column='id_titulo',
        null=True, blank=True
    )
    nivel = models.ForeignKey(
        'NivelBasico', on_delete=models.PROTECT, db_column='id_nivel',
        null=True, blank=True
    )
    basico = models.DecimalField(max_digits=10, decimal_places=2)

    SITUACION_CHOICES = [
        ('C', 'Contratado'),
        ('P', 'Permanente'),
    ]
    situacion = models.CharField(
        max_length=1,
        choices=SITUACION_CHOICES,
        null=True, blank=True,
        verbose_name='Situación'
    )

    # Volcado de nombres de FK
    categoria_nombre = models.TextField(null=True, blank=True)
    oficina_nombre   = models.TextField(null=True, blank=True)
    titulo_completo  = models.TextField(null=True, blank=True)

    calificacion = models.DecimalField(max_digits=5, decimal_places=2)
    antiguedad   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    supl1  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl2  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl3  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl4  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl6  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl8  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl12 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    bruto       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    jubilacion  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    obra_social = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # ------------- nuevo campo -----------------
    oficio_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Descuento Judicial',
    )
    liquido     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1) Básico calificado por calificación
        bq = (self.basico * (self.calificacion / Decimal('100'))).quantize(Decimal('0.01'))

        # 2) Antigüedad: 2% anual sobre bq
        años = self.antiguedad or Decimal('0')
        ant = (bq * Decimal('0.02') * años).quantize(Decimal('0.01'))
        self.antiguedad = ant

        # 3) Bonificación por título sobre bq
        tipo_str = str(self.titulo.tipo) if (self.titulo and self.titulo.tipo) else None
        pct_tit = {
            'Universitario': Decimal('0.50'),
            'Tecnicatura':   Decimal('0.35'),
            'Terciario':     Decimal('0.30'),
            'Secundario':    Decimal('0.28'),
        }.get(tipo_str, Decimal('0'))
        bonif = (bq * pct_tit).quantize(Decimal('0.01'))

        # 4) Subtotal
        subtotal = (bq + ant + bonif).quantize(Decimal('0.01'))

        # 5) Suplementos
        self.supl1  = (subtotal * (self.categoria.sup1  or 0)).quantize(Decimal('0.01'))
        self.supl2  = (subtotal * (self.categoria.sup2  or 0)).quantize(Decimal('0.01'))
        self.supl3  = (subtotal * (self.categoria.sup3  or 0)).quantize(Decimal('0.01'))
        self.supl4  = (subtotal * (self.categoria.sup4  or 0)).quantize(Decimal('0.01'))
        self.supl6  = (subtotal * (self.categoria.sup6  or 0)).quantize(Decimal('0.01'))
        self.supl8  = (subtotal * (self.categoria.sup8  or 0)).quantize(Decimal('0.01'))
        self.supl12 = (self.categoria.sup12 or Decimal('0')).quantize(Decimal('0.01'))

        # 6) Bruto
        total_supl = sum(filter(None, [
            self.supl1, self.supl2, self.supl3,
            self.supl4, self.supl6, self.supl8,
            self.supl12
        ]))
        self.bruto = (subtotal + total_supl).quantize(Decimal('0.01'))

        # 7) Aportes
        self.jubilacion  = (self.bruto * Decimal('0.11')).quantize(Decimal('0.01'))
        self.obra_social = (self.bruto * Decimal('0.05')).quantize(Decimal('0.01'))

        # 8) Calcular neto **antes** de descuento
        neto = (self.bruto - self.jubilacion - self.obra_social).quantize(Decimal('0.01'))

        # 9) Leer descuento judicial para este emp/año/mes
        try:
            desc = OficioJudicial.objects.get(
                anio=self.año,
                mes=self.mes,
                empleado=self.empleado
            ).monto_descontar
        except OficioJudicial.DoesNotExist:
            desc = Decimal('0.00')
        self.oficio_descuento = desc

        # 10) Aplicar descuento y asignar liquido final
        self.liquido = (neto - desc).quantize(Decimal('0.01'))

        # 11) Volcar nombres de FK
        self.categoria_nombre = self.categoria.nombre if self.categoria else None
        self.oficina_nombre   = self.oficina.nombre   if self.oficina   else None
        self.titulo_completo  = self.titulo.titulo_completo if self.titulo else None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.año}"

    class Meta:
        db_table = 'preliquidacion'
        verbose_name = "Preliquidación"
        verbose_name_plural = "Preliquidaciones"




from decimal import Decimal
from django.db import models
from django.apps import apps  # Para evitar importación circular

class Liquidacion(models.Model):
    id_liquidacion = models.AutoField(primary_key=True)
    año = models.PositiveSmallIntegerField(verbose_name='Año')
    mes = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        verbose_name='Mes'
    )
    empleado = models.ForeignKey(
        'Empleado', on_delete=models.CASCADE, db_column='id_empleado'
    )
    categoria = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, db_column='id_categoria'
    )
    oficina = models.ForeignKey(
        'Oficina', on_delete=models.PROTECT, db_column='id_oficina',
        null=True, blank=True
    )
    titulo = models.ForeignKey(
        'Titulo', on_delete=models.PROTECT, db_column='id_titulo',
        null=True, blank=True
    )
    nivel = models.ForeignKey(
        'NivelBasico', on_delete=models.PROTECT, db_column='id_nivel',
        null=True, blank=True
    )
    basico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    SITUACION_CHOICES = [
        ('C', 'Contratado'),
        ('P', 'Permanente'),
    ]
    situacion = models.CharField(
        max_length=1,
        choices=SITUACION_CHOICES,
        null=True, blank=True,
        verbose_name='Situación'
    )

    categoria_nombre = models.TextField(null=True, blank=True)
    oficina_nombre   = models.TextField(null=True, blank=True)
    titulo_completo  = models.TextField(null=True, blank=True)

    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    antiguedad   = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    supl1  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl2  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl3  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl4  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl6  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl8  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    supl12 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    bruto       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    jubilacion  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    obra_social = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    oficio_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Descuento Judicial',
    )
    liquido     = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1) Básico calificado
        b = self.basico or Decimal('0')
        pct = (self.calificacion or Decimal('0')) / Decimal('100')
        bq = (b * pct).quantize(Decimal('0.01'))

        # 2) Antigüedad: 2% anual sobre bq
        años = self.antiguedad or Decimal('0')
        ant = (bq * Decimal('0.02') * años).quantize(Decimal('0.01'))
        self.antiguedad = ant

        # 3) Bonificación por título sobre bq
        tipo_str = str(self.titulo.tipo) if (self.titulo and self.titulo.tipo) else None
        pct_tit = {
            'Universitario': Decimal('0.50'),
            'Tecnicatura':   Decimal('0.35'),
            'Terciario':     Decimal('0.30'),
            'Secundario':    Decimal('0.28'),
        }.get(tipo_str, Decimal('0'))
        bonif = (bq * pct_tit).quantize(Decimal('0.01'))

        # 4) Subtotal
        subtotal = (bq + ant + bonif).quantize(Decimal('0.01'))

        # 5) Suplementos
        self.supl1  = (subtotal * (self.categoria.sup1  or 0)).quantize(Decimal('0.01'))
        self.supl2  = (subtotal * (self.categoria.sup2  or 0)).quantize(Decimal('0.01'))
        self.supl3  = (subtotal * (self.categoria.sup3  or 0)).quantize(Decimal('0.01'))
        self.supl4  = (subtotal * (self.categoria.sup4  or 0)).quantize(Decimal('0.01'))
        self.supl6  = (subtotal * (self.categoria.sup6  or 0)).quantize(Decimal('0.01'))
        self.supl8  = (subtotal * (self.categoria.sup8  or 0)).quantize(Decimal('0.01'))
        self.supl12 = (self.categoria.sup12 or Decimal('0')).quantize(Decimal('0.01'))

        # 6) Bruto
        extras = sum(filter(None, [
            self.supl1, self.supl2, self.supl3,
            self.supl4, self.supl6, self.supl8,
            self.supl12
        ]))
        self.bruto = (subtotal + extras).quantize(Decimal('0.01'))

        # 7) Aportes
        self.jubilacion  = (self.bruto * Decimal('0.11')).quantize(Decimal('0.01'))
        self.obra_social = (self.bruto * Decimal('0.05')).quantize(Decimal('0.01'))

        # 8) Neto antes de descuento
        neto = (self.bruto - self.jubilacion - self.obra_social).quantize(Decimal('0.01'))

        # 9) Leer descuento judicial vía apps.get_model
        OficioJudicial = apps.get_model('empleados', 'OficioJudicial')
        try:
            desc = OficioJudicial.objects.get(
                anio=self.año,
                mes=self.mes,
                empleado=self.empleado
            ).monto_descontar
        except OficioJudicial.DoesNotExist:
            desc = Decimal('0.00')
        self.oficio_descuento = desc

        # 10) Aplicar descuento
        self.liquido = (neto - desc).quantize(Decimal('0.01'))

        # 11) Volcar nombres de FK
        self.categoria_nombre = self.categoria.nombre if self.categoria else None
        self.oficina_nombre   = self.oficina.nombre   if self.oficina   else None
        self.titulo_completo  = self.titulo.titulo_completo if self.titulo else None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.año}"

    class Meta:
        db_table = 'liquidacion'
        verbose_name = "Liquidación"
        verbose_name_plural = "Liquidaciones"



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

    def __str__(self):
        return f"{self.empleado} – {self.año}/{self.mes}: {self.calificacion}"

    def save(self, *args, **kwargs):
        # Sólo guardamos la propia Calificacion;
        # la señal post_save actualizará pre/liquidaciones.
        with transaction.atomic():
            super().save(*args, **kwargs)

# fonavi_project/apps/empleados/models.py

from django.db import models
from decimal import Decimal

class OficioJudicial(models.Model):
    anio = models.PositiveSmallIntegerField(verbose_name='Año')
    mes = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 13)],
        verbose_name='Mes'
    )
    empleado = models.ForeignKey(
        'Empleado',
        on_delete=models.CASCADE,
        verbose_name='Usuario (Empleado)'
    )
    monto_descontar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto a Descontar'
    )

    class Meta:
        unique_together = ('anio', 'mes', 'empleado')
        ordering = ['-anio', '-mes', 'empleado__apellido']
        verbose_name = 'Oficio Judicial'
        verbose_name_plural = 'Oficios Judiciales'

    def __str__(self):
        return f"{self.empleado} – {self.mes}/{self.anio}: {self.monto_descontar}"







