from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from inventario.models import (
    Factura, DetalleFactura, Despacho, Cliente, Producto,
    GuiaAbastecimiento, DetalleGuiaAbastecimiento, HistorialStock,
    Sucursal, Bodega
)

class Command(BaseCommand):
    help = 'Loads the anonymized demo seed data into the database'

    def handle(self, *args, **options):
        self.stdout.write("Deleting existing data...")
        try:
            with transaction.atomic():
                DetalleGuiaAbastecimiento.objects.all().delete()
                GuiaAbastecimiento.objects.all().delete()
                HistorialStock.objects.all().delete()
                Despacho.objects.all().delete()
                DetalleFactura.objects.all().delete()
                Factura.objects.all().delete()
                Producto.objects.all().delete()
                Cliente.objects.all().delete()
                Bodega.objects.all().delete()
                Sucursal.objects.all().delete()
            
            self.stdout.write("Loading demo seed data...")
            call_command('loaddata', 'demo_seed.json')
            self.stdout.write(self.style.SUCCESS("Demo seed data loaded successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding database: {e}"))
