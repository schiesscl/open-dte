from unittest.mock import MagicMock, patch

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from inventario.models import Despacho, Factura, HistorialStock
from inventario.utils import es_nombre_archivo_no_dte, procesar_factura_pdf, procesar_factura_xml
from inventario.views import procesar_carpeta_compartida_automatico
from .conftest import generar_xml_factura


@pytest.fixture
def operador(client, django_user_model):
    user = django_user_model.objects.create_superuser('operador', password='test-password')
    client.force_login(user)
    return client


@pytest.mark.parametrize('nombre', ['Libro Ventas.pdf', 'LIBRO_DE_COMPRAS.xml', 'libro-guías.pdf',
                                   'Cotización 123.pdf', 'presupuesto.xml', 'reporte.pdf'])
def test_filtro_no_dte(nombre):
    assert es_nombre_archivo_no_dte(nombre)
    with patch('inventario.utils.pdfplumber.open') as parser:
        assert not procesar_factura_pdf(ContentFile(b'', name=nombre), None)[0]
        parser.assert_not_called()


@pytest.mark.parametrize('nombre', ['factura.pdf', 'guia-52.xml', 'balanceador.xml', 'nota_credito.pdf'])
def test_filtro_permite_dte(nombre):
    assert not es_nombre_archivo_no_dte(nombre)


@pytest.mark.django_db
@pytest.mark.parametrize('titulo,tipo,stock,estado', [
    ('GUÍA DE DESPACHO ELECTRÓNICA', 'GUIA DE DESPACHO', 100, 'PENDIENTE'),
    ('NOTA DE CRÉDITO ELECTRÓNICA', 'NOTA DE CREDITO', 115, 'DESPACHADO'),
    ('FACTURA ELECTRONICA', 'FACTURA ELECTRONICA', 100, 'PENDIENTE'),
    ('FACTURA EXENTA ELECTRÓNICA', 'FACTURA ELECTRONICA EXENTA', 100, 'PENDIENTE'),
    ('Empresa SpA FACTURA ELECTRÓNICA', 'FACTURA ELECTRONICA', 100, 'PENDIENTE'),
    ('GUÍA DE\nDESPACHO\nELECTRÓNICA', 'GUIA DE DESPACHO', 100, 'PENDIENTE'),
])
def test_pdf_stock_y_tipo(producto_prod1, titulo, tipo, stock, estado):
    page = MagicMock()
    page.extract_text.return_value = f'{titulo}\nNº 123\n1 PROD1 Producto UN 15 100 0 1500\nReferencia cotización 45'
    with patch('inventario.utils.pdfplumber.open') as pdf:
        pdf.return_value.__enter__.return_value.pages = [page]
        exito, mensaje = procesar_factura_pdf(ContentFile(b'', name='documento.pdf'), None)
    assert exito, mensaje
    factura = Factura.objects.get(numero=123)
    assert factura.tipo_documento == tipo
    assert factura.estado_despacho == estado
    assert factura.detalles.count() == 1
    producto_prod1.refresh_from_db()
    assert producto_prod1.stock_actual == stock


@pytest.mark.django_db
@pytest.mark.parametrize('texto', ['COTIZACIÓN\nNº 123\nReferencia FACTURA ELECTRONICA',
                                  'BALANCE GENERAL\nNº 123', 'Libro de ventas sin folio'])
def test_pdf_no_dte_no_crea_factura(texto):
    page = MagicMock()
    page.extract_text.return_value = texto
    with patch('inventario.utils.pdfplumber.open') as pdf:
        pdf.return_value.__enter__.return_value.pages = [page]
        exito, mensaje = procesar_factura_pdf(ContentFile(b'', name='documento.pdf'), None)
    assert not exito
    assert 'Tipo de documento' in mensaje
    assert not Factura.objects.exists()


@pytest.mark.django_db
def test_xml_tipo_no_soportado_no_crea_documento():
    assert not procesar_factura_xml(ContentFile(generar_xml_factura(tipo_dte='39'), name='dte.xml'), None)[0]
    assert not Factura.objects.exists()


@pytest.mark.django_db
def test_xml_fallo_parcial_revierte_stock_y_documento(producto_prod1):
    xml = generar_xml_factura(tipo_dte='61')
    detalle_invalido = b'<Detalle><NroLinDet>2</NroLinDet><VlrCodigo>PROD1</VlrCodigo><NmbItem>Producto</NmbItem><QtyItem>invalida</QtyItem></Detalle>'
    xml = xml.replace(b'</Documento>', detalle_invalido + b'</Documento>')
    exito, _ = procesar_factura_xml(ContentFile(xml, name='nota.xml'), None)
    assert not exito
    assert not Factura.objects.exists()
    producto_prod1.refresh_from_db()
    assert producto_prod1.stock_actual == 100
    assert HistorialStock.objects.filter(producto=producto_prod1).count() == 1


