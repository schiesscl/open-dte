from django import template

register = template.Library()

@register.filter
def price_format(value):
    """
    Formatea un número como entero con separador de miles.
    Ejemplos: 1000 -> "1.000", 1000000 -> "1.000.000"
    """
    if value is None:
        return "-"

    try:
        # Convertir a entero
        amount = int(float(value))
        # Formatear con separador de miles usando punto
        return f"{amount:,}".replace(",", ".")
    except (ValueError, TypeError):
        return "-"
