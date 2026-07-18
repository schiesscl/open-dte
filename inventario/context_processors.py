import os
import logging
from django.conf import settings
from .roles import secciones_bloqueadas_de

logger = logging.getLogger(__name__)

def compartida_count(request):
    """
    Context processor que inyecta la cantidad de facturas pendientes en la carpeta compartida y sus rutas.
    """
    from .config import get_shared_dirs
    incoming_dir, processed_dir = get_shared_dirs()

    cant = 0
    if incoming_dir and os.path.exists(incoming_dir):
        try:
            # Listar archivos PDF y XML en la carpeta compartida
            archivos = [
                f for f in os.listdir(incoming_dir)
                if f.lower().endswith(('.pdf', '.xml')) and os.path.isfile(os.path.join(incoming_dir, f))
            ]
            cant = len(archivos)
        except Exception as e:
            logger.error("Error al listar archivos pendientes en la carpeta compartida: %s", e)

    return {
        'cant_compartidas': cant,
        'shared_incoming_dir': incoming_dir,
        'shared_processed_dir': processed_dir,
        'MODO_DEMO': getattr(settings, 'MODO_DEMO', False),
        # Secciones que el usuario logueado NO puede ver (ej. {'clientes', 'facturas'}).
        # Usar en templates: {% if 'clientes' not in secciones_bloqueadas %}...{% endif %}
        'secciones_bloqueadas': secciones_bloqueadas_de(getattr(request, 'user', None)),
    }

