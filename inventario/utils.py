import io
import os
import re
import logging
import xml.etree.ElementTree as ET

import pdfplumber
from django.db import transaction
from decimal import Decimal
from .models import Cliente, Producto, Factura, DetalleFactura

logger = logging.getLogger(__name__)

def calcular_dv(rut_sin_dv):
    """
    Recibe un RUT (entero o string) sin DV ni guion.
    Retorna el dígito verificador ('0'-'9' o 'K').
    """
    rut_str = str(rut_sin_dv).replace(".", "").replace("-", "")
    rut_reverso = rut_str[::-1]
    multiplicador = 2
    suma = 0

    for digito in rut_reverso:
        suma += int(digito) * multiplicador
        multiplicador += 1
        if multiplicador == 8:
            multiplicador = 2

    resto = suma % 11
    dv = 11 - resto

    if dv == 11:
        return '0'
    elif dv == 10:
        return 'K'
    else:
        return str(dv)

def limpiar_namespaces(root):
    """ El XML del SII trae 'namespaces' que complican la lectura. Esta función los elimina para facilitar la búsqueda. """
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return root

def _extraer_xml_desde_texto_pdf(texto):
    """Intenta encontrar un XML DTE embebido en el texto del PDF."""
    if not texto:
        return None
    match = re.search(r"<DTE[\s\S]*?</DTE>", texto)
    return match.group(0) if match else None

