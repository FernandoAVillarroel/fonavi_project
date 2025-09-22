from django import template
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

register = template.Library()

# ----------------------------
# Helpers internos
# ----------------------------
def _to_decimal(val) -> Decimal:
    """Convierte a Decimal de forma segura (None, '', etc. -> 0)."""
    try:
        if val is None or val == "":
            return Decimal("0")
        return val if isinstance(val, Decimal) else Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")

def _q2(v: Decimal) -> Decimal:
    """Redondea a 2 decimales con HALF_UP."""
    return Decimal(v or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _fmt_num(v: Decimal) -> str:
    """
    1234567.89 -> '1.234.567,89' (puntos miles, coma decimales)
    """
    s = f"{v:,.2f}"  # 1,234,567.89
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

# ----------------------------
# Filtros públicos
# ----------------------------
@register.filter
def ars_strict(value):
    """
    Formato ESTRICTO: NO intenta detectar centavos.
    Usa exactamente el valor recibido de la DB.
    """
    return _fmt_num(_q2(_to_decimal(value)))

@register.filter
def ars(value):
    """Igual que ars_strict pero antepone '$'."""
    return f"${ars_strict(value)}"

@register.filter
def ars_auto(value):
    """
    Formatea con miles/decimales e INTENTA detectar valores en centavos.
    Úsalo solo si a veces recibís valores en centavos y otras veces en pesos.
    """
    v = _to_decimal(value)

    two_decimals = (v == v.quantize(Decimal("0.01")))
    is_integer   = (v == v.quantize(Decimal("1")))

    looks_like_cents = (
        (is_integer and abs(v) >= Decimal("10000")) or
        (two_decimals and abs(v) >= Decimal("1000000"))
    )
    if looks_like_cents:
        v = v / Decimal("100")

    return _fmt_num(_q2(v))

@register.filter
def ars_from_cents(value):
    """Cuando sabés que viene en centavos: divide por 100 y formatea."""
    return _fmt_num(_q2(_to_decimal(value) / Decimal("100")))
