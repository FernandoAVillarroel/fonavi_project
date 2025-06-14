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


