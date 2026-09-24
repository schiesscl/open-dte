from django import forms
from .models import Producto, Cliente, Factura

CSS_FORM_CONTROL = 'form-control'


class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = ['codigo', 'codigo_alternativo', 'cant_alternativo', 'codigo_alternativo_2', 'cant_alternativo_2', 'codigo_alternativo_3', 'cant_alternativo_3', 'descripcion', 'unidad_medida',
                  'stock_actual', 'stock_real', 'stock_minimo', 'stock_sistema', 'precio_venta', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'codigo_alternativo': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'cant_alternativo': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL, 'min': '1'}),
            'codigo_alternativo_2': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'cant_alternativo_2': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL, 'min': '1'}),
            'codigo_alternativo_3': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'cant_alternativo_3': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL, 'min': '1'}),
            'descripcion': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'unidad_medida': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'stock_actual': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL}),
            'stock_real': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL}),
            'stock_minimo': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL}),
            'stock_sistema': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL}),
            'precio_venta': forms.NumberInput(attrs={'class': CSS_FORM_CONTROL, 'step': '0.01'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)

        # Si estamos editando (hay instancia), protegemos el código
        if self.instance and self.instance.pk:
            self.fields['codigo'].widget = forms.TextInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'})


from .utils import validar_rut_chileno, formatear_rut_chileno

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['rut', 'razon_social', 'giro', 'direccion', 'comuna', 'ciudad', 'telefono']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control rut-input'}),
            'razon_social': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'giro': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'direccion': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'comuna': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'ciudad': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
            'telefono': forms.TextInput(attrs={'class': CSS_FORM_CONTROL}),
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut', '').strip()
        if rut and not validar_rut_chileno(rut):
            raise forms.ValidationError("El RUT ingresado no es válido según el dígito verificador.")
        return formatear_rut_chileno(rut)

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        # Por seguridad contable, solo permitiremos editar la referencia o fechas, no los montos
        fields = ['numero', 'fecha_emision']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'}),
            'fecha_emision': forms.DateInput(attrs={'class': CSS_FORM_CONTROL, 'type': 'date'}),
        }
