"""
URL configuration for OpenDTE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from inventario.api import ClienteViewSet, ProductoViewSet, FacturaViewSet, DetalleFacturaViewSet, FacturaUploadAPIView

# Router de la API
router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'detalles-factura', DetalleFacturaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventario.urls')),  # Conecta con la app inventario

    # Rutas API
    path('api/upload-factura/', FacturaUploadAPIView.as_view(), name='api-upload-factura'),
    path('api/', include(router.urls)),

    # Rutas para el modo PWA Offline
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw.js'),
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest.json'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