def procesar_factura_pdf(archivo, usuario):
    """Lee un PDF e intenta extraer los datos ya sea del XML DTE o escaneando el texto impreso."""
    try:
        archivo.seek(0)
        with pdfplumber.open(archivo) as pdf:
            texto_paginas = []
            for page in pdf.pages:
                texto_paginas.append(page.extract_text() or "")
        texto = "\n".join(texto_paginas)

        # 1. Intentar compatibilidad antigua (XML embebido en el PDF si existe)
        xml_texto = _extraer_xml_desde_texto_pdf(texto)
        if xml_texto:
            from django.core.files.base import ContentFile
            xml_bytes = xml_texto.encode("utf-8", errors="ignore")
            archivo_xml = ContentFile(xml_bytes, name=getattr(archivo, 'name', 'factura_extraida.xml').replace('.pdf', '.xml'))
            return procesar_factura_xml(archivo_xml, usuario)

        # 2. Parsing directo a partir del texto impreso del PDF
        # Identificar Folio / Número
        numero_match = re.search(r"Nº\s*(\d+)", texto)
        if not numero_match:
            return False, "No se pudo encontrar el Folio (Número) de la factura en el texto."
        numero_factura = int(numero_match.group(1))

        tipo_documento = "FACTURA ELECTRONICA"
        texto_upper = texto.upper()
        if "GUIA DE DESPACHO" in texto_upper or "GUIA DESPACHO" in texto_upper:
            tipo_documento = "GUIA DE DESPACHO"
        elif "NOTA DE CREDITO" in texto_upper or "NOTA DE CREDITO" in texto_upper.replace("É", "E"):
            tipo_documento = "NOTA DE CREDITO"

        if Factura.objects.filter(numero=numero_factura, tipo_documento=tipo_documento).exists():
            if tipo_documento == "GUIA DE DESPACHO":
                nombre_doc = "La guía de despacho"
            elif tipo_documento == "NOTA DE CREDITO":
                nombre_doc = "La nota de crédito"
            else:
                nombre_doc = "La factura"
            return False, f"{nombre_doc} Nº {numero_factura} ya fue ingresada."

        # Identificar datos del cliente
        rut_match = re.search(r"R\.U\.T\.\s*:([\d\.\-Kk]+)", texto)
        rut_raw = rut_match.group(1).replace(".", "").strip() if rut_match else "11111111-1"

        # Extraemos la Razón Social y el Teléfono
        rs_match = re.search(r"Señor\(es\)\s*:(.*?)(?:Teléfono|Tel)\s*:\s*([\+\-\d\s]+)", texto)
        if rs_match:
            razon_social = rs_match.group(1).strip()
            telefono = rs_match.group(2).strip()
        else:
            rs_match_fallback = re.search(r"Señor\(es\)\s*:(.*?)\n", texto)
            razon_social = rs_match_fallback.group(1).strip() if rs_match_fallback else "Cliente Desconocido"
            telefono = ""

        giro_match = re.search(r"Giro\s*:(.*?)\s+(?:Forma|F\.)", texto)
        giro = giro_match.group(1).strip() if giro_match else ""

        dir_match = re.search(r"Dirección\s*:(.*?)\s+(?:Vendedor|Vend)", texto)
        direccion = dir_match.group(1).strip() if dir_match else ""

        comuna_match = re.search(r"Comuna\s*:(.*?)\s+(?:Ciudad|Ciud)", texto)
        comuna = comuna_match.group(1).strip() if comuna_match else ""

        ciu_match = re.search(r"Ciudad\s*:\s*(.*?)\n", texto)
        ciudad = ciu_match.group(1).strip() if ciu_match else ""

        # Identificar Fecha de emisión (Ej: "Santiago, 09 de abril de 2026")
        from datetime import datetime
        fecha_emision = datetime.now().strftime("%Y-%m-%d")
        fecha_match = re.search(r'(\d{2})\s+de\s+([a-z]+)\s+de\s+(\d{4})', texto, re.IGNORECASE)
        if fecha_match:
            dia, mes_str, anio = fecha_match.groups()
            map_meses = {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04', 'mayo': '05', 'junio': '06',
                         'julio': '07', 'agosto': '08', 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}
            mes = map_meses.get(mes_str.lower(), '01')
            fecha_emision = f"{anio}-{mes}-{dia}"

        with transaction.atomic():
            # Buscar o crear Cliente
            cliente, creado = Cliente.objects.get_or_create(
                rut=rut_raw,
                defaults={
                    'razon_social': razon_social,
                    'giro': giro,
                    'direccion': direccion,
                    'comuna': comuna,
                    'ciudad': ciudad,
                    'telefono': telefono
                }
            )

            # Buscar Totales
            neto_match = re.search(r"Neto:\s*\$\s*([\d\.]+)", texto)
            neto = int(neto_match.group(1).replace(".", "")) if neto_match else 0

            iva_match = re.search(r"19%\s+I\.V\.A\.:\s*\$\s*([\d\.]+)", texto)
            iva = int(iva_match.group(1).replace(".", "")) if iva_match else int(neto * 0.19)

            total_match = re.search(r"Total:\s*\$\s*([\d\.]+)", texto)
            total = int(total_match.group(1).replace(".", "")) if total_match else (neto + iva)

            usuario_valido = usuario if usuario and usuario.is_authenticated else None
            nombre_archivo = os.path.basename(archivo.name) if getattr(archivo, 'name', None) else ""

            # Crear cabecera Factura
            factura = Factura.objects.create(
                usuario_creador=usuario_valido,
                numero=numero_factura,
                tipo_documento=tipo_documento,
                fecha_emision=fecha_emision,
                cliente=cliente,
                neto=neto,
                iva=iva,
                total=total,
                archivo_origen=nombre_archivo
            )

            # Buscar y crear Detalles
            for line in texto.split("\n"):
                match_item = re.search(r"^(\d+)\s+([A-Za-z0-9\-]+)\s+(.+?)\s+(UN|KG|LT|u|m|cm|mm|lt|MT|MTS|CJ|CJA|CAJA|CAJAS|PAQ|PAR|SET|ROL|ROLLO|UNID|UNIDADES|METROS|L|LTS|G|GR)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)$", line.strip(), re.IGNORECASE)
                if match_item:
                    _, codigo_prod, descripcion, um, cant_str, precio_str, dscto_str, tot_str = match_item.groups()

                    cantidad = Decimal(cant_str.replace(".", "").replace(",", "."))
                    precio_unitario = float(precio_str.replace(".", "").replace(",", "."))
                    total_linea = int(tot_str.replace(".", ""))

                    # Buscar Producto en el maestro por código
                    try:
                        producto = Producto.objects.get(codigo=codigo_prod)
                    except Producto.DoesNotExist:
                        continue

                    # DetalleFactura
                    DetalleFactura.objects.create(
                        factura=factura,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=int(precio_unitario),
                        total_linea=total_linea
                    )

                    # Modificación automática de stock para guías de despacho y notas de crédito
                    if tipo_documento == 'GUIA DE DESPACHO':
                        producto.stock_actual -= int(cantidad)
                        if producto.stock_actual < 0:
                            producto.stock_actual = 0
                        producto.motivo_modificacion = f"Carga Automática - Guía de Despacho Nº {numero_factura}"
                        producto.usuario_modificador = usuario_valido
                        producto.save()
                    elif tipo_documento == 'NOTA DE CREDITO':
                        producto.stock_actual += int(cantidad)
                        producto.motivo_modificacion = f"Devolución Automática - Nota de Crédito Nº {numero_factura}"
                        producto.usuario_modificador = usuario_valido
                        producto.save()

            if tipo_documento in ["GUIA DE DESPACHO", "NOTA DE CREDITO"]:
                factura.estado_despacho = 'DESPACHADO'
                factura.save()

            if tipo_documento == "GUIA DE DESPACHO":
                nombre_doc = "Guía de despacho"
            elif tipo_documento == "NOTA DE CREDITO":
                nombre_doc = "Nota de crédito"
            else:
                nombre_doc = "Factura"
            return True, f"{nombre_doc} N° {numero_factura} extraída desde PDF impreso y guardada con éxito."

    except Exception as e:
        return False, f"Error al procesar el PDF: {str(e)}"

