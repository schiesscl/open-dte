import os
import logging
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre Sucursal")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Bodega(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre Bodega")
    codigo = models.CharField(max_length=20, verbose_name="Código")
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="bodegas")
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"
        ordering = ['sucursal__nombre', 'nombre']
        unique_together = ['sucursal', 'codigo']

    def __str__(self):
        return f"{self.nombre} ({self.sucursal.codigo})"

class Cliente(models.Model):
    rut = models.CharField(max_length=15, unique=True, verbose_name="R.U.T.")
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social")
    giro = models.CharField(max_length=255, null=True, blank=True)
    direccion = models.CharField(max_length=255)
    comuna = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return str(f"{self.razon_social} ({self.rut})")

class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código Principal")
    codigo_alternativo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código Alternativo")
    cant_alternativo = models.IntegerField(default=1, verbose_name="Cantidad Alternativo 1 (Unidad)")
    codigo_alternativo_2 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código Alternativo 2")
    cant_alternativo_2 = models.IntegerField(default=1, verbose_name="Cantidad Alternativo 2 (Caja)")
    codigo_alternativo_3 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código Alternativo 3")
    cant_alternativo_3 = models.IntegerField(default=1, verbose_name="Cantidad Alternativo 3")
    descripcion = models.CharField(max_length=255)
    unidad_medida = models.CharField(max_length=10, default="UN", blank=True, null=True)

    # Inventario - Stocks
    stock_actual = models.IntegerField(default=0, blank=True, null=True, verbose_name="Stock Actual")
    stock_real = models.IntegerField(default=0, blank=True, null=True, verbose_name="Stock Real (Contado)")
    stock_minimo = models.IntegerField(default=0, blank=True, null=True, verbose_name="Stock Mínimo")
    stock_sistema = models.IntegerField(default=0, blank=True, null=True, verbose_name="Stock Sistema ERP")

    # Precios y estado
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True, null=True, verbose_name="Precio de Venta")
    activo = models.BooleanField(default=True)

    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo']),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.descripcion}"

    @property
    def stock_diferencia(self):
        """Calcula la diferencia entre stock sistema y stock actual (Sistema - Stock Local)"""
        sistema = self.stock_sistema if self.stock_sistema is not None else 0
        actual = self.stock_actual if self.stock_actual is not None else 0
        return sistema - actual

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario_modificador = None
        self.motivo_modificacion = None

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        stock_actual_anterior = None
        stock_real_anterior = None

        if not is_new:
            try:
                orig = Producto.objects.only('stock_actual', 'stock_real').get(pk=self.pk)
                stock_actual_anterior = orig.stock_actual
                stock_real_anterior = orig.stock_real
            except Producto.DoesNotExist:
                is_new = True

        super().save(*args, **kwargs)

        hizo_cambios = False
        detalle_log = getattr(self, 'motivo_modificacion', None)

        if is_new:
            hizo_cambios = True
            if not detalle_log:
                detalle_log = "Creación de producto"
        else:
            if stock_actual_anterior != self.stock_actual or stock_real_anterior != self.stock_real:
                hizo_cambios = True
                if not detalle_log:
                    detalle_log = "Edición de producto"

        if hizo_cambios:
            usuario_mod = getattr(self, 'usuario_modificador', None)
            if usuario_mod and not usuario_mod.is_authenticated:
                usuario_mod = None

            HistorialStock.objects.create(
                producto=self,
                stock_actual_anterior=stock_actual_anterior,
                stock_actual_nuevo=self.stock_actual,
                stock_real_anterior=stock_real_anterior,
                stock_real_nuevo=self.stock_real,
                detalle=detalle_log,
                usuario=usuario_mod
            )

