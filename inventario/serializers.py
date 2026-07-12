from rest_framework import serializers
from .models import Cliente, Producto, Factura, DetalleFactura

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class DetalleFacturaSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.ReadOnlyField(source='producto.codigo')
    producto_descripcion = serializers.ReadOnlyField(source='producto.descripcion')

    class Meta:
        model = DetalleFactura
        fields = '__all__'

class FacturaSerializer(serializers.ModelSerializer):
    cliente_razon_social = serializers.ReadOnlyField(source='cliente.razon_social')
    detalles = DetalleFacturaSerializer(many=True, read_only=True)

    class Meta:
        model = Factura
        fields = '__all__'
