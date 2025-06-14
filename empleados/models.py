from django.db import models

class Categoria(models.Model):
    id_categoria = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)
    id_nivel = models.IntegerField()
    tipo_supl1 = models.IntegerField()
    supl1 = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_supl2 = models.IntegerField()
    supl2 = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_supl3 = models.IntegerField()
    supl3 = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_supl4 = models.IntegerField()
    supl4 = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_supl6 = models.IntegerField()
    supl6 = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_supl8 = models.IntegerField()
    supl8 = models.DecimalField(max_digits=10, decimal_places=2)
    supl12 = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_supl12 = models.IntegerField()

    class Meta:
        db_table = 'categorias'  # <-- MUY importante para usar la tabla real


class Oficina(models.Model):
    id_oficina = models.AutoField(primary_key=True)  # Si tu tabla tiene PK manual
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'oficinas'  # ← nombre exacto de tu tabla en MySQL


class NivelBasico(models.Model):
    id_nivel = models.AutoField(primary_key=True)  # si la tabla usa este campo como PK
    nivel = models.PositiveIntegerField(unique=True)
    descripcion = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Nivel {self.nivel}"

    class Meta:
        db_table = 'nivel_basico'  # ← nombre exacto de la tabla real


class Titulo(models.Model):
    id_titulo = models.AutoField(primary_key=True)  # si tu tabla tiene esta PK
    nombre = models.CharField(max_length=100, unique=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_resolucion = models.DateField()

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'titulos'  # ← nombre exacto de la tabla en tu base


class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20)
    cuil = models.CharField(max_length=20)
    numero_cuenta = models.CharField(max_length=20)
    situacion = models.CharField(max_length=1)
    estado = models.CharField(max_length=1)
    fecha_ingreso = models.DateField()
    antiguedad = models.IntegerField(null=True, blank=True)
    fecha_salida = models.DateField(null=True, blank=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        db_column='id_categoria'
    )
    oficina = models.ForeignKey(
        Oficina,
        on_delete=models.PROTECT,
        db_column='id_oficina'
    )
    titulo = models.ForeignKey(
        Titulo,
        on_delete=models.PROTECT,
        db_column='id_titulo'
    )

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        db_table = 'empleados'



class Preliquidacion(models.Model):
    id_preliquidacion = models.AutoField(primary_key=True)  # si tu tabla usa este campo
    empleado          = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='id_empleado')
    categoria         = models.ForeignKey(Categoria, on_delete=models.PROTECT, db_column='id_categoria')
    año               = models.PositiveSmallIntegerField()
    MES_CHOICES       = [(i, i) for i in range(1, 13)]
    mes               = models.PositiveSmallIntegerField(choices=MES_CHOICES)
    calificacion      = models.DecimalField(max_digits=5, decimal_places=2)
    fecha             = models.DateField()
    salario_base      = models.DecimalField(max_digits=10, decimal_places=2)
    total_por_titulos = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.empleado} - {self.categoria} {self.mes}/{self.año}: {self.calificacion}"

    class Meta:
        db_table = 'preliquidacion'

class Liquidacion(models.Model):
    id_liquidacion    = models.AutoField(primary_key=True)  # si tu tabla usa este campo
    preliquidacion    = models.OneToOneField(Preliquidacion, on_delete=models.CASCADE, db_column='id_preliquidacion')
    fecha_liquidacion = models.DateField(auto_now_add=True)
    total             = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Liquidación {self.preliquidacion}"

    class Meta:
        db_table = 'liquidacion'
        
        
        
class Calificacion(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='id_empleado')
    año = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    calificacion = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'calificacion'

    def __str__(self):
        return f"{self.empleado} - {self.mes}/{self.año}: {self.calificacion}"