@transaction.atomic
def procesar_factura_xml(archivo, usuario):
    """ Lee el XML del SII y guarda todo en la base de datos """
    try:
        # 1. Leer el archivo XML
        tree = ET.parse(archivo)
        root = tree.getroot()
        root = limpiar_namespaces(root)

        # 2. Extraer datos del Encabezado (IdDoc)
        numero_factura = int(root.find('.//Folio').text)
        fecha_emision = root.find('.//FchEmis').text  # Formato YYYY-MM-DD

        tipo_dte_nodo = root.find('.//TipoDTE')
        tipo_dte = tipo_dte_nodo.text if tipo_dte_nodo is not None else "33"
        tipo_documento = "FACTURA ELECTRONICA"
        if tipo_dte == "52":
            tipo_documento = "GUIA DE DESPACHO"
        elif tipo_dte == "34":
            tipo_documento = "FACTURA ELECTRONICA EXENTA"
        elif tipo_dte == "61":
            tipo_documento = "NOTA DE CREDITO"

        # Verificar si la factura ya existe para no duplicar
        if Factura.objects.filter(numero=numero_factura, tipo_documento=tipo_documento).exists():
            if tipo_documento == "GUIA DE DESPACHO":
                nombre_doc = "La guía de despacho"
            elif tipo_documento == "NOTA DE CREDITO":
                nombre_doc = "La nota de crédito"
            else:
                nombre_doc = "La factura"
            return False, f"{nombre_doc} Nº {numero_factura} ya existe en el sistema."

        # 3. Extraer datos del Cliente (Receptor)
        rut_cliente = root.find('.//RUTRecep').text
        razon_social = root.find('.//RznSocRecep').text

        giro = root.find('.//GiroRecep').text if root.find('.//GiroRecep') is not None else ""
        direccion = root.find('.//DirRecep').text if root.find('.//DirRecep') is not None else ""
        comuna = root.find('.//CmnaRecep').text if root.find('.//CmnaRecep') is not None else ""
        ciudad = root.find('.//CiudadRecep').text if root.find('.//CiudadRecep') is not None else ""

        # Buscar cliente o crearlo si es nuevo
        cliente, creado = Cliente.objects.get_or_create(
            rut=rut_cliente,
            defaults={
                'razon_social': razon_social,
                'giro': giro,
                'direccion': direccion,
                'comuna': comuna,
                'ciudad': ciudad
            }
        )

        # 4. Extraer Totales
        neto = int(root.find('.//MntNeto').text)
        iva = int(root.find('.//IVA').text)
        total = int(root.find('.//MntTotal').text)

        # 5. Crear la Factura
        usuario_valido = usuario if usuario and usuario.is_authenticated else None
        nombre_archivo = os.path.basename(archivo.name) if getattr(archivo, 'name', None) else ""

        factura = Factura.objects.create(
            usuario_creador=usuario_valido,
            numero=numero_factura,
            tipo_documento=tipo_documento,
            fecha_emision=fecha_emision,
            cliente=cliente,
            neto=neto,
            iva=iva,
            total=total,
            archivo_origen=nombre_archivo
        )

        # 6. Extraer el Detalle de Productos
        detalles_xml = root.findall('.//Detalle')
        for det in detalles_xml:
            codigo_nodo = det.find('.//VlrCodigo')
            codigo_prod = codigo_nodo.text if codigo_nodo is not None else f"GEN-{det.find('.//NroLinDet').text}"

            descripcion = det.find('.//NmbItem').text

            # Cantidad y Precio
            cantidad = Decimal(det.find('.//QtyItem').text)
            precio_unitario = float(det.find('.//PrcItem').text)
            total_linea = int(det.find('.//MontoItem').text)

            um_nodo = det.find('.//UnmdItem')
            unidad_medida = um_nodo.text if um_nodo is not None else "UN"

            # Buscar Producto en el maestro por código
            try:
                producto = Producto.objects.get(codigo=codigo_prod)
            except Producto.DoesNotExist:
                continue

            # Enlazar el producto a la factura
            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=int(precio_unitario),
                total_linea=total_linea
            )

            # Modificación automática de stock para guías de despacho y notas de crédito
            if tipo_documento == 'GUIA DE DESPACHO':
                producto.stock_actual -= int(cantidad)
                if producto.stock_actual < 0:
                    producto.stock_actual = 0
                producto.motivo_modificacion = f"Carga Automática - Guía de Despacho Nº {numero_factura}"
                producto.usuario_modificador = usuario_valido
                producto.save()
            elif tipo_documento == 'NOTA DE CREDITO':
                producto.stock_actual += int(cantidad)
                producto.motivo_modificacion = f"Devolución Automática - Nota de Crédito Nº {numero_factura}"
                producto.usuario_modificador = usuario_valido
                producto.save()

        if tipo_documento in ["GUIA DE DESPACHO", "NOTA DE CREDITO"]:
            factura.estado_despacho = 'DESPACHADO'
            factura.save()

        if tipo_documento == "GUIA DE DESPACHO":
            nombre_doc = "Guía de despacho"
        elif tipo_documento == "NOTA DE CREDITO":
            nombre_doc = "Nota de crédito"
        else:
            nombre_doc = "Factura"
        return True, f"{nombre_doc} {numero_factura} procesada con éxito."

    except Exception as e:
        return False, f"Error al procesar el archivo: {str(e)}"

