"""
Fixtures compartidos entre todos los tests de la app inventario.
"""
import pytest


XML_FACTURA_ELECTRONICA = """<?xml version="1.0" encoding="UTF-8"?>
<DTE>
  <Documento>
    <Encabezado>
      <IdDoc>
        <TipoDTE>33</TipoDTE>
        <Folio>{numero}</Folio>
        <FchEmis>2026-01-15</FchEmis>
      </IdDoc>
      <Receptor>
        <RUTRecep>{rut}</RUTRecep>
        <RznSocRecep>Cliente Test SpA</RznSocRecep>
        <GiroRecep>Comercio</GiroRecep>
        <DirRecep>Calle Falsa 123</DirRecep>
        <CmnaRecep>Santiago</CmnaRecep>
        <CiudadRecep>Santiago</CiudadRecep>
      </Receptor>
      <Totales>
        <MntNeto>10000</MntNeto>
        <IVA>1900</IVA>
        <MntTotal>11900</MntTotal>
      </Totales>
    </Encabezado>
    <Detalle>
      <NroLinDet>1</NroLinDet>
      <VlrCodigo>{codigo_producto}</VlrCodigo>
      <NmbItem>Producto de prueba</NmbItem>
      <QtyItem>{cantidad}</QtyItem>
      <PrcItem>5000</PrcItem>
      <MontoItem>10000</MontoItem>
      <UnmdItem>UN</UnmdItem>
    </Detalle>
  </Documento>
</DTE>
"""


def generar_xml_factura(numero=1001, rut="76123456-7", codigo_producto="PROD1", cantidad=2, tipo_dte=None):
    """
    Genera bytes de un XML DTE de prueba, reemplazando TipoDTE si se indica
    (ej. '52' para Guía de Despacho, '61' para Nota de Crédito).
    """
    xml = XML_FACTURA_ELECTRONICA.format(
        numero=numero, rut=rut, codigo_producto=codigo_producto, cantidad=cantidad
    )
    if tipo_dte:
        xml = xml.replace("<TipoDTE>33</TipoDTE>", f"<TipoDTE>{tipo_dte}</TipoDTE>")
    return xml.encode("utf-8")


@pytest.fixture
def xml_factura_valida():
    """Bytes de un XML de Factura Electrónica (TipoDTE 33) listo para usar."""
    return generar_xml_factura()


@pytest.fixture
def producto_prod1(db):
    """Producto con código PROD1, requerido para que el XML de prueba pueda enlazar el detalle."""
    from inventario.models import Producto
    return Producto.objects.create(codigo="PROD1", descripcion="Producto de prueba", stock_actual=100)


@pytest.fixture
def cliente_test(db):
    from inventario.models import Cliente
    return Cliente.objects.create(
        rut="11111111-1",
        razon_social="Cliente de Prueba SpA",
        direccion="Calle Falsa 123",
        comuna="Santiago",
        ciudad="Santiago",
    )
