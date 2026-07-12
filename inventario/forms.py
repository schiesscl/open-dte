from django import forms
from .models import Producto, Cliente, Factura

class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = ['codigo', 'codigo_alternativo', 'cant_alternativo', 'codigo_alternativo_2', 'cant_alternativo_2', 'codigo_alternativo_3', 'cant_alternativo_3', 'descripcion', 'unidad_medida',
                  'stock_actual', 'stock_real', 'stock_minimo', 'stock_sistema', 'precio_venta', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_alternativo': forms.TextInput(attrs={'class': 'form-control'}),
            'cant_alternativo': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'codigo_alternativo_2': forms.TextInput(attrs={'class': 'form-control'}),
            'cant_alternativo_2': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'codigo_alternativo_3': forms.TextInput(attrs={'class': 'form-control'}),
            'cant_alternativo_3': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_real': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_sistema': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)

        # Si estamos editando (hay instancia), protegemos el código
        if self.instance and self.instance.pk:
            self.fields['codigo'].widget = forms.TextInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'})


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'razon_social', 'giro', 'direccion', 'comuna', 'ciudad', 'telefono']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'giro': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        # Por seguridad contable, solo permitiremos editar la referencia o fechas, no los montos
        fields = ['numero', 'fecha_emision']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'}),
            'fecha_emision': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
