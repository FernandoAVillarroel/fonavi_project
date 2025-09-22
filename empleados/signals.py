# empleados/signals.py

from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from .models import (
    Calificacion,
    Preliquidacion,
    Liquidacion,
    OficioJudicial,
    Empleado,
    NovedadMensual,
)
from .services import registrar_novedad


# ========= TRACKING DE CAMBIOS EN EMPLEADO =========

@receiver(pre_save, sender=Empleado)
def _cache_old_empleado(sender, instance: Empleado, **kwargs):
    """Cachear valores anteriores del empleado para detectar cambios"""
    instance._old_values = {}
    if instance.pk:
        try:
            old = Empleado.objects.get(pk=instance.pk)
            instance._old_values = {
                'nombre': old.nombre,
                'apellido': old.apellido,
                'dni': old.dni,
                'cuil': old.cuil,
                'categoria': old.categoria_id,
                'oficina': old.oficina_id,
                'titulo': old.titulo_id,
                'antiguedad': getattr(old, 'antiguedad', None),
                'situacion': getattr(old, 'situacion', None),
                'estado': old.estado,
            }
        except Empleado.DoesNotExist:
            pass


@receiver(post_save, sender=Empleado)
def log_cambios_empleado(sender, instance: Empleado, created, **kwargs):
    """Registra cambios en empleados"""
    try:
        if created:
            # Alta de empleado
            registrar_novedad(
                tipo=NovedadMensual.Tipo.EMPLEADO_ALTA,
                descripcion=f"Alta de empleado: {instance.apellido}, {instance.nombre} (DNI: {instance.dni})",
                empleado=instance,
                area="PRESIDENCIA",
            )
        else:
            # Verificar cambios
            old_values = getattr(instance, '_old_values', {})
            cambios = []
            
            # Verificar cambios importantes
            if old_values.get('nombre') != instance.nombre:
                cambios.append(f"Nombre: {old_values.get('nombre')} → {instance.nombre}")
            
            if old_values.get('apellido') != instance.apellido:
                cambios.append(f"Apellido: {old_values.get('apellido')} → {instance.apellido}")
            
            if old_values.get('dni') != instance.dni:
                cambios.append(f"DNI: {old_values.get('dni')} → {instance.dni}")
            
            if old_values.get('categoria') != instance.categoria_id:
                old_cat = f"ID:{old_values.get('categoria')}" if old_values.get('categoria') else "Sin categoría"
                new_cat = f"{instance.categoria}" if instance.categoria else "Sin categoría"
                cambios.append(f"Categoría: {old_cat} → {new_cat}")
                
                # Registrar cambio de categoría específico
                registrar_novedad(
                    tipo=NovedadMensual.Tipo.CAMBIO_CATEG,
                    descripcion=f"Cambio de categoría para {instance.apellido}, {instance.nombre}: {old_cat} → {new_cat}",
                    empleado=instance,
                    area="PRESIDENCIA",
                )
            
            if old_values.get('oficina') != instance.oficina_id:
                old_of = f"ID:{old_values.get('oficina')}" if old_values.get('oficina') else "Sin oficina"
                new_of = f"{instance.oficina}" if instance.oficina else "Sin oficina"
                cambios.append(f"Oficina: {old_of} → {new_of}")
            
            if old_values.get('titulo') != instance.titulo_id:
                old_tit = f"ID:{old_values.get('titulo')}" if old_values.get('titulo') else "Sin título"
                new_tit = f"{instance.titulo}" if instance.titulo else "Sin título"
                cambios.append(f"Título: {old_tit} → {new_tit}")
            
            # Antigüedad
            old_ant = old_values.get('antiguedad')
            new_ant = getattr(instance, 'antiguedad', None)
            if old_ant != new_ant:
                cambios.append(f"Antigüedad: {old_ant or 'Sin definir'} → {new_ant or 'Sin definir'}")
            
            # Situación laboral
            old_sit = old_values.get('situacion')
            new_sit = getattr(instance, 'situacion', None)
            if old_sit != new_sit:
                sit_names = {'P': 'Permanente', 'C': 'Contratado', 'T': 'Temporal'}
                old_sit_name = sit_names.get(old_sit, old_sit or 'Sin definir')
                new_sit_name = sit_names.get(new_sit, new_sit or 'Sin definir')
                cambios.append(f"Situación: {old_sit_name} → {new_sit_name}")
            
            # Estado activo/inactivo
            # Estado activo/inactivo
            old_estado = old_values.get('estado', 1)
            new_estado = instance.estado
            if old_estado != new_estado:
                if new_estado == 0:  # 0 = Inactivo
                    registrar_novedad(
                        tipo=NovedadMensual.Tipo.EMPLEADO_BAJA,
                        descripcion=f"Baja de empleado: {instance.apellido}, {instance.nombre}",
                        empleado=instance,
                        area="PRESIDENCIA",
                    )
                    return
                else:
                    cambios.append("Estado: Inactivo → Activo")
            
            # Si hubo cambios, registrar novedad general
            if cambios:
                descripcion = f"Modificación de empleado {instance.apellido}, {instance.nombre}: " + "; ".join(cambios)
                registrar_novedad(
                    tipo=NovedadMensual.Tipo.OTRO,
                    descripcion=descripcion[:500],  # Limitar longitud
                    empleado=instance,
                    area="PRESIDENCIA",
                )
                
    except Exception as e:
        print(f"❌ Error registrando cambios empleado: {e}")
        # Agregar después de log_cambios_empleado

