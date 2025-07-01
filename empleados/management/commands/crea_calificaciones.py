from django.core.management.base import BaseCommand
from django.utils import timezone
from empleados.models import Empleado, Calificacion

class Command(BaseCommand):
    help = "Crea Calificacion al 100% para todos los empleados que aún no la tengan para mes/año actual."

    def handle(self, *args, **options):
        hoy = timezone.now()
        anyo = hoy.year
        mes  = hoy.month

        creadas = 0
        for emp in Empleado.objects.all():
            # get_or_create evita duplicados
            obj, created = Calificacion.objects.get_or_create(
                empleado=emp,
                año=anyo,
                mes=mes,
                defaults={'calificacion': 100.00, 'id_usuario': None},
            )
            if created:
                creadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"Comando completado: creadas {creadas} calificaciones al 100% para {mes}/{anyo}."
        ))
