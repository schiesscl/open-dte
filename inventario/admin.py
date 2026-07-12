from django.contrib import admin
from .models import Cliente, Producto, Factura, DetalleFactura, Sucursal, Bodega, HistorialStock

# Sucursales
@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'codigo')

# Bodegas
@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'sucursal', 'activa')
    list_filter = ('sucursal', 'activa')
    search_fields = ('nombre', 'codigo')

# Clientes
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('rut', 'razon_social', 'comuna', 'ciudad')
    search_fields = ('rut', 'razon_social')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'stock_actual', 'stock_minimo', 'precio_venta', 'activo')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('codigo', 'codigo_alternativo', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo',
                'codigo_alternativo', 'cant_alternativo',
                'codigo_alternativo_2', 'cant_alternativo_2',
                'codigo_alternativo_3', 'cant_alternativo_3',
                'descripcion', 'unidad_medida'
            )
        }),
        ('Inventario', {
            'fields': ('stock_actual', 'stock_real', 'stock_minimo')
        }),
        ('Precios y Estado', {
            'fields': ('precio_venta', 'activo')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

# Para ver los productos de la factura dentro de la misma pantalla de la factura
class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 1

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha_emision', 'total')
    list_filter = ('fecha_emision',)
    search_fields = ('numero', 'cliente__razon_social')
    inlines = [DetalleFacturaInline]  # Esto anida el detalle dentro de la factura

@admin.register(HistorialStock)
class HistorialStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'fecha', 'stock_actual_anterior', 'stock_actual_nuevo', 'stock_real_anterior', 'stock_real_nuevo', 'detalle', 'usuario')
    list_filter = ('fecha', 'detalle', 'usuario')
    search_fields = ('producto__codigo', 'producto__descripcion', 'detalle')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
