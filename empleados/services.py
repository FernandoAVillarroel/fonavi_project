# empleados/services.py
from django.utils import timezone
from typing import Optional, Union

from .models import NovedadMensual  # asegúrate de tener este modelo
# Si vas a pasar instancias de Empleado/Usuario como actor/empleado, no hace falta importarlas aquí.


def _resolve_id(obj_or_id: Optional[Union[int, object]]) -> Optional[int]:
    """Devuelve el id si recibe una instancia o el entero si ya es id."""
    if obj_or_id is None:
        return None
    return getattr(obj_or_id, "id", obj_or_id)

def _periodo_from_request(request) -> str:
    """Obtiene 'YYYY-MM' desde la sesión; si falla, usa el mes actual."""
    try:
        from .utils import get_periodo_from_session
        anio, mes, per = get_periodo_from_session(request)
        return per  # 'YYYY-MM'
    except Exception:
        now = timezone.now()
        return f"{now.year:04d}-{now.month:02d}"
    
    
    
    

def registrar_novedad(tipo, descripcion, empleado=None, periodo=None, area="", **kwargs):
    if not periodo:
        now = timezone.now()
        periodo = f"{now.year:04d}-{now.month:02d}"
    
    print(f"🔍 Intentando registrar novedad: {tipo} - {descripcion[:50]}")
    
    try:
        novedad = NovedadMensual.objects.create(
            tipo=tipo,
            descripcion=descripcion,
            empleado=empleado,
            periodo=periodo,
            area=area,
            fecha=timezone.now()
        )
        print(f"✅ Novedad creada con ID: {novedad.id}")
        return novedad
    except Exception as e:
        print(f"❌ Error creando novedad: {e}")
        return None