def parsear_guia_abastecimiento(archivo):
    """
    Parsea un archivo XML o PDF de una Guía de Abastecimiento (DTE o impreso).
    Retorna una tupla (folio, lista_items).
    Cada item en lista_items es un diccionario:
    {'codigo': str, 'descripcion': str, 'cantidad': int}
    """
    name = getattr(archivo, 'name', '').lower()

    if name.endswith('.xml'):
        # Leer XML
        archivo.seek(0)
        tree = ET.parse(archivo)
        root = tree.getroot()

        # Eliminar namespaces
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        # Extraer Folio
        folio_el = root.find('.//Folio')
        folio = int(folio_el.text) if folio_el is not None else None

        items = []
        detalles_xml = root.findall('.//Detalle')
        for det in detalles_xml:
            codigo_nodo = det.find('.//VlrCodigo')
            nro_lin = det.find('.//NroLinDet').text if det.find('.//NroLinDet') is not None else '1'
            codigo_prod = codigo_nodo.text if codigo_nodo is not None else f"GEN-{nro_lin}"

            desc_nodo = det.find('.//NmbItem')
            descripcion = desc_nodo.text if desc_nodo is not None else "Producto sin nombre"

            qty_nodo = det.find('.//QtyItem')
            try:
                cantidad = int(float(qty_nodo.text)) if qty_nodo is not None else 0
            except ValueError:
                cantidad = 0

            items.append({
                'codigo': codigo_prod.strip(),
                'descripcion': descripcion.strip(),
                'cantidad': cantidad
            })

        return folio, items

    elif name.endswith('.pdf'):
        # Leer PDF
        archivo.seek(0)
        with pdfplumber.open(archivo) as pdf:
            texto_paginas = []
            for page in pdf.pages:
                texto_paginas.append(page.extract_text() or "")
        texto = "\n".join(texto_paginas)

        # Encontrar Folio
        numero_match = re.search(r"Nº\s*(\d+)", texto)
        if not numero_match:
            numero_match = re.search(r"FOLIO\s*:\s*(\d+)", texto, re.IGNORECASE)

        folio = int(numero_match.group(1)) if numero_match else None

        items = []
        for line in texto.split("\n"):
            match_item = re.search(r"^(\d+)\s+([A-Za-z0-9\-]+)\s+(.+?)\s+(UN|KG|LT|u|m|cm|mm|lt|MT|MTS|CJ|CJA|CAJA|CAJAS|PAQ|PAR|SET|ROL|ROLLO|UNID|UNIDADES|METROS|L|LTS|G|GR)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)\s+([\d\.,]+)$", line.strip(), re.IGNORECASE)
            if match_item:
                _, codigo_prod, descripcion, um, cant_str, precio_str, dscto_str, tot_str = match_item.groups()
                try:
                    cantidad = int(float(cant_str.replace(".", "").replace(",", ".")))
                except ValueError:
                    cantidad = 0
                items.append({
                    'codigo': codigo_prod.strip(),
                    'descripcion': descripcion.strip(),
                    'cantidad': cantidad
                })
            else:
                match_flexible = re.search(r"^(\d+)\s+([A-Za-z0-9\-]+)\s+(.+?)\s+(UN|KG|LT|u|m|cm|mm|lt|MT|MTS|CJ|CJA|CAJA|CAJAS|PAQ|PAR|SET|ROL|ROLLO|UNID|UNIDADES|METROS|L|LTS|G|GR)\s+([\d\.,]+)$", line.strip(), re.IGNORECASE)
                if match_flexible:
                    _, codigo_prod, descripcion, um, cant_str = match_flexible.groups()
                    try:
                        cantidad = int(float(cant_str.replace(".", "").replace(",", ".")))
                    except ValueError:
                        cantidad = 0
                    items.append({
                        'codigo': codigo_prod.strip(),
                        'descripcion': descripcion.strip(),
                        'cantidad': cantidad
                    })

        return folio, items
    else:
        raise ValueError("Formato de archivo no soportado. Debe ser XML o PDF.")
