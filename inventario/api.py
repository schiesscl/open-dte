from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Cliente, Producto, Factura, DetalleFactura
from .serializers import ClienteSerializer, ProductoSerializer, FacturaSerializer, DetalleFacturaSerializer
from .utils import procesar_factura_pdf, procesar_factura_xml

class FacturaUploadAPIView(APIView):
    """
    Endpoint dedicado a recibir y parsear archivos PDF y XML de facturas desde PWA/Frontend.
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get('archivo_factura')
        if not archivo:
            return Response({"error": "No se recibió ningún archivo"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            nombre_archivo = archivo.name.lower()
            if nombre_archivo.endswith('.pdf'):
                exito, mensaje = procesar_factura_pdf(archivo, request.user)
            elif nombre_archivo.endswith('.xml'):
                exito, mensaje = procesar_factura_xml(archivo, request.user)
            else:
                return Response({"error": "Formato no válido. Por favor, suba un archivo XML o PDF."}, status=status.HTTP_400_BAD_REQUEST)

            if exito:
                return Response({"mensaje": mensaje}, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": mensaje}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer

class DetalleFacturaViewSet(viewsets.ModelViewSet):
    queryset = DetalleFactura.objects.all()
    serializer_class = DetalleFacturaSerializer
