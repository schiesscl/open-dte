"""
Tests para la lógica de negocio dentro de los modelos: signals de HistorialStock
y reversión de stock al eliminar una Factura/Guía/Nota de Crédito.
"""
import pytest

from inventario.models import Producto, HistorialStock, DetalleFactura


@pytest.mark.django_db
def test_creacion_producto_crea_entrada_de_historial():
    producto = Producto.objects.create(codigo="P100", descripcion="Producto Test", stock_actual=10)

    historial = HistorialStock.objects.filter(producto=producto)
    assert historial.count() == 1
    assert historial.first().detalle == "Creación de producto"
    assert historial.first().stock_actual_nuevo == 10


@pytest.mark.django_db
def test_cambiar_stock_actual_crea_nueva_entrada_de_historial():
    producto = Producto.objects.create(codigo="P101", descripcion="Producto Test 2", stock_actual=5)

    producto.stock_actual = 8
    producto.save()

    assert HistorialStock.objects.filter(producto=producto).count() == 2
    ultimo = HistorialStock.objects.filter(producto=producto).order_by("-fecha").first()
    assert ultimo.stock_actual_anterior == 5
    assert ultimo.stock_actual_nuevo == 8


@pytest.mark.django_db
def test_guardar_sin_cambio_de_stock_no_duplica_historial():
    """Editar un campo que no sea stock_actual/stock_real no debe generar una nueva entrada."""
    producto = Producto.objects.create(codigo="P102", descripcion="Producto Test 3", stock_actual=5)

    producto.descripcion = "Producto Test 3 (editado)"
    producto.save()

    # Solo debe existir la entrada de la creación inicial
    assert HistorialStock.objects.filter(producto=producto).count() == 1


@pytest.mark.django_db
def test_eliminar_guia_despacho_revierte_stock(cliente_test):
    from inventario.models import Factura

    producto = Producto.objects.create(codigo="P200", descripcion="Producto Test 4", stock_actual=7)
    factura = Factura.objects.create(
        numero=500,
        tipo_documento="GUIA DE DESPACHO",
        fecha_emision="2026-01-01",
        cliente=cliente_test,
        neto=1000,
        iva=190,
        total=1190,
        estado_despacho="DESPACHADO",
    )
    DetalleFactura.objects.create(factura=factura, producto=producto, cantidad=3, precio_unitario=1000, total_linea=3000)

    factura.delete()

    producto.refresh_from_db()
    assert producto.stock_actual == 10  # 7 + 3 revertidos


@pytest.mark.django_db
def test_eliminar_nota_credito_revierte_stock(cliente_test):
    from inventario.models import Factura

    producto = Producto.objects.create(codigo="P201", descripcion="Producto Test 5", stock_actual=13)
    factura = Factura.objects.create(
        numero=501,
        tipo_documento="NOTA DE CREDITO",
        fecha_emision="2026-01-01",
        cliente=cliente_test,
        neto=1000,
        iva=190,
        total=1190,
        estado_despacho="DESPACHADO",
    )
    DetalleFactura.objects.create(factura=factura, producto=producto, cantidad=3, precio_unitario=1000, total_linea=3000)

    factura.delete()

    producto.refresh_from_db()
    assert producto.stock_actual == 10  # 13 - 3 revertidos


@pytest.mark.django_db
def test_eliminar_factura_pendiente_no_altera_stock(cliente_test):
    """Si la factura NUNCA fue despachada (estado_despacho=PENDIENTE), eliminarla no debe tocar el stock."""
    from inventario.models import Factura

    producto = Producto.objects.create(codigo="P202", descripcion="Producto Test 6", stock_actual=20)
    factura = Factura.objects.create(
        numero=502,
        tipo_documento="FACTURA ELECTRONICA",
        fecha_emision="2026-01-01",
        cliente=cliente_test,
        neto=1000,
        iva=190,
        total=1190,
        estado_despacho="PENDIENTE",
    )
    DetalleFactura.objects.create(factura=factura, producto=producto, cantidad=3, precio_unitario=1000, total_linea=3000)

    factura.delete()

    producto.refresh_from_db()
    assert producto.stock_actual == 20
