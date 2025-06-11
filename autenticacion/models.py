from django.db import models

class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre     = models.CharField(max_length=150)
    contrasena = models.CharField(max_length=128)
    email      = models.CharField(max_length=255)
    tipo       = models.IntegerField()

    class Meta:
        managed  = False      # Django NO creará/alterará esta tabla
        db_table = 'usuarios' # nombre exacto de tu tabla en MySQL

class Empleados(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150)
    dni = models.CharField(max_length=20)
    cuil = models.CharField(max_length=20)
    numero_cuenta = models.CharField(max_length=30)
    SITUACION_CHOICES = (
        (1, 'Permanente'),
        (2, 'Contratado'),
    )
    situacion = models.IntegerField(choices=SITUACION_CHOICES)
    ESTADO_CHOICES = (
        (1, 'Activo'),
        (2, 'Inactivo'),
    )
    estado = models.IntegerField(choices=ESTADO_CHOICES)
    fecha_ingreso = models.DateField()
    antiguedad = models.IntegerField()
    fecha_salida = models.DateField(null=True, blank=True)

    class Meta:
        managed = False  # Si la tabla ya existe en la base de datos
        db_table = 'empleados'

class Oficinas(models.Model):
    id_oficina = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)

    class Meta:
        managed = False  # Si la tabla ya existe en la base de datos
        db_table = 'oficinas'