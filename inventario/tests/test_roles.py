"""
Tests del sistema de roles (inventario/roles.py) y su aplicación en las vistas.

Cubren:
- La restricción de rol funciona sin depender de settings.MODO_DEMO (aplica siempre).
- Los usuarios 'vendedor' y 'operario' son redirigidos fuera de las secciones que
  tienen bloqueadas, y pueden acceder a las que no.
- Las vistas CRUD que antes no tenían ninguna protección ahora exigen login
  (regresión de la vulnerabilidad de control de acceso corregida).
"""
import pytest
from django.urls import reverse

from inventario.roles import secciones_bloqueadas_de, seccion_bloqueada, redirect_por_rol


# --- Tests unitarios de inventario/roles.py ---

@pytest.mark.django_db
def test_seccion_bloqueada_para_vendedor(django_user_model):
    user = django_user_model.objects.create_user(username="vendedor", password="pass1234")
    assert seccion_bloqueada(user, "clientes") is True
    assert seccion_bloqueada(user, "productos") is False


@pytest.mark.django_db
def test_seccion_bloqueada_para_operario(django_user_model):
    user = django_user_model.objects.create_user(username="operario", password="pass1234")
    assert seccion_bloqueada(user, "productos") is True
    assert seccion_bloqueada(user, "despacho") is False


@pytest.mark.django_db
def test_seccion_bloqueada_usuario_sin_rol_restringido(django_user_model):
    user = django_user_model.objects.create_user(username="admin", password="pass1234")
    assert seccion_bloqueada(user, "clientes") is False
    assert seccion_bloqueada(user, "productos") is False


def test_seccion_bloqueada_usuario_anonimo():
    from django.contrib.auth.models import AnonymousUser
    assert seccion_bloqueada(AnonymousUser(), "clientes") is False


@pytest.mark.django_db
def test_redirect_por_rol(django_user_model):
    vendedor = django_user_model.objects.create_user(username="vendedor", password="pass1234")
    operario = django_user_model.objects.create_user(username="operario", password="pass1234")
    admin = django_user_model.objects.create_user(username="admin", password="pass1234")

    assert redirect_por_rol(vendedor) == "stock_vendedores"
    assert redirect_por_rol(operario) == "despacho"
    assert redirect_por_rol(admin) is None


@pytest.mark.django_db
def test_secciones_bloqueadas_de_expuesto_para_templates(django_user_model):
    vendedor = django_user_model.objects.create_user(username="vendedor", password="pass1234")
    assert "clientes" in secciones_bloqueadas_de(vendedor)
    assert "productos" not in secciones_bloqueadas_de(vendedor)


# --- Tests de integración: la restricción aplica SIEMPRE, sin depender de MODO_DEMO ---

@pytest.mark.django_db
@pytest.mark.parametrize("modo_demo", [False, True])
def test_vendedor_es_redirigido_de_clientes_independiente_de_modo_demo(
    client, django_user_model, settings, modo_demo
):
    settings.MODO_DEMO = modo_demo
    user = django_user_model.objects.create_user(username="vendedor", password="pass1234")
    client.force_login(user)

    response = client.get(reverse("lista_clientes"))

    assert response.status_code == 302
    assert response.url == reverse("stock_vendedores")


@pytest.mark.django_db
@pytest.mark.parametrize("modo_demo", [False, True])
def test_operario_es_redirigido_de_productos_independiente_de_modo_demo(
    client, django_user_model, settings, modo_demo
):
    settings.MODO_DEMO = modo_demo
    user = django_user_model.objects.create_user(username="operario", password="pass1234")
    client.force_login(user)

    response = client.get(reverse("lista_productos"))

    assert response.status_code == 302
    assert response.url == reverse("despacho")


@pytest.mark.django_db
def test_vendedor_puede_acceder_a_productos(client, django_user_model):
    user = django_user_model.objects.create_user(username="vendedor", password="pass1234")
    client.force_login(user)

    response = client.get(reverse("lista_productos"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_operario_puede_acceder_a_despacho(client, django_user_model):
    user = django_user_model.objects.create_user(username="operario", password="pass1234")
    client.force_login(user)

    response = client.get(reverse("despacho"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_no_tiene_secciones_bloqueadas(client, django_user_model):
    user = django_user_model.objects.create_user(username="admin", password="pass1234")
    client.force_login(user)

    for url_name in ("dashboard", "lista_clientes", "lista_facturas", "lista_productos", "despacho"):
        response = client.get(reverse(url_name))
        assert response.status_code == 200, f"admin no debería ser bloqueado en {url_name}"


# --- Regresión: vistas CRUD que antes NO exigían autenticación ---

@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name, kwargs",
    [
        ("crear_producto", {}),
        ("editar_producto_masivo", {}),
        ("historial_despachos", {}),
    ],
)
def test_vistas_crud_sin_parametros_exigen_login(client, url_name, kwargs):
    response = client.get(reverse(url_name, kwargs=kwargs))
    assert response.status_code == 302
    assert "/accounts/login/" in response.url or "login" in response.url


@pytest.mark.django_db
def test_editar_producto_exige_login(client, producto_prod1):
    response = client.get(reverse("editar_producto", kwargs={"id": producto_prod1.id}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_eliminar_producto_exige_login(client, producto_prod1):
    response = client.post(reverse("eliminar_producto", kwargs={"id": producto_prod1.id}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_editar_cliente_exige_login(client, cliente_test):
    response = client.get(reverse("editar_cliente", kwargs={"id": cliente_test.id}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_eliminar_cliente_exige_login(client, cliente_test):
    response = client.post(reverse("eliminar_cliente", kwargs={"id": cliente_test.id}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_facturas_cliente_exige_login(client, cliente_test):
    response = client.get(reverse("facturas_cliente", kwargs={"id": cliente_test.id}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_operario_es_redirigido_de_editar_cliente(client, django_user_model, cliente_test):
    user = django_user_model.objects.create_user(username="operario", password="pass1234")
    client.force_login(user)

    response = client.get(reverse("editar_cliente", kwargs={"id": cliente_test.id}))

    assert response.status_code == 302
    assert response.url == reverse("despacho")
