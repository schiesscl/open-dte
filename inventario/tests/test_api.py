"""
Tests para los endpoints DRF (ViewSets registrados en opendte_config/urls.py).

Los ViewSets en inventario/api.py (ClienteViewSet, ProductoViewSet, FacturaViewSet,
DetalleFacturaViewSet) y FacturaUploadAPIView requieren `IsAuthenticated`: un usuario
anónimo recibe 401/403, y un usuario autenticado puede operar con normalidad.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status

from inventario.models import Cliente


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def usuario_api(django_user_model):
    return django_user_model.objects.create_user(username="usuario_api", password="pass1234")


@pytest.fixture
def api_client_autenticado(api_client, usuario_api):
    api_client.force_authenticate(user=usuario_api)
    return api_client


@pytest.mark.django_db
def test_cliente_api_rechaza_creacion_anonima(api_client):
    response = api_client.post("/api/clientes/", {
        "rut": "99999999-9",
        "razon_social": "Anonimo SA",
        "direccion": "Calle X",
        "comuna": "Santiago",
        "ciudad": "Santiago",
    })

    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
    assert not Cliente.objects.filter(rut="99999999-9").exists()


@pytest.mark.django_db
def test_cliente_api_permite_creacion_autenticada(api_client_autenticado):
    response = api_client_autenticado.post("/api/clientes/", {
        "rut": "99999999-9",
        "razon_social": "Cliente Autenticado SA",
        "direccion": "Calle X",
        "comuna": "Santiago",
        "ciudad": "Santiago",
    })

    assert response.status_code == status.HTTP_201_CREATED
    assert Cliente.objects.filter(rut="99999999-9").exists()


@pytest.mark.django_db
def test_cliente_api_lista_requiere_autenticacion(api_client, cliente_test):
    response = api_client.get("/api/clientes/")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_cliente_api_lista_autenticado(api_client_autenticado, cliente_test):
    response = api_client_autenticado.get("/api/clientes/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    ruts = [c["rut"] for c in data["results"]] if "results" in data else [c["rut"] for c in data]
    assert "11111111-1" in ruts


@pytest.mark.django_db
def test_producto_api_crud_autenticado(api_client_autenticado):
    # Crear
    response = api_client_autenticado.post("/api/productos/", {
        "codigo": "API-001",
        "descripcion": "Producto vía API",
        "stock_actual": 5,
    })
    assert response.status_code == status.HTTP_201_CREATED
    producto_id = response.json()["id"]

    # Leer
    response = api_client_autenticado.get(f"/api/productos/{producto_id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["codigo"] == "API-001"

    # Actualizar (PATCH)
    response = api_client_autenticado.patch(f"/api/productos/{producto_id}/", {"stock_actual": 50}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["stock_actual"] == 50

    # Eliminar
    response = api_client_autenticado.delete(f"/api/productos/{producto_id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_producto_api_rechaza_acceso_anonimo(api_client):
    response = api_client.get("/api/productos/")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_factura_upload_api_rechaza_anonimo(api_client):
    response = api_client.post("/api/upload-factura/", {}, format="multipart")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_factura_upload_api_sin_archivo(api_client_autenticado):
    response = api_client_autenticado.post("/api/upload-factura/", {}, format="multipart")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


@pytest.mark.django_db
def test_factura_upload_api_formato_no_valido(api_client_autenticado):
    from django.core.files.uploadedfile import SimpleUploadedFile

    archivo = SimpleUploadedFile("factura.txt", b"contenido", content_type="text/plain")
    response = api_client_autenticado.post("/api/upload-factura/", {"archivo_factura": archivo}, format="multipart")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
