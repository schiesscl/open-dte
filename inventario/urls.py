from django.urls import path
from . import views

urlpatterns = [
    path('despacho/', views.preparar_despacho, name='despacho'),
    path('despacho/confirmar/<int:id>/', views.confirmar_despacho, name='confirmar_despacho'),
    path('despacho/historial/', views.historial_despachos, name='historial_despachos'),
    # --- RUTAS GENERALES ---
    path('', views.dashboard, name='dashboard'),
    path('subir/', views.subir_documento, name='subir_documento'),

    # --- RUTAS DE LECTURA (LISTAS) ---
    path('productos/', views.lista_productos, name='lista_productos'),
    path('stock-vendedores/', views.stock_vendedores, name='stock_vendedores'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('facturas/', views.lista_facturas, name='lista_facturas'),

    # --- RUTAS CRUD PRODUCTOS ---
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('productos/editar-masivo/', views.editar_producto_masivo, name='editar_producto_masivo'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    # CRUD Clientes
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:id>/', views.eliminar_cliente, name='eliminar_cliente'),

    # CRUD Facturas
    path('facturas/editar/<int:id>/', views.editar_factura, name='editar_factura'),
    path('facturas/eliminar/<int:id>/', views.eliminar_factura, name='eliminar_factura'),
    path('facturas/ver/<int:id>/', views.ver_factura, name='ver_factura'),
    path('clientes/<int:id>/facturas/', views.facturas_cliente, name='facturas_cliente'),

    # --- API ENDPOINTS ---
    path('api/producto-por-codigo/', views.api_producto_por_codigo, name='api_producto_por_codigo'),
    path('productos/guia/analizar/', views.analizar_guia_abastecimiento, name='analizar_guia_abastecimiento'),
    path('productos/guia/procesar/', views.procesar_guia_abastecimiento, name='procesar_guia_abastecimiento'),
    path('productos/importar-excel/analizar/', views.analizar_importar_excel, name='analizar_importar_excel'),
    path('productos/importar-excel/procesar/', views.procesar_importar_excel, name='procesar_importar_excel'),


    # Guía de Despacho
    path('despachos/guia/<int:id>/', views.ver_guia_despacho, name='ver_guia_despacho'),

    # Buzón Compartido / Carpeta Compartida
    path('compartida/', views.lista_compartida, name='lista_compartida'),
    path('compartida/subir-archivo/', views.subir_a_compartida, name='subir_a_compartida'),
    path('compartida/importar/', views.importar_factura_compartida, name='importar_factura_compartida'),
    path('compartida/eliminar/', views.eliminar_factura_compartida, name='eliminar_factura_compartida'),
    path('compartida/configurar/guardar/', views.guardar_configuracion, name='guardar_configuracion'),
    path('compartida/api/status/', views.compartida_api_status, name='compartida_api_status'),
    path('accounts/login/', views.login_demo, name='login_demo'),

    # --- DEMO RESET (JavaScript API) ---
    path('api/demo/reset/', views.api_demo_reset, name='api_demo_reset'),
]
