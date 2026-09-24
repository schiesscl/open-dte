import pytest
from django.core.files.base import ContentFile

from inventario.models import Cliente, Factura, DetalleFactura
from inventario.utils import calcular_dv, procesar_factura_xml
from .conftest import generar_xml_factura


def test_calcular_dv():
    # Test cases with known RUTs and their expected DVs
    test_cases = {
        '12345678': '5',
        '12345684': 'K',
        '76612679': '0',
    }

    for rut, expected_dv in test_cases.items():
        assert calcular_dv(rut) == expected_dv, f"Failed for RUT: {rut}"


@pytest.mark.parametrize("rut_sin_dv,dv_esperado", [
    ("12345678", "5"),
    ("12345684", "K"),
    ("76612679", "0"),
    ("6.512.849", "7"),   # con puntos, debe limpiarlos antes de calcular
    ("7-654-321", "6"),   # con guiones sueltos, también debe limpiarlos
])
def test_calcular_dv_parametrizado(rut_sin_dv, dv_esperado):
    """Misma validación que test_calcular_dv, pero en formato parametrizado (más idiomático en pytest)."""
    assert calcular_dv(rut_sin_dv) == dv_esperado


# --- Tests de integración: procesar_factura_xml (requieren base de datos) ---

@pytest.mark.django_db
def test_procesar_factura_xml_crea_factura_cliente_y_detalle(producto_prod1):
    xml_bytes = generar_xml_factura(numero=1001, rut="76123456-7", codigo_producto="PROD1", cantidad=2)
    archivo = ContentFile(xml_bytes, name="factura_test.xml")

    exito, mensaje = procesar_factura_xml(archivo, None)

    assert exito is True
    assert Cliente.objects.filter(rut="76123456-7").exists()

    factura = Factura.objects.get(numero=1001, tipo_documento="FACTURA ELECTRONICA")
    assert factura.neto == 10000
    assert factura.iva == 1900
    assert factura.total == 11900

    detalle = DetalleFactura.objects.get(factura=factura)
    assert detalle.producto.codigo == "PROD1"
    assert float(detalle.cantidad) == 2


@pytest.mark.django_db
def test_procesar_factura_xml_duplicada_no_se_reprocesa(producto_prod1):
    xml_bytes = generar_xml_factura(numero=2002)

    archivo_1 = ContentFile(xml_bytes, name="factura_1.xml")
    exito_1, _ = procesar_factura_xml(archivo_1, None)
    assert exito_1 is True

    archivo_2 = ContentFile(xml_bytes, name="factura_2.xml")
    exito_2, mensaje_2 = procesar_factura_xml(archivo_2, None)

    assert exito_2 is False
    assert "ya existe" in mensaje_2
    assert Factura.objects.filter(numero=2002).count() == 1


@pytest.mark.django_db
def test_procesar_factura_xml_guia_despacho_pendiente_sin_descontar_stock(producto_prod1):
    xml_bytes = generar_xml_factura(numero=3003, codigo_producto="PROD1", cantidad=15, tipo_dte="52")
    archivo = ContentFile(xml_bytes, name="guia_test.xml")

    exito, _ = procesar_factura_xml(archivo, None)

    assert exito is True
    producto_prod1.refresh_from_db()
    assert producto_prod1.stock_actual == 100

    factura = Factura.objects.get(numero=3003, tipo_documento="GUIA DE DESPACHO")
    assert factura.estado_despacho == "PENDIENTE"


@pytest.mark.django_db
def test_procesar_factura_xml_nota_credito_aumenta_stock(producto_prod1):
    xml_bytes = generar_xml_factura(numero=4004, codigo_producto="PROD1", cantidad=5, tipo_dte="61")
    archivo = ContentFile(xml_bytes, name="nota_credito_test.xml")

    exito, _ = procesar_factura_xml(archivo, None)

    assert exito is True
    producto_prod1.refresh_from_db()
    assert producto_prod1.stock_actual == 100 + 5
    assert Factura.objects.get(numero=4004).estado_despacho == 'DESPACHADO'
