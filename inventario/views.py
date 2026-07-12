import os
import shutil
import logging
from django.conf import settings
from django.core.files import File
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, ProtectedError
from .models import Factura, Cliente, Producto, DetalleFactura, Despacho
from .utils import procesar_factura_xml, procesar_factura_pdf
from .forms import ProductoForm, ClienteForm, FacturaForm

logger = logging.getLogger(__name__)

def _mover_archivo_seguro(src, dst):
    """ Mueve un archivo a un destino, reemplazándolo si ya existe para evitar colisiones en Windows/Linux. """
    if os.path.exists(dst):
        try:
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        except Exception as e:
            logger.debug("No se pudo eliminar el destino anterior '%s' en _mover_archivo_seguro: %s", dst, e)
    shutil.move(src, dst)

def dashboard(request):
    """ Vista principal del panel de control con filtrado por período de tiempo """
    import datetime
    import calendar
    from django.utils import timezone

    # 1. Obtener parámetros de filtrado
    periodo = request.GET.get('periodo', 'mes_actual').strip()

    today = timezone.localdate()
    start_date = today.replace(day=1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end_date = today.replace(day=last_day)

    # Parámetros adicionales
    mes_sel = request.GET.get('mes', '')
    anio_sel = request.GET.get('anio', '')
    cantidad_sel = request.GET.get('cantidad', '')
    unidad_sel = request.GET.get('unidad', 'dias')
    desde_sel = request.GET.get('desde', '')
    hasta_sel = request.GET.get('hasta', '')

    if periodo == 'semana_actual':
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=6)
    elif periodo == 'anio_actual':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    elif periodo == 'mes_especifico':
        try:
            m = int(mes_sel) if mes_sel else today.month
            y = int(anio_sel) if anio_sel else today.year
            if 1 <= m <= 12:
                start_date = datetime.date(y, m, 1)
                last_day = calendar.monthrange(y, m)[1]
                end_date = datetime.date(y, m, last_day)
        except ValueError:
            pass
    elif periodo == 'anio_especifico':
        try:
            y = int(anio_sel) if anio_sel else today.year
            start_date = datetime.date(y, 1, 1)
            end_date = datetime.date(y, 12, 31)
        except ValueError:
            pass
    elif periodo == 'relativo':
        try:
            cant = int(cantidad_sel) if cantidad_sel else 30
            end_date = today
            if unidad_sel == 'dias':
                start_date = today - datetime.timedelta(days=cant)
            elif unidad_sel == 'semanas':
                start_date = today - datetime.timedelta(weeks=cant)
            elif unidad_sel == 'meses':
                start_date = today - datetime.timedelta(days=cant * 30)
            elif unidad_sel == 'anios':
                start_date = today - datetime.timedelta(days=cant * 365)
        except ValueError:
            pass
    elif periodo == 'personalizado':
        if desde_sel:
            try:
                start_date = datetime.datetime.strptime(desde_sel, '%Y-%m-%d').date()
            except ValueError:
                pass
        if hasta_sel:
            try:
                end_date = datetime.datetime.strptime(hasta_sel, '%Y-%m-%d').date()
            except ValueError:
                pass

    # Generar etiqueta humana para el período
    MESES_ESP = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    if periodo == 'mes_actual':
        periodo_label = f"Mes Actual ({MESES_ESP.get(today.month, '')} {today.year})"
    elif periodo == 'semana_actual':
        periodo_label = "Semana Actual"
    elif periodo == 'anio_actual':
        periodo_label = f"Año Actual ({today.year})"
    elif periodo == 'mes_especifico':
        try:
            m = int(mes_sel) if mes_sel else today.month
            y = int(anio_sel) if anio_sel else today.year
            periodo_label = f"{MESES_ESP.get(m, '')} {y}"
        except ValueError:
            periodo_label = "Mes Específico"
    elif periodo == 'anio_especifico':
        try:
            y = int(anio_sel) if anio_sel else today.year
            periodo_label = f"Año {y}"
        except ValueError:
            periodo_label = "Año Específico"
    elif periodo == 'relativo':
        try:
            cant = int(cantidad_sel) if cantidad_sel else 30
            unidad_dict = {'dias': 'Días', 'semanas': 'Semanas', 'meses': 'Meses', 'anios': 'Años'}
            uni_esp = unidad_dict.get(unidad_sel, unidad_sel)
            periodo_label = f"Últimos {cant} {uni_esp}"
        except ValueError:
            periodo_label = "Rango Relativo"
    elif periodo == 'personalizado':
        periodo_label = "Rango Personalizado"
    else:
        periodo_label = "Período Filtrado"

    # 2. Filtrar documentos del período por fecha_emision
    qs_periodo = Factura.objects.filter(fecha_emision__range=[start_date, end_date])

    # 3. Calcular métricas del período
    total_facturas_sum = qs_periodo.filter(tipo_documento__in=['FACTURA ELECTRONICA', 'FACTURA ELECTRONICA EXENTA']).aggregate(Sum('total'))['total__sum'] or 0
    total_notas_sum = qs_periodo.filter(tipo_documento='NOTA DE CREDITO').aggregate(Sum('total'))['total__sum'] or 0
    total_ventas = total_facturas_sum - total_notas_sum

    total_facturas = qs_periodo.filter(tipo_documento__in=['FACTURA ELECTRONICA', 'FACTURA ELECTRONICA EXENTA']).count()
    total_guias = qs_periodo.filter(tipo_documento='GUIA DE DESPACHO').count()
    total_notas = qs_periodo.filter(tipo_documento='NOTA DE CREDITO').count()

    # Sub-indicadores de Facturas
    facturas_despachadas = qs_periodo.filter(tipo_documento__in=['FACTURA ELECTRONICA', 'FACTURA ELECTRONICA EXENTA'], estado_despacho='DESPACHADO').count()
    facturas_pendientes = qs_periodo.filter(tipo_documento__in=['FACTURA ELECTRONICA', 'FACTURA ELECTRONICA EXENTA'], estado_despacho='PENDIENTE').count()

    # Sub-indicadores de Notas de Crédito
    notas_despachadas = qs_periodo.filter(tipo_documento='NOTA DE CREDITO', estado_despacho='DESPACHADO').count()
    notas_pendientes = qs_periodo.filter(tipo_documento='NOTA DE CREDITO', estado_despacho='PENDIENTE').count()

    # 4. Listar documentos
    ultimas_facturas = Factura.objects.all().order_by('-fecha_subida')[:10]
    documentos_periodo = qs_periodo.order_by('-fecha_emision', '-numero')[:50]

    contexto = {
        'total_ventas': total_ventas,
        'total_facturas': total_facturas,
        'total_guias': total_guias,
        'total_notas': total_notas,

        'facturas_despachadas': facturas_despachadas,
        'facturas_pendientes': facturas_pendientes,
        'notas_despachadas': notas_despachadas,
        'notas_pendientes': notas_pendientes,

        'ultimas_facturas': ultimas_facturas,
        'documentos_periodo': documentos_periodo,

        # Filtros activos para repoblar el formulario
        'periodo_activo': periodo,
        'periodo_label': periodo_label,
        'start_date': start_date,
        'end_date': end_date,
        'mes_sel': mes_sel,
        'anio_sel': anio_sel,
        'cantidad_sel': cantidad_sel,
        'unidad_sel': unidad_sel,
        'desde_sel': desde_sel,
        'hasta_sel': hasta_sel,
    }
    return render(request, 'inventario/dashboard.html', contexto)

