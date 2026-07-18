"""
Tests de vistas (Django views): autenticación requerida y flujo de subida de documentos.
"""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from inventario.models import Factura
from .conftest import generar_xml_factura


@pytest.mark.django_db
def test_dashboard_redirige_si_no_autenticado(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_dashboard_devuelve_200_autenticado(client, django_user_model):
    user = django_user_model.objects.create_user(username="tester_dashboard", password="pass1234")
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_subir_documento_requiere_login(client):
    response = client.post(reverse("subir_documento"), {})
    assert response.status_code == 302


@pytest.mark.django_db
def test_subir_documento_via_view_procesa_xml(client, django_user_model, producto_prod1):
    user = django_user_model.objects.create_user(username="tester_subir", password="pass1234")
    client.force_login(user)

    xml_bytes = generar_xml_factura(numero=9001, codigo_producto="PROD1", cantidad=1)
    archivo = SimpleUploadedFile("factura.xml", xml_bytes, content_type="text/xml")

    response = client.post(reverse("subir_documento"), {"archivo_factura": archivo}, follow=True)

    assert response.status_code == 200
    assert Factura.objects.filter(numero=9001).exists()


@pytest.mark.django_db
def test_subir_documento_formato_no_soportado(client, django_user_model):
    user = django_user_model.objects.create_user(username="tester_formato", password="pass1234")
    client.force_login(user)

    archivo = SimpleUploadedFile("factura.txt", b"contenido invalido", content_type="text/plain")
    response = client.post(reverse("subir_documento"), {"archivo_factura": archivo}, follow=True)

    assert response.status_code == 200
    mensajes = [str(m) for m in response.context["messages"]]
    assert any("Formato no válido" in m for m in mensajes)


@pytest.mark.django_db
def test_api_producto_por_codigo_encuentra_producto(client, producto_prod1):
    response = client.get(reverse("api_producto_por_codigo"), {"codigo": "PROD1"})

    assert response.status_code == 200
    assert response.json()["codigo"] == "PROD1"


@pytest.mark.django_db
def test_api_producto_por_codigo_no_encontrado(client):
    response = client.get(reverse("api_producto_por_codigo"), {"codigo": "NO-EXISTE"})
    assert response.status_code == 404


@pytest.mark.django_db
def test_api_producto_por_codigo_sin_parametro(client):
    response = client.get(reverse("api_producto_por_codigo"))
    assert response.status_code == 400
