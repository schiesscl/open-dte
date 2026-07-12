import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = os.path.join(settings.BASE_DIR, 'config.json')

def get_shared_dirs():
    """
    Retorna una tupla (incoming_dir, processed_dir) leída desde config.json.
    Si no existe o tiene algún error, retorna los valores por defecto en media.
    """
    default_incoming = os.path.join(settings.MEDIA_ROOT, 'compartida')
    default_processed = os.path.join(settings.MEDIA_ROOT, 'compartida_procesadas')

    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                incoming = config.get('incoming', default_incoming)
                processed = config.get('processed', default_processed)
                return incoming, processed
        except Exception as e:
            logger.error("Error al leer el archivo de configuración config.json: %s", e)

    return default_incoming, default_processed

def set_shared_dirs(incoming, processed):
    """
    Guarda las rutas absolutas para las carpetas compartidas en config.json.
    """
    config_data = {
        'incoming': incoming,
        'processed': processed
    }
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