def subir_documento(request):
    """ Vista que procesa el formulario del Modal """
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_factura')
        if archivo:
            if archivo.name.endswith('.xml') or archivo.name.endswith('.XML'):
                exito, mensaje = procesar_factura_xml(archivo, request.user)
                if exito:
                    messages.success(request, mensaje)
                else:
                    messages.error(request, mensaje)

            elif archivo.name.endswith('.pdf') or archivo.name.endswith('.PDF'):
                exito, mensaje = procesar_factura_pdf(archivo, request.user)
                if exito:
                    messages.success(request, mensaje)
                else:
                    messages.error(request, mensaje)

            else:
                messages.error(request, "Formato no válido. Por favor, suba un archivo XML o PDF.")

    referer = request.META.get('HTTP_REFERER', '')
    if '/subir/' in referer or not referer:
        return redirect('lista_facturas')

    return redirect(referer)

def lista_productos(request):
    """ Vista del inventario (CRUD Leer) """
    productos = Producto.objects.prefetch_related('detallefactura_set__factura').all().order_by('codigo')
    form = ProductoForm()

    from .models import GuiaAbastecimiento
    guias = GuiaAbastecimiento.objects.select_related('usuario').prefetch_related('detalles__producto').all().order_by('-fecha_registro')

    return render(request, 'inventario/lista_productos.html', {
        'productos': productos,
        'form': form,
        'guias': guias
    })

def lista_clientes(request):
    """ Vista del directorio de clientes (CRUD Leer) """
    clientes = Cliente.objects.all().order_by('razon_social')
    return render(request, 'inventario/lista_clientes.html', {'clientes': clientes})

def lista_facturas(request):
    """ Vista del registro histórico de facturas, guías y notas de crédito (CRUD Leer) """
    estado = request.GET.get('estado', 'PENDIENTE')

    if estado == 'TODAS':
        facturas = Factura.objects.exclude(tipo_documento__in=['GUIA DE DESPACHO', 'NOTA DE CREDITO']).select_related('cliente').prefetch_related('detalles__producto').all()
    else:
        facturas = Factura.objects.filter(estado_despacho=estado).exclude(tipo_documento__in=['GUIA DE DESPACHO', 'NOTA DE CREDITO']).select_related('cliente').prefetch_related('detalles__producto')

    facturas = facturas.order_by('-fecha_emision', '-numero')

    notas = Factura.objects.filter(tipo_documento='NOTA DE CREDITO').select_related('cliente').prefetch_related('detalles__producto').all()
    notas = notas.order_by('-fecha_emision', '-numero')

    guias = Factura.objects.filter(tipo_documento='GUIA DE DESPACHO').select_related('cliente').prefetch_related('detalles__producto').all()
    guias = guias.order_by('-fecha_emision', '-numero')

    return render(request, 'inventario/lista_facturas.html', {
        'facturas': facturas,
        'guias': guias,
        'notas': notas,
        'estado_filtro': estado
    })

def editar_producto(request, id):
    """ Vista para editar un producto existente """
    producto = get_object_or_404(Producto, id=id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            prod_instance = form.save(commit=False)
            prod_instance.usuario_modificador = request.user if request.user.is_authenticated else None
            prod_instance.motivo_modificacion = "Edición manual"
            prod_instance.save()
            form.save_m2m()
            messages.success(request, f"Producto '{producto.codigo}' actualizado correctamente.")
            return redirect('lista_productos')
        else:
            logger.warning("Errores de validación en formulario ProductoForm para '%s': %s", producto.codigo, form.errors)
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'inventario/editar_producto.html', {'form': form, 'producto': producto})

def editar_producto_masivo(request):
    """ Vista para editar en masa múltiples productos seleccionados """
    ids_raw = request.GET.get('ids', '') or request.POST.get('ids', '')
    if not ids_raw:
        messages.warning(request, "No se seleccionó ningún producto para editar en masa.")
        return redirect('lista_productos')

    ids = [int(i) for i in ids_raw.split(',') if i.strip().isdigit()]
    if not ids:
        messages.warning(request, "No se seleccionó ningún producto válido.")
        return redirect('lista_productos')

    productos = Producto.objects.filter(id__in=ids)
    if not productos.exists():
        messages.warning(request, "Los productos seleccionados no existen.")
        return redirect('lista_productos')

    fields_to_check = [
        'descripcion', 'unidad_medida',
        'cant_alternativo', 'cant_alternativo_2', 'cant_alternativo_3',
        'stock_actual', 'stock_real', 'stock_minimo', 'stock_sistema',
        'precio_venta', 'activo'
    ]

    identical_fields = {}
    blocked_fields = []

    for field in fields_to_check:
        values = {getattr(p, field) for p in productos}
        if len(values) == 1:
            identical_fields[field] = values.pop()
        else:
            blocked_fields.append(field)
            identical_fields[field] = None

    if request.method == 'POST':
        updated_fields = {}
        for field in fields_to_check:
            if field not in blocked_fields:
                if field == 'activo':
                    updated_fields[field] = 'activo' in request.POST
                else:
                    raw_val = request.POST.get(field)
                    if raw_val is not None:
                        raw_val = raw_val.strip()
                        if field in ['cant_alternativo', 'cant_alternativo_2', 'cant_alternativo_3', 'stock_actual', 'stock_real', 'stock_minimo', 'stock_sistema']:
                            updated_fields[field] = int(raw_val) if raw_val.isdigit() else 0
                        elif field == 'precio_venta':
                            try:
                                updated_fields[field] = float(raw_val)
                            except ValueError:
                                updated_fields[field] = 0.0
                        else:
                            updated_fields[field] = raw_val

        with transaction.atomic():
            for p in productos:
                for field, val in updated_fields.items():
                    setattr(p, field, val)
                p.usuario_modificador = request.user if request.user.is_authenticated else None
                p.motivo_modificacion = "Edición masiva"
                p.save()

        messages.success(request, f"Se actualizaron {productos.count()} productos correctamente en masa.")
        return redirect('lista_productos')

    contexto = {
        'productos': productos,
        'ids_raw': ids_raw,
        'identical_fields': identical_fields,
        'blocked_fields': blocked_fields,
    }
    return render(request, 'inventario/editar_producto_masivo.html', contexto)

def crear_producto(request):
    """ Vista para crear un nuevo producto """
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            prod_instance = form.save(commit=False)
            prod_instance.usuario_modificador = request.user if request.user.is_authenticated else None
            prod_instance.motivo_modificacion = "Creación de producto"
            prod_instance.save()
            form.save_m2m()
            messages.success(request, f"Producto '{prod_instance.codigo}' creado correctamente.")
            return redirect('lista_productos')
    else:
        form = ProductoForm()

    return render(request, 'inventario/editar_producto.html', {'form': form, 'producto': None})

