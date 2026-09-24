import pytest
from django.core.management import call_command

from inventario.models import Producto, Factura


@pytest.mark.django_db
def test_demo_seed_compatible_con_campos_no_nulos(django_user_model):
    call_command('seed_demo')
    assert Producto.objects.count() == 433
    assert Factura.objects.count() == 4
    for username in ['admin', 'vendedor', 'operario']:
        assert django_user_model.objects.get(username=username).check_password('demo123')
    assert not Producto.objects.filter(codigo_alternativo__isnull=True).exists()
