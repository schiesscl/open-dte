import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_normalizar_textos_conserva_stock_y_estado():
    anterior = [('inventario', '0001_initial')]
    actual = [('inventario', '0002_normalizar_campos_texto')]
    executor = MigrationExecutor(connection)
    executor.migrate(anterior)
    try:
        apps = executor.loader.project_state(anterior).apps
        producto = apps.get_model('inventario', 'Producto').objects.create(
            codigo='MIGRACION', descripcion='Prueba', stock_actual=27,
            codigo_alternativo=None, codigo_alternativo_2=None, codigo_alternativo_3=None, unidad_medida=None,
        )
        cliente = apps.get_model('inventario', 'Cliente').objects.create(
            rut='11111111-1', razon_social='Prueba', giro=None, telefono=None,
        )
        factura = apps.get_model('inventario', 'Factura').objects.create(
            numero=9999, cliente=cliente, tipo_documento='GUIA DE DESPACHO',
            estado_despacho='DESPACHADO', fecha_emision='2026-01-01',
            neto=1, iva=0, total=1, archivo_origen=None,
        )
        sucursal = apps.get_model('inventario', 'Sucursal').objects.create(nombre='Prueba', codigo='TEST', direccion=None)
        historial = apps.get_model('inventario', 'HistorialStock').objects.create(producto=producto, detalle=None)
        executor = MigrationExecutor(connection)
        executor.migrate(actual)
        apps = executor.loader.project_state(actual).apps
        producto = apps.get_model('inventario', 'Producto').objects.get(pk=producto.pk)
        assert producto.stock_actual == 27
        for campo in ['codigo_alternativo', 'codigo_alternativo_2', 'codigo_alternativo_3', 'unidad_medida']:
            assert getattr(producto, campo) == ''
        cliente = apps.get_model('inventario', 'Cliente').objects.get(pk=cliente.pk)
        assert cliente.giro == cliente.telefono == ''
        factura = apps.get_model('inventario', 'Factura').objects.get(pk=factura.pk)
        assert factura.archivo_origen == ''
        assert factura.estado_despacho == 'DESPACHADO'
        assert apps.get_model('inventario', 'Sucursal').objects.get(pk=sucursal.pk).direccion == ''
        assert apps.get_model('inventario', 'HistorialStock').objects.get(pk=historial.pk).detalle == ''
    finally:
        MigrationExecutor(connection).migrate(actual)