@receiver(post_delete, sender=Empleado)
def log_eliminacion_empleado(sender, instance: Empleado, **kwargs):
    """Registra cuando se elimina un empleado completamente"""
    from django.utils import timezone
    now = timezone.now()
    periodo_str = f"{now.year:04d}-{now.month:02d}"
    
    try:
        registrar_novedad(
            tipo=NovedadMensual.Tipo.EMPLEADO_BAJA,
            descripcion=f"Empleado eliminado del sistema: {instance.apellido}, {instance.nombre} (DNI: {instance.dni})",
            empleado=None,  # Ya no existe la instancia
            area="PRESIDENCIA",
            periodo=periodo_str,
        )
        print(f"✅ Novedad de eliminación registrada para {instance.apellido}, {instance.nombre}")
    except Exception as e:
        print(f"❌ Error registrando eliminación empleado: {e}")
        
# ========= CALIFICACIONES =========

@receiver(pre_save, sender=Calificacion)
def _cache_old_calificacion(sender, instance: Calificacion, **kwargs):
    """Cachear calificación anterior"""
    instance._old_calificacion = None
    if instance.pk:
        try:
            prev = Calificacion.objects.get(pk=instance.pk)
            instance._old_calificacion = prev.calificacion
        except Calificacion.DoesNotExist:
            pass


@receiver(post_save, sender=Calificacion)
def actualiza_porc_calificacion(sender, instance: Calificacion, created, **kwargs):
    """Propagar calificación y registrar novedad"""
    # 1) Propagar valores
    filtros = {
        'empleado': instance.empleado,
        'año': instance.año,
        'mes': instance.mes,
    }
    Preliquidacion.objects.filter(**filtros).update(calificacion=instance.calificacion)
    Liquidacion.objects.filter(**filtros).update(calificacion=instance.calificacion)

    # 2) Registrar novedad
    periodo_str = f"{int(instance.año):04d}-{int(instance.mes):02d}"
    try:
        if created:
            registrar_novedad(
                tipo=NovedadMensual.Tipo.CAMBIO_CALIF,
                descripcion=f"Nueva calificación: {instance.calificacion} para {instance.empleado} (Período: {periodo_str})",
                periodo=periodo_str,
                empleado=instance.empleado,
                area="PRESIDENCIA",
            )
        else:
            old = getattr(instance, '_old_calificacion', None)
            if old is not None and old != instance.calificacion:
                registrar_novedad(
                    tipo=NovedadMensual.Tipo.CAMBIO_CALIF,
                    descripcion=f"Calificación modificada de {old} a {instance.calificacion} para {instance.empleado} (Período: {periodo_str})",
                    periodo=periodo_str,
                    empleado=instance.empleado,
                    area="PRESIDENCIA",
                )
    except Exception as e:
        print(f"❌ Error registrando novedad calificación: {e}")


# ========= PRELIQUIDACIONES (SIN NOVEDADES) =========

@receiver(post_save, sender=Preliquidacion)
def propagar_desde_preliquidacion(sender, instance: Preliquidacion, created, **kwargs):
    """Solo propagar a liquidación, SIN registrar novedades"""
    if hasattr(instance, '_generando_masivamente'):
        return

    defaults = {
        'categoria': instance.categoria,
        'oficina': instance.oficina,
        'titulo': instance.titulo,
        'nivel': instance.nivel,
        'basico': instance.basico,
        'situacion': instance.situacion,
        'categoria_nombre': instance.categoria_nombre,
        'oficina_nombre': instance.oficina_nombre,
        'titulo_completo': instance.titulo_completo,
        'calificacion': instance.calificacion,
        'antiguedad': instance.antiguedad,
        'supl1': instance.supl1,
        'supl2': instance.supl2,
        'supl3': instance.supl3,
        'supl4': instance.supl4,
        'supl6': instance.supl6,
        'supl8': instance.supl8,
        'supl12': instance.supl12,
        'bruto': instance.bruto,
        'jubilacion': instance.jubilacion,
        'obra_social': instance.obra_social,
        'oficio_judicial': instance.oficio_judicial,
        'liquido': instance.liquido,
    }

    Liquidacion.objects.update_or_create(
        empleado=instance.empleado,
        año=instance.año,
        mes=instance.mes,
        defaults=defaults
    )
    
    # NO registramos novedad para preliquidaciones
    # para no saturar la lista de novedades