@pytest.mark.django_db
def test_guia_importar_buscar_confirmar_una_vez(operador, producto_prod1):
    assert procesar_factura_xml(ContentFile(generar_xml_factura(numero=52, cantidad=15, tipo_dte='52'), name='guia.xml'), None)[0]
    factura = Factura.objects.get(numero=52)
    response = operador.get(reverse('despacho'), {'buscar': 52})
    assert response.context['factura'] == factura
    assert 'GUIA DE DESPACHO' in response.content.decode()
    url = reverse('confirmar_despacho', args=[factura.pk])
    assert operador.post(url).status_code == 302
    assert operador.post(url).status_code == 302
    producto_prod1.refresh_from_db()
    factura.refresh_from_db()
    assert producto_prod1.stock_actual == 85
    assert factura.estado_despacho == 'DESPACHADO'
    assert Despacho.objects.filter(factura=factura).count() == 1
    assert HistorialStock.objects.filter(producto=producto_prod1, detalle='Despacho - Guía de despacho Nº 52').count() == 1


@pytest.mark.django_db
def test_busqueda_folio_compartido_y_nota_excluida(operador, producto_prod1):
    for tipo in ['33', '52', '61']:
        assert procesar_factura_xml(ContentFile(generar_xml_factura(numero=52, tipo_dte=tipo), name='dte.xml'), None)[0]
    response = operador.get(reverse('despacho'), {'buscar': 52})
    assert response.context['multiple_matches']
    assert {f.tipo_documento for f in response.context['matches']} == {'FACTURA ELECTRONICA', 'GUIA DE DESPACHO'}
    response = operador.get(reverse('despacho'), {'buscar': 52, 'tipo': 'GUIA DE DESPACHO'})
    assert response.context['factura'].tipo_documento == 'GUIA DE DESPACHO'
    response = operador.get(reverse('despacho'), {'buscar': 52, 'tipo': 'NOTA DE CREDITO'})
    assert response.context['factura'] is None


@pytest.mark.django_db
@pytest.mark.parametrize('tamano,esperado', [('20', 20), ('50', 50), ('100', 100), ('200', 200), ('todos', 205), ('invalido', 50)])
def test_dashboard_paginado_con_filtros(operador, cliente_test, tamano, esperado):
    Factura.objects.bulk_create([
        Factura(numero=n, cliente=cliente_test, fecha_emision='2026-01-15', neto=100, iva=19, total=119)
        for n in range(205)
    ])
    Factura.objects.create(numero=999, cliente=cliente_test, fecha_emision='2025-01-15', neto=100, iva=19, total=119)
    filtros = {'periodo': 'mes_especifico', 'mes': '1', 'anio': '2026', 'per_page': tamano}
    response = operador.get(reverse('dashboard'), filtros)
    assert response.status_code == 200
    assert response.context['total_documentos_periodo'] == 205
    assert len(response.context['documentos_periodo']) == esperado
    assert 'anio=2026' in response.context['querystring_filtros']
    assert 'mes=1' in response.context['querystring_filtros']
    for documento in response.context['documentos_periodo']:
        assert f'id="modalVerFactPeriodo{documento.pk}"' in response.content.decode()
    response = operador.get(reverse('dashboard'), {**filtros, 'per_page': '50', 'page': 2})
    assert response.context['page_obj'].start_index() == 51
    assert len(response.context['documentos_periodo']) == 50


@pytest.mark.django_db
@pytest.mark.parametrize('page', ['invalida', '-1', '999'])
def test_dashboard_vacio_y_pagina_invalida(operador, page):
    response = operador.get(reverse('dashboard'), {'per_page': 'todos', 'page': page})
    assert response.status_code == 200
    assert response.context['page_obj'].number == 1
    assert response.context['total_documentos_periodo'] == 0


def test_buzon_aparta_no_dte_sin_reintentar(tmp_path):
    incoming = tmp_path / 'entrada'
    incoming.mkdir()
    (incoming / 'Libro Ventas.pdf').write_bytes(b'no es un PDF DTE')
    with patch('inventario.config.get_shared_dirs', return_value=(str(incoming), str(tmp_path / 'procesados'))), \
         patch('inventario.views.procesar_factura_pdf') as parser:
        assert procesar_carpeta_compartida_automatico() == []
        assert procesar_carpeta_compartida_automatico() == []
        parser.assert_not_called()
    assert (tmp_path / 'entrada_errores' / 'Libro Ventas.pdf').exists()
    assert 'Archivo omitido' in (tmp_path / 'entrada_errores' / 'Libro Ventas.pdf.err').read_text(encoding='utf-8')