def eliminar_producto(request, id):
    """ Vista para eliminar un producto """
    producto = get_object_or_404(Producto, id=id)
    if request.method == 'POST':
        try:
            producto.delete()
            messages.success(request, f"Producto '{producto.descripcion}' eliminado.")
        except ProtectedError:
            messages.error(request, f"No puedes eliminar '{producto.descripcion}' porque está asociado a una o más facturas.")

    return redirect('lista_productos')

# --- CRUD CLIENTES ---
def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente '{cliente.razon_social}' actualizado.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'inventario/editar_cliente.html', {'form': form, 'cliente': cliente})

def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, f"Cliente eliminado.")
        except ProtectedError:
            messages.error(request, f"No puedes eliminar a '{cliente.razon_social}' porque tiene facturas emitidas en el sistema.")
    return redirect('lista_clientes')

# --- CRUD FACTURAS ---
def editar_factura(request, id):
    factura = get_object_or_404(Factura, id=id)
    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        if form.is_valid():
            form.save()
            messages.success(request, f"Factura {factura.numero} actualizada.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm(instance=factura)
    return render(request, 'inventario/editar_factura.html', {'form': form, 'factura': factura})

def eliminar_factura(request, id):
    factura = get_object_or_404(Factura, id=id)
    if request.method == 'POST':
        numero = factura.numero
        tipo_documento = factura.tipo_documento
        detalles = list(factura.detalles.all())

        with transaction.atomic():
            factura.delete()

            for detalle in detalles:
                producto = detalle.producto
                if not DetalleFactura.objects.filter(producto=producto).exists():
                    producto.delete()

        tipo_lbl = "Nota de Crédito" if tipo_documento == "NOTA DE CREDITO" else ("Guía de Despacho" if tipo_documento == "GUIA DE DESPACHO" else "Factura")
        messages.success(request, f"La {tipo_lbl} {numero} y sus productos exclusivos fueron eliminados. El stock fue ajustado correspondientemente.")
    return redirect('lista_facturas')

def ver_factura(request, id):
    """ Vista para ver detalles de una factura (para modal) """
    factura = get_object_or_404(Factura, id=id)
    detalles = factura.detalles.all()
    contexto = {
        'factura': factura,
        'detalles': detalles,
    }
    return render(request, 'inventario/modal_factura.html', contexto)

def ver_guia_despacho(request, id):
    """ Vista para visualizar o imprimir la Guía de Despacho """
    despacho = get_object_or_404(Despacho, id=id)
    factura = despacho.factura
    detalles = factura.detalles.all()
    contexto = {
        'despacho': despacho,
        'factura': factura,
        'detalles': detalles,
    }
    return render(request, 'inventario/guia_despacho.html', contexto)

def facturas_cliente(request, id):
    """ Vista para ver facturas pendientes de despacho de un cliente específico """
    cliente = get_object_or_404(Cliente, id=id)
    facturas = cliente.facturas.filter(estado_despacho='PENDIENTE').exclude(tipo_documento__in=['GUIA DE DESPACHO', 'NOTA DE CREDITO']).order_by('-fecha_emision')
    contexto = {
        'cliente': cliente,
        'facturas': facturas,
    }
    return render(request, 'inventario/facturas_cliente.html', contexto)

def preparar_despacho(request):
    buscar = request.GET.get('buscar', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    factura = None
    estado_busqueda = None
    multiple_matches = False
    matches = []

    if buscar:
        try:
            num = int(buscar)
            qs = Factura.objects.filter(numero=num).exclude(tipo_documento__in=['GUIA DE DESPACHO', 'NOTA DE CREDITO'])

            if qs.exists():
                if tipo:
                    factura_obj = qs.filter(tipo_documento=tipo).first()
                else:
                    pending_qs = qs.filter(estado_despacho='PENDIENTE')
                    if pending_qs.count() > 1:
                        multiple_matches = True
                        matches = pending_qs
                        return render(request, 'inventario/despacho.html', {
                            'buscar': buscar,
                            'multiple_matches': True,
                            'matches': matches
                        })
                    else:
                        factura_obj = pending_qs.first() or qs.first()

                if factura_obj:
                    if factura_obj.estado_despacho == 'DESPACHADO':
                        estado_busqueda = 'DESPACHADO'
                    else:
                        estado_busqueda = 'PENDIENTE'
                        factura = factura_obj
                else:
                    estado_busqueda = 'NO_ENCONTRADO'
            else:
                estado_busqueda = 'NO_ENCONTRADO'
        except ValueError:
            estado_busqueda = 'NO_ENCONTRADO'

    return render(request, 'inventario/despacho.html', {
        'factura': factura,
        'buscar': buscar,
        'tipo': tipo,
        'estado_busqueda': estado_busqueda,
        'multiple_matches': multiple_matches,
        'matches': matches
    })

def confirmar_despacho(request, id):
    """ Marca una factura o nota de crédito como despachada/procesada y descuenta o devuelve stock """
    if request.method == 'POST':
        factura = get_object_or_404(Factura, id=id)

        tipo_lbl = "Nota de crédito" if factura.tipo_documento == "NOTA DE CREDITO" else "Factura"

        if factura.estado_despacho == 'DESPACHADO':
            messages.warning(request, f"La {tipo_lbl.lower()} Nº {factura.numero} ya se encuentra procesada.")
            return redirect('despacho')

        with transaction.atomic():
            factura.estado_despacho = 'DESPACHADO'
            factura.save()

            for detalle in factura.detalles.all():
                producto = detalle.producto
                if factura.tipo_documento == 'NOTA DE CREDITO':
                    producto.stock_actual += int(detalle.cantidad)
                    producto.motivo_modificacion = f"Devolución - Nota de Crédito Nº {factura.numero}"
                else:
                    producto.stock_actual -= int(detalle.cantidad)
                    if producto.stock_actual < 0:
                        producto.stock_actual = 0
                    producto.motivo_modificacion = f"Despacho - Factura Nº {factura.numero}"
                producto.usuario_modificador = request.user if request.user.is_authenticated else None
                producto.save()

            from .models import Despacho
            usuario = request.user if request.user.is_authenticated else None
            Despacho.objects.create(
                factura=factura,
                usuario=usuario
            )

        messages.success(request, f"¡Confirmado exitosamente para {tipo_lbl} Nº {factura.numero}!")
        return redirect('despacho')
    return redirect('despacho')

def historial_despachos(request):
    """ Muestra la lista de todos los despachos realizados """
    from .models import Despacho
    despachos = Despacho.objects.select_related('factura', 'factura__cliente', 'usuario').all().order_by('-fecha_despacho')
    return render(request, 'inventario/historial_despachos.html', {'despachos': despachos})

def procesar_carpeta_compartida_automatico(user=None):
    """
    Escanea la carpeta compartida de entrada, procesa automáticamente todas las facturas
    (PDF/XML) y las mueve a la carpeta de procesados (éxito) o carpeta de errores (fallo).
    """
    from .config import get_shared_dirs
    incoming_dir, processed_dir = get_shared_dirs()

    os.makedirs(incoming_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    error_dir = incoming_dir + "_errores"

    resultados = []

    if os.path.exists(incoming_dir):
        for filename in os.listdir(incoming_dir):
            if filename.lower().endswith(('.pdf', '.xml')):
                filepath = os.path.join(incoming_dir, filename)
                if os.path.isfile(filepath):
                    filename_limpio = os.path.basename(filename)
                    exito = False
                    mensaje = ""

                    try:
                        with open(filepath, 'rb') as f:
                            archivo_django = File(f, name=filename_limpio)
                            if filename_limpio.lower().endswith('.pdf'):
                                exito, mensaje = procesar_factura_pdf(archivo_django, user)
                            elif filename_limpio.lower().endswith('.xml'):
                                exito, mensaje = procesar_factura_xml(archivo_django, user)
                            else:
                                mensaje = "Formato de archivo no soportado."
                    except Exception as e:
                        mensaje = f"Error al leer el archivo: {str(e)}"

                    if exito:
                        try:
                            _mover_archivo_seguro(filepath, os.path.join(processed_dir, filename_limpio))
                            resultados.append({
                                'nombre': filename_limpio,
                                'exito': True,
                                'mensaje': f"Factura '{filename_limpio}' importada automáticamente con éxito: {mensaje}"
                            })
                        except Exception as e:
                            resultados.append({
                                'nombre': filename_limpio,
                                'exito': True,
                                'mensaje': f"Factura '{filename_limpio}' importada, pero no se pudo mover a procesados: {str(e)}"
                            })
                    else:
                        try:
                            os.makedirs(error_dir, exist_ok=True)
                            _mover_archivo_seguro(filepath, os.path.join(error_dir, filename_limpio))

                            err_file_path = os.path.join(error_dir, filename_limpio) + ".err"
                            with open(err_file_path, 'w', encoding='utf-8') as f_err:
                                f_err.write(mensaje)

                            resultados.append({
                                'nombre': filename_limpio,
                                'exito': False,
                                'mensaje': f"Error al procesar '{filename_limpio}': {mensaje}. El archivo fue movido a la carpeta de errores."
                            })
                        except Exception as e:
                            resultados.append({
                                'nombre': filename_limpio,
                                'exito': False,
                                'mensaje': f"Error al procesar '{filename_limpio}': {mensaje}. Tampoco se pudo mover a la carpeta de errores o registrar el log de error: {str(e)}"
                            })

    return resultados

def lista_compartida(request):
    """
    Lista las facturas depositadas en la carpeta compartida que están listas para importar.
    """
    from .config import get_shared_dirs
    incoming_dir, _ = get_shared_dirs()
    os.makedirs(incoming_dir, exist_ok=True)
    error_dir = incoming_dir + "_errores"
    os.makedirs(error_dir, exist_ok=True)

    facturas_compartidas = []
    if os.path.exists(incoming_dir):
        for filename in os.listdir(incoming_dir):
            if filename.lower().endswith(('.pdf', '.xml')):
                filepath = os.path.join(incoming_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    from datetime import datetime
                    fecha_mod = datetime.fromtimestamp(stat.st_mtime)
                    facturas_compartidas.append({
                        'nombre': filename,
                        'tamano': round(stat.st_size / 1024, 2),
                        'fecha_modificacion': fecha_mod,
                        'es_pdf': filename.lower().endswith('.pdf'),
                        'es_xml': filename.lower().endswith('.xml')
                    })

    facturas_compartidas.sort(key=lambda x: x['fecha_modificacion'], reverse=True)

    facturas_erroneas = []
    if os.path.exists(error_dir):
        for filename in os.listdir(error_dir):
            if filename.lower().endswith(('.pdf', '.xml')):
                filepath = os.path.join(error_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    from datetime import datetime
                    fecha_mod = datetime.fromtimestamp(stat.st_mtime)

                    err_message = "Error desconocido de procesamiento."
                    err_file = filepath + ".err"
                    if os.path.exists(err_file):
                        try:
                            with open(err_file, 'r', encoding='utf-8') as f:
                                err_message = f.read().strip()
                        except Exception as e:
                            logger.warning("No se pudo leer el archivo de error .err '%s': %s", err_file, e)

                    facturas_erroneas.append({
                        'nombre': filename,
                        'tamano': round(stat.st_size / 1024, 2),
                        'fecha_modificacion': fecha_mod,
                        'es_pdf': filename.lower().endswith('.pdf'),
                        'es_xml': filename.lower().endswith('.xml'),
                        'error_mensaje': err_message
                    })

    facturas_erroneas.sort(key=lambda x: x['fecha_modificacion'], reverse=True)

    return render(request, 'inventario/lista_compartida.html', {
        'facturas_compartidas': facturas_compartidas,
        'facturas_erroneas': facturas_erroneas
    })


@require_POST
def importar_factura_compartida(request):
    """
    Importa una factura desde la carpeta compartida tras la confirmación del administrador.
    """
    from django.http import JsonResponse
    filename = request.POST.get('filename')
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', '')

    if not filename:
        if is_ajax:
            return JsonResponse({'exito': False, 'mensaje': "Nombre de archivo no especificado."})
        messages.error(request, "Nombre de archivo no especificado.")
        return redirect('lista_compartida')

    filename_limpio = os.path.basename(filename)
    from .config import get_shared_dirs
    incoming_dir, processed_dir = get_shared_dirs()

    filepath = os.path.join(incoming_dir, filename_limpio)

    if not os.path.exists(filepath):
        msg = f"El archivo '{filename_limpio}' no existe en la carpeta compartida."
        if is_ajax:
            return JsonResponse({'exito': False, 'mensaje': msg})
        messages.error(request, msg)
        return redirect('lista_compartida')

    exito = False
    mensaje = ""

    try:
        with open(filepath, 'rb') as f:
            archivo_django = File(f, name=filename_limpio)

            if filename_limpio.lower().endswith('.pdf'):
                exito, mensaje = procesar_factura_pdf(archivo_django, request.user)
            elif filename_limpio.lower().endswith('.xml'):
                exito, mensaje = procesar_factura_xml(archivo_django, request.user)
            else:
                mensaje = "Formato de archivo no soportado."

    except Exception as e:
        mensaje = f"Error de lectura del archivo: {str(e)}"

    if exito:
        try:
            os.makedirs(processed_dir, exist_ok=True)
            _mover_archivo_seguro(filepath, os.path.join(processed_dir, filename_limpio))
            msg = f"Importado con éxito: {mensaje}"
            if is_ajax:
                return JsonResponse({'exito': True, 'mensaje': msg})
            messages.success(request, msg)
        except Exception as e:
            msg = f"Factura importada pero no se pudo mover el archivo: {str(e)}"
            if is_ajax:
                return JsonResponse({'exito': True, 'mensaje': msg})
            messages.warning(request, msg)
    else:
        error_dir = incoming_dir + "_errores"
        try:
            os.makedirs(error_dir, exist_ok=True)
            _mover_archivo_seguro(filepath, os.path.join(error_dir, filename_limpio))
            msg = f"Error al procesar '{filename_limpio}': {mensaje}. El archivo fue movido a errores."
        except Exception as e:
            msg = f"Error al procesar '{filename_limpio}': {mensaje}. Tampoco se pudo mover a errores: {str(e)}"

        if is_ajax:
            return JsonResponse({'exito': False, 'mensaje': msg})
        messages.error(request, msg)

    return redirect('lista_compartida')

@require_POST
def eliminar_factura_compartida(request):
    """
    Elimina físicamente una factura de la carpeta compartida.
    """
    from django.http import JsonResponse
    filename = request.POST.get('filename')
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', '')

    if not filename:
        if is_ajax:
            return JsonResponse({'exito': False, 'mensaje': "Nombre de archivo no especificado."})
        messages.error(request, "Nombre de archivo no especificado.")
        return redirect('lista_compartida')

    filename_limpio = os.path.basename(filename)
    from .config import get_shared_dirs
    incoming_dir, _ = get_shared_dirs()
    error_dir = incoming_dir + "_errores"

    filepath = os.path.join(incoming_dir, filename_limpio)
    filepath_err = os.path.join(error_dir, filename_limpio)
    filepath_err_txt = filepath_err + ".err"

    deleted = False

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            deleted = True
        except Exception as e:
            msg = f"No se pudo eliminar el archivo: {str(e)}"
            if is_ajax:
                return JsonResponse({'exito': False, 'mensaje': msg})
            messages.error(request, msg)
            return redirect('lista_compartida')

    if os.path.exists(filepath_err):
        try:
            os.remove(filepath_err)
            if os.path.exists(filepath_err_txt):
                os.remove(filepath_err_txt)
            deleted = True
        except Exception as e:
            msg = f"No se pudo eliminar el archivo de error: {str(e)}"
            if is_ajax:
                return JsonResponse({'exito': False, 'mensaje': msg})
            messages.error(request, msg)
            return redirect('lista_compartida')

    if deleted:
        msg = f"El archivo '{filename_limpio}' fue eliminado del buzón."
        if is_ajax:
            return JsonResponse({'exito': True, 'mensaje': msg})
        messages.success(request, msg)
    else:
        msg = f"El archivo '{filename_limpio}' no existe en el buzón."
        if is_ajax:
            return JsonResponse({'exito': False, 'mensaje': msg})
        messages.error(request, msg)

    return redirect('lista_compartida')

def guardar_configuracion(request):
    """
    Guarda la configuración de las rutas de las carpetas compartidas.
    """
    if request.method == 'POST':
        incoming = request.POST.get('incoming', '').strip()
        processed = request.POST.get('processed', '').strip()

        if not incoming or not processed:
            messages.error(request, "Ambas rutas son requeridas.")
        else:
            if not os.path.exists(incoming):
                messages.error(request, f"La carpeta de Entrada no existe: {incoming}")
            elif not os.path.isdir(incoming):
                messages.error(request, f"La ruta de Entrada no es una carpeta: {incoming}")
            elif not os.path.exists(processed):
                messages.error(request, f"La carpeta de Procesados no existe: {processed}")
            elif not os.path.isdir(processed):
                messages.error(request, f"La ruta de Procesados no es una carpeta: {processed}")
            else:
                try:
                    from .config import set_shared_dirs
                    set_shared_dirs(incoming, processed)
                    messages.success(request, "Configuración de carpetas guardada correctamente.")
                except Exception as e:
                    messages.error(request, f"Error al guardar configuración: {str(e)}")

    referer = request.META.get('HTTP_REFERER', '')
    if not referer or '/configurar/' in referer:
        return redirect('lista_compartida')
    return redirect(referer)

def api_producto_por_codigo(request):
    """
    API endpoint para buscar un producto por cualquiera de sus 4 códigos.
    """
    from django.http import JsonResponse
    from django.db.models import Q

    codigo_escaneado = request.GET.get('codigo', '').strip()

    if not codigo_escaneado:
        return JsonResponse({'error': 'Código requerido'}, status=400)

    producto = Producto.objects.filter(
        Q(codigo=codigo_escaneado) |
        Q(codigo_alternativo=codigo_escaneado) |
        Q(codigo_alternativo_2=codigo_escaneado) |
        Q(codigo_alternativo_3=codigo_escaneado),
        activo=True
    ).first()

    if not producto:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    multiplicador = 1
    if codigo_escaneado == producto.codigo_alternativo:
        multiplicador = producto.cant_alternativo
    elif codigo_escaneado == producto.codigo_alternativo_2:
        multiplicador = producto.cant_alternativo_2
    elif codigo_escaneado == producto.codigo_alternativo_3:
        multiplicador = producto.cant_alternativo_3

    return JsonResponse({
        'id': producto.id,
        'codigo': producto.codigo,
        'codigo_alternativo': producto.codigo_alternativo or '',
        'codigo_alternativo_2': producto.codigo_alternativo_2 or '',
        'codigo_alternativo_3': producto.codigo_alternativo_3 or '',
        'descripcion': producto.descripcion,
        'multiplicador': multiplicador,
        'unidad_medida': producto.unidad_medida
    })

def compartida_api_status(request):
    """
    Endpoint JSON que devuelve la cantidad y metadatos de los archivos en la carpeta compartida.
    Procesa automáticamente los archivos encontrados si se detectan.
    """
    from django.http import JsonResponse
    from .config import get_shared_dirs
    from datetime import datetime

    user = request.user if request.user.is_authenticated else None
    resultados_automaticos = procesar_carpeta_compartida_automatico(user)

    incoming_dir, _ = get_shared_dirs()

    archivos_raw = []
    if incoming_dir and os.path.exists(incoming_dir):
        try:
            for filename in os.listdir(incoming_dir):
                if filename.lower().endswith(('.pdf', '.xml')):
                    filepath = os.path.join(incoming_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        archivos_raw.append((filename, stat.st_size, stat.st_mtime))
        except Exception as e:
            logger.error("Error al listar archivos pendientes en la carpeta compartida: %s", e)

    archivos_raw.sort(key=lambda x: x[2], reverse=True)

    facturas_compartidas = []
    for filename, size, mtime in archivos_raw:
        fecha_mod = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        facturas_compartidas.append({
            'nombre': filename,
            'tamano': round(size / 1024, 2),
            'fecha_modificacion': fecha_mod,
            'es_pdf': filename.lower().endswith('.pdf'),
            'es_xml': filename.lower().endswith('.xml')
        })

    # Listar facturas con errores
    error_dir = incoming_dir + "_errores"
    archivos_err_raw = []
    if os.path.exists(error_dir):
        try:
            for filename in os.listdir(error_dir):
                if filename.lower().endswith(('.pdf', '.xml')):
                    filepath = os.path.join(error_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        archivos_err_raw.append((filename, stat.st_size, stat.st_mtime))
        except Exception as e:
            logger.error("Error al listar archivos con errores en la carpeta compartida: %s", e)

    archivos_err_raw.sort(key=lambda x: x[2], reverse=True)

    facturas_erroneas = []
    for filename, size, mtime in archivos_err_raw:
        fecha_mod = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")

        err_message = "Error desconocido de procesamiento."
        err_file = os.path.join(error_dir, filename) + ".err"
        if os.path.exists(err_file):
            try:
                with open(err_file, 'r', encoding='utf-8') as f:
                    err_message = f.read().strip()
            except Exception as e:
                logger.warning("No se pudo leer el archivo de error '%s': %s", err_file, e)

        facturas_erroneas.append({
            'nombre': filename,
            'tamano': round(size / 1024, 2),
            'fecha_modificacion': fecha_mod,
            'es_pdf': filename.lower().endswith('.pdf'),
            'es_xml': filename.lower().endswith('.xml'),
            'error_mensaje': err_message
        })

    from django.utils import timezone
    since_str = request.GET.get('since')
    notificaciones = []
    server_now = timezone.now()

    if since_str:
        try:
            since_str = since_str.replace(' ', '+')
            if since_str.endswith('Z'):
                since_str = since_str[:-1] + '+00:00'
            since_dt = datetime.fromisoformat(since_str)

            nuevas_facturas = Factura.objects.filter(fecha_subida__gt=since_dt)
            for fact in nuevas_facturas:
                nombre_doc = "Factura"
                if fact.tipo_documento == "GUIA DE DESPACHO":
                    nombre_doc = "Guía de despacho"
                elif fact.tipo_documento == "NOTA DE CREDITO":
                    nombre_doc = "Nota de crédito"

                notificaciones.append({
                    'tipo': 'success',
                    'mensaje': f'¡Novedad! {nombre_doc} Nº {fact.numero} de "{fact.cliente.razon_social}" ingresada con éxito.'
                })

            if os.path.exists(error_dir):
                for filename in os.listdir(error_dir):
                    if filename.lower().endswith(('.pdf', '.xml')):
                        filepath = os.path.join(error_dir, filename)
                        if os.path.isfile(filepath):
                            mtime = os.path.getmtime(filepath)
                            mtime_dt = timezone.make_aware(datetime.fromtimestamp(mtime))
                            if mtime_dt > since_dt:
                                err_message = "Error desconocido de procesamiento."
                                err_file = filepath + ".err"
                                if os.path.exists(err_file):
                                    try:
                                        with open(err_file, 'r', encoding='utf-8') as f:
                                            err_message = f.read().strip()
                                    except Exception as e:
                                        logger.warning("No se pudo leer el archivo de error '%s' en filtro de fecha: %s", err_file, e)
                                notificaciones.append({
                                    'tipo': 'error',
                                    'mensaje': f'Fallo al procesar "{filename}": {err_message}'
                                })
        except Exception as ex:
            logger.error("Error filtrando novedades desde fecha %s: %s", since_str, ex)

    return JsonResponse({
        'cant_compartidas': len(facturas_compartidas),
        'facturas_compartidas': facturas_compartidas,
        'facturas_erroneas': facturas_erroneas,
        'resultados_automaticos': resultados_automaticos,
        'notificaciones_tiempo_real': notificaciones,
        'server_time': server_now.isoformat()
    })

def login_temporal(request):
    """
    Vista temporal para evitar el 404 de login.
    Redirige automáticamente al parámetro 'next' o al dashboard.
    """
    next_url = request.GET.get('next', '/')
    return redirect(next_url)


@require_POST
def subir_a_compartida(request):
    """
    Recibe un archivo subido vía AJAX, lo almacena físicamente y lo procesa de inmediato.
    """
    from django.http import JsonResponse
    from django.core.files.base import File
    import shutil
    from .utils import procesar_factura_pdf, procesar_factura_xml

    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'exito': False, 'mensaje': 'No se recibió ningún archivo.'})

    nombre_archivo = os.path.basename(archivo.name)
    if not (nombre_archivo.lower().endswith('.pdf') or nombre_archivo.lower().endswith('.xml')):
        return JsonResponse({'exito': False, 'mensaje': 'Formato de archivo no soportado. Solo se permiten archivos PDF o XML.'})

    from .config import get_shared_dirs
    incoming_dir, processed_dir = get_shared_dirs()
    os.makedirs(incoming_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    error_dir = incoming_dir + "_errores"
    os.makedirs(error_dir, exist_ok=True)

    filepath = os.path.join(incoming_dir, nombre_archivo)

    try:
        with open(filepath, 'wb+') as destination:
            for chunk in archivo.chunks():
                destination.write(chunk)

        user = request.user if request.user.is_authenticated else None
        exito = False
        mensaje = ""

        with open(filepath, 'rb') as f:
            archivo_django = File(f, name=nombre_archivo)
            if nombre_archivo.lower().endswith('.pdf'):
                exito, mensaje = procesar_factura_pdf(archivo_django, user)
            elif nombre_archivo.lower().endswith('.xml'):
                exito, mensaje = procesar_factura_xml(archivo_django, user)

        if exito:
            _mover_archivo_seguro(filepath, os.path.join(processed_dir, nombre_archivo))
            return JsonResponse({'exito': True, 'mensaje': f'Archivo "{nombre_archivo}" importado y clasificado con éxito: {mensaje}'})
        else:
            _mover_archivo_seguro(filepath, os.path.join(error_dir, nombre_archivo))
            err_file_path = os.path.join(error_dir, nombre_archivo) + ".err"
            with open(err_file_path, 'w', encoding='utf-8') as f_err:
                f_err.write(mensaje)
            return JsonResponse({'exito': False, 'mensaje': f'Error al procesar "{nombre_archivo}": {mensaje}'})

    except Exception as e:
        logger.error("Error crítico en subir_a_compartida para '%s': %s", nombre_archivo, e)
        if os.path.exists(filepath):
            try:
                _mover_archivo_seguro(filepath, os.path.join(error_dir, nombre_archivo))
                err_file_path = os.path.join(error_dir, nombre_archivo) + ".err"
                with open(err_file_path, 'w', encoding='utf-8') as f_err:
                    f_err.write(str(e))
            except Exception as ex:
                logger.error("No se pudo mover el archivo con error o escribir el log .err en subir_a_compartida: %s", ex)
        return JsonResponse({'exito': False, 'mensaje': f'Error crítico al procesar en el servidor: {str(e)}'})


@require_POST
def analizar_guia_abastecimiento(request):
    """
    Recibe el archivo de la guía, lo parsea y busca coincidencias de productos en la base de datos.
    """
    from django.http import JsonResponse
    from django.db.models import Q
    from .utils import parsear_guia_abastecimiento

    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'exito': False, 'mensaje': 'No se recibió ningún archivo.'}, status=400)

    try:
        folio, items = parsear_guia_abastecimiento(archivo)
    except Exception as e:
        return JsonResponse({'exito': False, 'mensaje': f'Error al procesar el archivo: {str(e)}'}, status=400)

    if folio is not None:
        from .models import GuiaAbastecimiento
        if GuiaAbastecimiento.objects.filter(numero=folio).exists():
            return JsonResponse({
                'exito': False,
                'folio_duplicado': True,
                'folio': folio,
                'mensaje': f'La guía con Folio {folio} ya fue ingresada al sistema.'
            })

    items_procesados = []
    for item in items:
        codigo = item['codigo']
        producto = Producto.objects.filter(
            Q(codigo=codigo) |
            Q(codigo_alternativo=codigo) |
            Q(codigo_alternativo_2=codigo) |
            Q(codigo_alternativo_3=codigo)
        ).first()

        items_procesados.append({
            'codigo_origen': codigo,
            'descripcion_origen': item['descripcion'],
            'cantidad': item['cantidad'],
            'producto_id': producto.id if producto else None,
            'producto_codigo': producto.codigo if producto else None,
            'producto_descripcion': producto.descripcion if producto else None,
        })

    return JsonResponse({
        'exito': True,
        'folio': folio,
        'items': items_procesados
    })


@require_POST
def procesar_guia_abastecimiento(request):
    """
    Recibe la confirmación final de la guía (folio e ítems) y actualiza el stock de los productos.
    """
    from django.http import JsonResponse
    import json
    from .models import GuiaAbastecimiento, DetalleGuiaAbastecimiento

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'exito': False, 'mensaje': 'Datos JSON no válidos.'}, status=400)

    folio_raw = data.get('folio')
    items = data.get('items', [])

    if not folio_raw:
        return JsonResponse({'exito': False, 'mensaje': 'El número de Folio es requerido.'}, status=400)

    try:
        folio = int(folio_raw)
    except ValueError:
        return JsonResponse({'exito': False, 'mensaje': 'El número de Folio debe ser un valor entero válido.'}, status=400)

    if GuiaAbastecimiento.objects.filter(numero=folio).exists():
        return JsonResponse({'exito': False, 'mensaje': f'La guía con Folio {folio} ya fue ingresada al sistema.'}, status=400)

    if not items:
        return JsonResponse({'exito': False, 'mensaje': 'Debe ingresar al menos un producto.'}, status=400)

    for item in items:
        p_id = item.get('producto_id')
        qty = item.get('cantidad')
        if not p_id:
            return JsonResponse({'exito': False, 'mensaje': f'El ítem "{item.get("descripcion_origen")}" no tiene un producto asociado.'}, status=400)
        try:
            qty_val = int(qty)
            if qty_val <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return JsonResponse({'exito': False, 'mensaje': f'La cantidad para el producto ID {p_id} debe ser un entero positivo.'}, status=400)

    try:
        with transaction.atomic():
            guia = GuiaAbastecimiento.objects.create(
                numero=folio,
                usuario=request.user if request.user.is_authenticated else None
            )
            for item in items:
                producto = Producto.objects.select_for_update().get(id=int(item['producto_id']))
                cantidad = int(item['cantidad'])

                producto.stock_actual = (producto.stock_actual or 0) + cantidad
                producto.usuario_modificador = request.user if request.user.is_authenticated else None
                producto.motivo_modificacion = f"Guía de Abastecimiento Nº {folio}"
                producto.save()

                DetalleGuiaAbastecimiento.objects.create(
                    guia=guia,
                    producto=producto,
                    cantidad=cantidad
                )
    except Producto.DoesNotExist:
        return JsonResponse({'exito': False, 'mensaje': 'Uno de los productos seleccionados no existe en el catálogo.'}, status=400)
    except Exception as e:
        return JsonResponse({'exito': False, 'mensaje': f'Error en base de datos: {str(e)}'}, status=500)

    return JsonResponse({'exito': True, 'mensaje': f'Guía Nº {folio} ingresada con éxito y stock actualizado.'})


@require_POST
def analizar_importar_excel(request):
    """
    Recibe el archivo Excel, extrae las columnas y genera una vista previa.
    """
    from django.http import JsonResponse

    archivo = request.FILES.get('archivo')
    if not archivo:
        return JsonResponse({'exito': False, 'mensaje': 'No se recibió ningún archivo.'}, status=400)

    try:
        import pandas as pd
        df = pd.read_excel(archivo, nrows=5)

        archivo.seek(0)
        df_full = pd.read_excel(archivo)
        total_filas = len(df_full)

        columnas = [str(c).strip() for c in df.columns if pd.notna(c)]

        import math
        vista_previa_raw = df.to_dict(orient='records')
        vista_previa = []
        for row in vista_previa_raw:
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    cleaned_row[k] = None
                elif pd.isna(v):
                    cleaned_row[k] = None
                else:
                    cleaned_row[k] = v
            vista_previa.append(cleaned_row)

        return JsonResponse({
            'exito': True,
            'columnas': columnas,
            'vista_previa': vista_previa,
            'total_filas': total_filas
        })
    except ModuleNotFoundError as e:
        return JsonResponse({
            'exito': False,
            'mensaje': f'Falta una librería requerida ({str(e)}). Por favor, asegúrate de activar el entorno virtual.'
        }, status=500)
    except Exception as e:
        return JsonResponse({'exito': False, 'mensaje': f'Error al leer el archivo Excel: {str(e)}'}, status=400)


@require_POST
def procesar_importar_excel(request):
    """
    Procesa el archivo Excel completo y actualiza el inventario en base al mapeo de columnas provisto.
    """
    from django.http import JsonResponse
    from django.db import transaction
    from django.db.models import Q
    from .models import Producto

    archivo = request.FILES.get('archivo')
    col_codigo = request.POST.get('columna_codigo')
    col_stock_actual = request.POST.get('columna_stock_actual')
    col_stock_real = request.POST.get('columna_stock_real')
    col_stock_minimo = request.POST.get('columna_stock_minimo')
    col_stock_sistema = request.POST.get('columna_stock_sistema')
    non_numeric_option = request.POST.get('opcion_no_numericos', 'mantener')

    if not archivo:
        return JsonResponse({'exito': False, 'mensaje': 'No se recibió ningún archivo.'}, status=400)
    if not col_codigo:
        return JsonResponse({'exito': False, 'mensaje': 'La columna para el Código de Producto es obligatoria.'}, status=400)

    try:
        import pandas as pd
        df = pd.read_excel(archivo)
    except ModuleNotFoundError as e:
        return JsonResponse({
            'exito': False,
            'mensaje': f'Falta una librería requerida ({str(e)}). Por favor, asegúrate de activar el entorno virtual.'
        }, status=500)
    except Exception as e:
        return JsonResponse({'exito': False, 'mensaje': f'Error al leer el archivo Excel: {str(e)}'}, status=400)

    if col_codigo not in df.columns:
        return JsonResponse({'exito': False, 'mensaje': f'La columna de códigos "{col_codigo}" no se encuentra en el archivo.'}, status=400)

    actualizados = 0
    omitidos = 0
    codigos_no_encontrados = []

    try:
        def limpiar_codigo(val):
            if pd.isna(val):
                return ""
            val_str = str(val).strip().lower()
            if val_str.endswith('.0'):
                return val_str[:-2]
            return val_str

        productos = Producto.objects.all()
        productos_por_codigo = {}
        for p in productos:
            if p.codigo:
                productos_por_codigo[limpiar_codigo(p.codigo)] = p
            if p.codigo_alternativo:
                productos_por_codigo[limpiar_codigo(p.codigo_alternativo)] = p
            if p.codigo_alternativo_2:
                productos_por_codigo[limpiar_codigo(p.codigo_alternativo_2)] = p
            if p.codigo_alternativo_3:
                productos_por_codigo[limpiar_codigo(p.codigo_alternativo_3)] = p

        productos_a_actualizar = set()
        historial_por_producto = {}

        for index, row in df.iterrows():
            codigo_val = row.get(col_codigo)
            if pd.isna(codigo_val):
                continue

            codigo_limpio = limpiar_codigo(codigo_val)
            if not codigo_limpio:
                continue

            producto = productos_por_codigo.get(codigo_limpio)

            if producto:
                stock_actual_ant = producto.stock_actual
                stock_real_ant = producto.stock_real
                stock_minimo_ant = producto.stock_minimo
                stock_sistema_ant = producto.stock_sistema
                updated = False

                if col_stock_actual and col_stock_actual in df.columns:
                    val = row.get(col_stock_actual)
                    if pd.notna(val):
                        try:
                            producto.stock_actual = int(round(float(val)))
                            updated = True
                        except (ValueError, TypeError):
                            if non_numeric_option == 'cero':
                                producto.stock_actual = 0
                                updated = True
                    else:
                        if non_numeric_option == 'cero':
                            producto.stock_actual = 0
                            updated = True

                if col_stock_real and col_stock_real in df.columns:
                    val = row.get(col_stock_real)
                    if pd.notna(val):
                        try:
                            producto.stock_real = int(round(float(val)))
                            updated = True
                        except (ValueError, TypeError):
                            if non_numeric_option == 'cero':
                                producto.stock_real = 0
                                updated = True
                    else:
                        if non_numeric_option == 'cero':
                            producto.stock_real = 0
                            updated = True

                if col_stock_minimo and col_stock_minimo in df.columns:
                    val = row.get(col_stock_minimo)
                    if pd.notna(val):
                        try:
                            producto.stock_minimo = int(round(float(val)))
                            updated = True
                        except (ValueError, TypeError):
                            if non_numeric_option == 'cero':
                                producto.stock_minimo = 0
                                updated = True
                    else:
                        if non_numeric_option == 'cero':
                            producto.stock_minimo = 0
                            updated = True

                if col_stock_sistema and col_stock_sistema in df.columns:
                    val = row.get(col_stock_sistema)
                    if pd.notna(val):
                        try:
                            producto.stock_sistema = int(round(float(val)))
                            updated = True
                        except (ValueError, TypeError):
                            if non_numeric_option == 'cero':
                                producto.stock_sistema = 0
                                updated = True
                    else:
                        if non_numeric_option == 'cero':
                            producto.stock_sistema = 0
                            updated = True

                if updated:
                    if (producto.stock_actual != stock_actual_ant or
                        producto.stock_real != stock_real_ant or
                        producto.stock_minimo != stock_minimo_ant or
                        producto.stock_sistema != stock_sistema_ant):

                        productos_a_actualizar.add(producto)
                        actualizados += 1

                        if stock_actual_ant != producto.stock_actual or stock_real_ant != producto.stock_real:
                            hist_data = historial_por_producto.get(producto.id)
                            if hist_data:
                                hist_data['stock_actual_nuevo'] = producto.stock_actual
                                hist_data['stock_real_nuevo'] = producto.stock_real
                            else:
                                historial_por_producto[producto.id] = {
                                    'producto': producto,
                                    'stock_actual_anterior': stock_actual_ant,
                                    'stock_actual_nuevo': producto.stock_actual,
                                    'stock_real_anterior': stock_real_ant,
                                    'stock_real_nuevo': producto.stock_real
                                }
            else:
                raw_codigo_str = str(codigo_val).strip()
                if raw_codigo_str not in codigos_no_encontrados:
                    codigos_no_encontrados.append(raw_codigo_str)
                omitidos += 1

        if productos_a_actualizar:
            fields_to_update = []
            if col_stock_actual:
                fields_to_update.append('stock_actual')
            if col_stock_real:
                fields_to_update.append('stock_real')
            if col_stock_minimo:
                fields_to_update.append('stock_minimo')
            if col_stock_sistema:
                fields_to_update.append('stock_sistema')

            with transaction.atomic():
                Producto.objects.bulk_update(list(productos_a_actualizar), fields_to_update)

                from .models import HistorialStock
                hist_objects = [
                    HistorialStock(
                        producto=h['producto'],
                        stock_actual_anterior=h['stock_actual_anterior'],
                        stock_actual_nuevo=h['stock_actual_nuevo'],
                        stock_real_anterior=h['stock_real_anterior'],
                        stock_real_nuevo=h['stock_real_nuevo'],
                        detalle="Importación Excel",
                        usuario=request.user if request.user.is_authenticated else None
                    )
                    for h in historial_por_producto.values()
                ]
                if hist_objects:
                    HistorialStock.objects.bulk_create(hist_objects)

    except Exception as e:
        return JsonResponse({'exito': False, 'mensaje': f'Error al procesar la base de datos: {str(e)}'}, status=500)

    return JsonResponse({
        'exito': True,
        'mensaje': f'Importación completada. Se actualizaron {actualizados} productos.',
        'actualizados': actualizados,
        'omitidos': omitidos,
        'codigos_no_encontrados': codigos_no_encontrados
    })

def stock_vendedores(request):
    """ Vista simplificada de stock para vendedores """
    productos = Producto.objects.all().order_by('codigo')
    return render(request, 'inventario/stock_vendedores.html', {'productos': productos})


# =============================================================================
# DEMO RESET API — Restauración de datos demo vía JavaScript
# =============================================================================

@require_POST
def api_demo_reset(request):
    """
    Endpoint API para restaurar todos los datos de demostración.
    Diseñado para ser invocado desde JavaScript (AJAX) sin necesidad de
    ejecutar un management command de Python.

    Elimina todos los datos existentes y carga la fixture demo_seed.json.
    """
    from django.http import JsonResponse
    from django.core.management import call_command
    from .models import (
        Factura, DetalleFactura, Despacho, Cliente, Producto,
        GuiaAbastecimiento, DetalleGuiaAbastecimiento, HistorialStock,
        Sucursal, Bodega
    )

    try:
        with transaction.atomic():
            # 1. Eliminar todos los datos en orden de dependencia
            DetalleGuiaAbastecimiento.objects.all().delete()
            GuiaAbastecimiento.objects.all().delete()
            HistorialStock.objects.all().delete()
            Despacho.objects.all().delete()
            DetalleFactura.objects.all().delete()
            Factura.objects.all().delete()
            Producto.objects.all().delete()
            Cliente.objects.all().delete()
            Bodega.objects.all().delete()
            Sucursal.objects.all().delete()

            # 2. Cargar fixture de datos demo
            call_command('loaddata', 'demo_seed.json', verbosity=0)

        return JsonResponse({
            'exito': True,
            'mensaje': '¡Datos de demostración restaurados con éxito! La página se recargará automáticamente.'
        })

    except Exception as e:
        logger.error("Error al restaurar datos demo: %s", e)
        return JsonResponse({
            'exito': False,
            'mensaje': f'Error al restaurar datos de demostración: {str(e)}'
        }, status=500)