# ========= OFICIOS JUDICIALES =========

@receiver(post_save, sender=OficioJudicial)
def registrar_oficio_judicial(sender, instance: OficioJudicial, created, **kwargs):
    """Registrar novedad cuando se crea o modifica un oficio judicial"""
    if hasattr(instance, '_generando_masivamente'):
        return
    
    periodo_str = f"{int(instance.anio):04d}-{int(instance.mes):02d}"
    
    # Describir el tipo de descuento
    if instance.tipo == 1:  # Monto fijo
        detalle = f"${instance.monto_descontar}"
    else:  # Porcentaje
        detalle = f"{instance.porcentaje_descontar}%"
    
    try:
        if created:
            registrar_novedad(
                tipo=NovedadMensual.Tipo.OFICIO_CREADO,
                descripcion=f"Oficio judicial creado para {instance.empleado} - Descuento: {detalle} (Período: {periodo_str})",
                periodo=periodo_str,
                empleado=instance.empleado,
                area="PRESIDENCIA",
            )
        else:
            registrar_novedad(
                tipo=NovedadMensual.Tipo.OFICIO_CREADO,
                descripcion=f"Oficio judicial modificado para {instance.empleado} - Descuento: {detalle} (Período: {periodo_str})",
                periodo=periodo_str,
                empleado=instance.empleado,
                area="PRESIDENCIA",
            )
    except Exception as e:
        print(f"❌ Error registrando novedad oficio judicial: {e}")


@receiver(post_delete, sender=OficioJudicial)
def registrar_eliminacion_oficio(sender, instance: OficioJudicial, **kwargs):
    """Registrar cuando se elimina un oficio judicial"""
    periodo_str = f"{int(instance.anio):04d}-{int(instance.mes):02d}"
    try:
        registrar_novedad(
            tipo=NovedadMensual.Tipo.OFICIO_CREADO,  # Usar el mismo tipo
            descripcion=f"Oficio judicial eliminado para {instance.empleado} (Período: {periodo_str})",
            periodo=periodo_str,
            empleado=instance.empleado,
            area="PRESIDENCIA",
        )
    except Exception as e:
        print(f"❌ Error registrando eliminación oficio: {e}")


# ========= RECALCULO DE DESCUENTOS =========

@receiver(post_save, sender=OficioJudicial)
@receiver(post_delete, sender=OficioJudicial)
def propagar_descuento(sender, instance: OficioJudicial, **kwargs):
    """Recalcular descuentos en preliquidaciones y liquidaciones"""
    if hasattr(instance, '_generando_masivamente'):
        return
    if hasattr(instance, '_procesando_descuento'):
        return

    instance._procesando_descuento = True
    try:
        filtros = {
            'año': instance.anio,
            'mes': instance.mes,
            'empleado': instance.empleado
        }

        preliqs = Preliquidacion.objects.filter(**filtros)
        if not preliqs.exists():
            return

        for preliq in preliqs:
            oficios = OficioJudicial.objects.filter(
                anio=instance.anio,
                mes=instance.mes,
                empleado=instance.empleado
            )

            total_descuento_judicial = Decimal('0.00')
            for oficio in oficios:
                if oficio.tipo == 1:  # monto fijo
                    total_descuento_judicial += oficio.monto_descontar
                elif oficio.tipo == 2:  # porcentaje
                    porcentaje = (oficio.porcentaje_descontar or Decimal('0')) / Decimal('100.00')
                    total_descuento_judicial += (preliq.basico or Decimal('0')) * porcentaje

            if abs(total_descuento_judicial - Decimal(str(preliq.oficio_judicial or 0))) > Decimal('0.01'):
                Preliquidacion.objects.filter(pk=preliq.pk).update(oficio_judicial=total_descuento_judicial)
                nuevo_liquido = (preliq.bruto or Decimal('0')) - (
                    (preliq.jubilacion or Decimal('0')) +
                    (preliq.obra_social or Decimal('0')) +
                    total_descuento_judicial
                )
                Preliquidacion.objects.filter(pk=preliq.pk).update(liquido=nuevo_liquido)
                Liquidacion.objects.filter(**filtros).update(
                    oficio_judicial=total_descuento_judicial,
                    liquido=nuevo_liquido
                )
    finally:
        if hasattr(instance, '_procesando_descuento'):
            del instance._procesando_descuento