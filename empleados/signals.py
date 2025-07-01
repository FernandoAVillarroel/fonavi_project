# empleados/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Calificacion, Preliquidacion, Liquidacion

@receiver(post_save, sender=Calificacion)
def actualiza_porc_calificacion(sender, instance, **kwargs):
    """
    Cuando guardo una Calificacion, actualizo su valor en Preliquidacion
    (si ya existe) y luego en Liquidacion.
    No se crean filas nuevas.
    """
    filtros = {
        'empleado': instance.empleado,
        'año':       instance.año,
        'mes':       instance.mes,
    }
    # 1) actualizo SOLO el campo calificacion de la preliquidacion
    updated = Preliquidacion.objects.filter(**filtros).update(
        calificacion=instance.calificacion
    )
    if not updated:
        # no había preliquidacion, salgo
        return

    # 2) si se actualizó, propago el cambio a la liquidacion
    pre = Preliquidacion.objects.get(**filtros)
    Liquidacion.objects.filter(**filtros).update(
        calificacion=pre.calificacion
    )

@receiver(post_save, sender=Preliquidacion)
def propagar_desde_preliquidacion(sender, instance, created, **kwargs):
    """
    Cada vez que se guarde o actualice una Preliquidacion:
      - Crea/actualiza la Liquidacion con todos los campos calculados.
    """
    Liquidacion.objects.update_or_create(
        empleado=instance.empleado,
        año=instance.año,
        mes=instance.mes,
        defaults={
            'categoria'       : instance.categoria,
            'oficina'         : instance.oficina,
            'titulo'          : instance.titulo,
            'nivel'           : instance.nivel,
            'basico'          : instance.basico,
            'situacion'       : instance.situacion,
            'categoria_nombre': instance.categoria_nombre,
            'oficina_nombre'  : instance.oficina_nombre,
            'titulo_completo' : instance.titulo_completo,
            'calificacion'    : instance.calificacion,
            'antiguedad'      : instance.antiguedad,
            'supl1'           : instance.supl1,
            'supl2'           : instance.supl2,
            'supl3'           : instance.supl3,
            'supl4'           : instance.supl4,
            'supl6'           : instance.supl6,
            'supl8'           : instance.supl8,
            'supl12'          : instance.supl12,
            'bruto'           : instance.bruto,
            'jubilacion'      : instance.jubilacion,
            'obra_social'     : instance.obra_social,
            'liquido'         : instance.liquido,
        }
    )
