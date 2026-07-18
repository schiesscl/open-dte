"""
Sistema de roles de la aplicación.

Diseño deliberado: se mantiene el hardcodeo por username (en vez de un sistema
genérico de Groups/permisos de Django) porque la aplicación solo tiene 3 perfiles
fijos y conocidos de antemano: 'admin' (sin restricciones), 'vendedor' y 'operario'.
Un sistema de permisos genérico agregaría complejidad de configuración y pruebas
sin aportar valor real a este tamaño de proyecto.

Lo que SÍ se centraliza aquí es el mapeo rol -> secciones bloqueadas, para que
exista una única fuente de verdad reutilizable desde:
- Vistas Django (decorador `bloquear_seccion`)
- API DRF (ver inventario/api.py)
- Templates (ver context_processors.py)

IMPORTANTE: a diferencia del código original, esta restricción NO depende de
`settings.MODO_DEMO`. La restricción de rol es una regla de control de acceso
real y debe aplicar siempre; MODO_DEMO solo debe controlar funcionalidades
propias del entorno de demostración (ej. el botón de reset de datos).
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

# Mapeo hardcodeado: username -> secciones bloqueadas + vista de redirección por defecto.
ROLES_RESTRINGIDOS = {
    'vendedor': {
        'secciones_bloqueadas': {
            'dashboard', 'subir_documento', 'clientes', 'facturas',
            'despacho', 'compartida', 'configuracion',
        },
        'redirect': 'stock_vendedores',
    },
    'operario': {
        'secciones_bloqueadas': {
            'dashboard', 'subir_documento', 'productos', 'clientes',
            'facturas', 'compartida', 'configuracion',
        },
        'redirect': 'despacho',
    },
}


def seccion_bloqueada(user, seccion):
    """Retorna True si el usuario autenticado tiene bloqueada la sección indicada."""
    if not getattr(user, 'is_authenticated', False):
        return False
    regla = ROLES_RESTRINGIDOS.get(user.username)
    return bool(regla and seccion in regla['secciones_bloqueadas'])


def redirect_por_rol(user):
    """Nombre de URL al que redirigir a este usuario si intenta entrar a una
    sección bloqueada (o None si no tiene un rol con restricciones)."""
    regla = ROLES_RESTRINGIDOS.get(getattr(user, 'username', None))
    return regla['redirect'] if regla else None


def secciones_bloqueadas_de(user):
    """Set de secciones bloqueadas para este usuario (vacío si no tiene rol restringido).
    Útil para exponer en templates vía context processor."""
    if not getattr(user, 'is_authenticated', False):
        return set()
    regla = ROLES_RESTRINGIDOS.get(getattr(user, 'username', None))
    return regla['secciones_bloqueadas'] if regla else set()


def bloquear_seccion(seccion, mensaje=None):
    """
    Decorador de vistas: bloquea el acceso si el usuario autenticado tiene la
    sección restringida según ROLES_RESTRINGIDOS, redirigiéndolo a su pantalla
    permitida por defecto.

    Debe aplicarse DESPUÉS de @login_required (es decir, más cerca de la
    función) para garantizar que `request.user` ya esté autenticado:

        @login_required
        @bloquear_seccion('clientes')
        def lista_clientes(request):
            ...
    """
    def decorador(vista):
        @wraps(vista)
        def wrapper(request, *args, **kwargs):
            if seccion_bloqueada(request.user, seccion):
                messages.warning(
                    request,
                    mensaje or "Acceso restringido: tu perfil no tiene acceso a esta sección."
                )
                return redirect(redirect_por_rol(request.user))
            return vista(request, *args, **kwargs)
        return wrapper
    return decorador
