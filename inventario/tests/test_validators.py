import pytest
from inventario.utils import validar_rut_chileno, formatear_rut_chileno, calcular_dv

@pytest.mark.parametrize("rut_sin_dv, dv_esperado", [
    ("77267987", "4"),
    ("76123456", "0"),
    ("76844214", "2"),
    ("11111111", "1"),
    ("11111112", "K"),
])
def test_calcular_dv(rut_sin_dv, dv_esperado):
    assert calcular_dv(rut_sin_dv) == dv_esperado

@pytest.mark.parametrize("rut, valido", [
    ("77.267.987-4", True),
    ("77267987-4", True),
    ("772679874", True),
    ("76.123.456-0", True),
    ("76.844.214-2", True),
    ("11.111.111-1", True),
    ("11.111.112-K", True),
    ("11111112K", True),
    ("11.111.111-9", False),
    ("77.267.987-9", False),
    ("", False),
    (None, False),
    ("ABC", False),
])
def test_validar_rut_chileno(rut, valido):
    assert validar_rut_chileno(rut) == valido

def test_formatear_rut_chileno():
    assert formatear_rut_chileno("772679874") == "77.267.987-4"
    assert formatear_rut_chileno("77.267.987-4") == "77.267.987-4"
    assert formatear_rut_chileno("11111112K") == "11.111.112-K"
    assert formatear_rut_chileno("invalid") == "invalid"