class Factura(models.Model):
    usuario_creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    numero = models.IntegerField(verbose_name="Nº Factura")
    tipo_documento = models.CharField(max_length=50, default="FACTURA ELECTRONICA")
    fecha_emision = models.DateField()
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="facturas")
    neto = models.IntegerField()
    iva = models.IntegerField()
    total = models.IntegerField()
    fecha_subida = models.DateTimeField(auto_now_add=True)
    archivo_origen = models.CharField(max_length=255, blank=True, null=True, verbose_name="Archivo de origen")

    ESTADOS_DESPACHO = [
        ('PENDIENTE', 'Pendiente'),
        ('DESPACHADO', 'Despachado'),
    ]
    estado_despacho = models.CharField(max_length=20, choices=ESTADOS_DESPACHO, default='PENDIENTE')

    class Meta:
        unique_together = ('numero', 'tipo_documento')

    def __str__(self) -> str:
        return str(f"Factura {self.numero} - {self.cliente.razon_social}")

class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.IntegerField()
    total_linea = models.IntegerField()

    def __str__(self) -> str:
        return str(f"{self.cantidad} x {self.producto.codigo}")

class Despacho(models.Model):
    factura = models.OneToOneField(Factura, on_delete=models.CASCADE, related_name="despacho")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_despacho = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Despacho Factura {self.factura.numero} - {self.fecha_despacho.strftime('%d/%m/%Y %H:%M')}"

class GuiaAbastecimiento(models.Model):
    numero = models.IntegerField(unique=True, verbose_name="Nº Guía Abastecimiento")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Guía Abastecimiento {self.numero}"

class DetalleGuiaAbastecimiento(models.Model):
    guia = models.ForeignKey(GuiaAbastecimiento, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.codigo} en Guía {self.guia.numero}"

class HistorialStock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='historial_stock')
    fecha = models.DateTimeField(auto_now_add=True)

    # Valores de stock
    stock_actual_anterior = models.IntegerField(null=True, blank=True)
    stock_actual_nuevo = models.IntegerField(null=True, blank=True)

    stock_real_anterior = models.IntegerField(null=True, blank=True)
    stock_real_nuevo = models.IntegerField(null=True, blank=True)

    # Metadatos del cambio
    detalle = models.CharField(max_length=255, blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Historial de Stock"
        verbose_name_plural = "Historiales de Stock"

    def __str__(self):
        return f"Cambio en {self.producto.codigo} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=Factura)
def revertir_stock_factura_pre_delete(sender, instance, **kwargs):
    """
    Cuando se elimina una Factura, Guía de Despacho o Nota de Crédito, se revierte
    el stock modificado si el documento ya estaba en estado DESPACHADO.
    """
    if instance.estado_despacho == 'DESPACHADO':
        try:
            for detalle in instance.detalles.all():
                producto = detalle.producto
                cantidad = int(detalle.cantidad)

                if instance.tipo_documento == 'NOTA DE CREDITO':
                    # Restar stock porque la nota de crédito había sumado
                    producto.stock_actual = max(0, (producto.stock_actual or 0) - cantidad)
                    producto.motivo_modificacion = f"Reversión de Devolución - Nota de Crédito Nº {instance.numero} eliminada"
                else:
                    # Sumar stock porque el despacho había restado
                    producto.stock_actual = (producto.stock_actual or 0) + cantidad
                    producto.motivo_modificacion = f"Reversión de Despacho - Documento Nº {instance.numero} eliminado"

                producto.usuario_modificador = None
                producto.save()
        except Exception as e:
            logger.error("Error al revertir stock de la factura en pre_delete: %s", e)

@receiver(post_delete, sender=Factura)
def eliminar_archivo_factura_post_delete(sender, instance, **kwargs):
    if instance.archivo_origen:
        try:
            from .config import get_shared_dirs
            incoming_dir, processed_dir = get_shared_dirs()
            error_dir = incoming_dir + "_errores"

            # Eliminar de procesados
            proc_path = os.path.join(processed_dir, instance.archivo_origen)
            if os.path.exists(proc_path):
                os.remove(proc_path)

            # Eliminar de errores si existiera
            err_path = os.path.join(error_dir, instance.archivo_origen)
            if os.path.exists(err_path):
                os.remove(err_path)

            # Eliminar log de errores .err
            err_log = err_path + ".err"
            if os.path.exists(err_log):
                os.remove(err_log)
        except Exception as e:
            logger.error("Error al eliminar archivo de factura: %s", e)
