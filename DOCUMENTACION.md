# 📄 OpenDTE — Sistema Genérico de Gestión de Documentos Tributarios Electrónicos

> **Versión:** 1.0.0  
> **Basado en:** [OpenDTE ERP](https://github.com/schiesscl/opendte) — Sistema ERP interno de Comercial OpenDTE Ltda.  
> **Licencia:** MIT  
> **País objetivo inicial:** Chile 🇨🇱 (compatible con DTEs del SII)

---

## 📖 Descripción General

**OpenDTE** es una plataforma web **genérica y de código abierto** para la gestión integral de **Documentos Tributarios Electrónicos (DTE)**, inventario de productos y despacho de mercadería. Fue diseñada para ser utilizada por **cualquier empresa chilena** que necesite procesar facturas electrónicas, guías de despacho y notas de crédito emitidas bajo el estándar del **Servicio de Impuestos Internos (SII)** de Chile.

A diferencia del proyecto original (OpenDTE ERP), OpenDTE:

- ✅ **No contiene datos reales** de ninguna empresa.
- ✅ Utiliza **datos de demostración ficticios** que se restauran automáticamente.
- ✅ Usa **PostgreSQL** como base de datos en lugar de SQLite.
- ✅ Implementa el **reset de datos demo mediante JavaScript** (no Python).
- ✅ Es **genérico y configurable** para adaptarse a cualquier empresa.
- ✅ Sigue buenas prácticas de **accesibilidad (WCAG 2.1)**.

---

## 🔗 Relación con el Proyecto Original (OpenDTE ERP)

OpenDTE nace como una **copia genérica y limpia** del proyecto `opendte`, manteniendo la misma arquitectura y estructura de archivos pero eliminando toda referencia a datos empresariales reales.

### Mapeo de Componentes

| OpenDTE (Original) | OpenDTE (Genérico) | Notas |
|---|---|---|
| `opendte_config/` (Django config) | `opendte_config/` | Paquete de configuración Django |
| `inventario/` (App principal) | `inventario/` | App principal renombrada |
| SQLite3 (`db.sqlite3`) | PostgreSQL | Base de datos de producción |
| `manage.py reset_demo` (Python) | API REST + JS frontend | Reset demo vía JavaScript |
| Datos de Comercial OpenDTE | Datos ficticios de "Empresa Demo SpA" | Sin información real |
| `config.json` (rutas compartidas) | Variables de entorno `.env` | Configuración centralizada |
| Bootstrap 5 (bundled) | Bootstrap 5 (CDN + bundled) | Mismo framework CSS |
| PWA + Service Workers | PWA + Service Workers | Misma funcionalidad offline |

---

## 🛠️ Stack Tecnológico

### Backend
| Tecnología | Versión | Propósito |
|---|---|---|
| **Python** | 3.12+ | Lenguaje principal del backend |
| **Django** | 6.0 | Framework web MVC (MTV) |
| **Django REST Framework** | 3.14+ | API RESTful para endpoints JSON |
| **PostgreSQL** | 15+ | Base de datos relacional principal |
| **psycopg2-binary** | 2.9+ | Driver PostgreSQL para Django |
| **WhiteNoise** | 6.x | Servicio de archivos estáticos en producción |
| **python-dotenv** | 1.x | Variables de entorno desde `.env` |
| **Gunicorn** | 23.x | Servidor WSGI para producción |

### Frontend
| Tecnología | Versión | Propósito |
|---|---|---|
| **HTML5** | — | Estructura semántica |
| **CSS3 / Bootstrap 5** | 5.3+ | Framework de diseño responsivo |
| **Bootstrap Icons** | 1.11+ | Iconografía SVG |
| **JavaScript ES6+** | Vanilla | Lógica del cliente, AJAX, PWA |
| **localforage** | 1.10+ | Almacenamiento offline (IndexedDB) |

### Procesamiento de Documentos
| Tecnología | Propósito |
|---|---|
| **pdfplumber** | Extracción de texto de PDFs impresos |
| **pdfminer.six** | Motor de parsing PDF subyacente |
| **xml.etree** | Parsing de XMLs del SII (DTE) |
| **openpyxl / pandas** | Importación/exportación de Excel |

### Herramientas de Desarrollo
| Tecnología | Propósito |
|---|---|
| **Git** | Control de versiones |
| **pip / venv** | Gestión de dependencias Python |
| **npm** | Dependencias JavaScript (localforage) |

---

## 📂 Estructura del Proyecto

```
opendte/
├── manage.py                     # Entry point de Django
├── DOCUMENTACION.md              # ← Este archivo
├── README.md                     # Guía rápida de instalación
├── requirements.txt              # Dependencias Python
├── package.json                  # Dependencias JavaScript
├── runtime.txt                   # Versión de Python para deploy
├── .env.example                  # Plantilla de variables de entorno
├── .gitignore                    # Reglas de exclusión Git
├── config.json                   # Configuración de rutas compartidas
│
├── opendte_config/               # 🔧 Paquete de configuración Django
│   ├── __init__.py
│   ├── settings.py               # Configuración principal (PostgreSQL, apps, middleware)
│   ├── urls.py                   # Rutas raíz (admin, API, app, PWA)
│   ├── wsgi.py                   # WSGI para producción
│   └── asgi.py                   # ASGI para producción
│
├── inventario/                   # 📦 App principal de Django
│   ├── __init__.py
│   ├── models.py                 # Modelos de datos (Producto, Factura, Cliente, etc.)
│   ├── views.py                  # Vistas basadas en funciones (Dashboard, CRUD, Despacho)
│   ├── urls.py                   # Rutas de la app
│   ├── forms.py                  # Formularios Django (ProductoForm, ClienteForm, FacturaForm)
│   ├── admin.py                  # Configuración del panel de administración
│   ├── api.py                    # ViewSets DRF (REST API)
│   ├── serializers.py            # Serializadores DRF
│   ├── utils.py                  # Parsers XML/PDF, lógica de negocio
│   ├── config.py                 # Gestión de rutas de carpetas compartidas
│   ├── context_processors.py     # Inyección de contexto global (badge buzón)
│   ├── apps.py                   # Configuración de la app Django
│   ├── tests.py                  # Suite de tests
│   │
│   ├── fixtures/                 # 📋 Datos de demostración
│   │   └── demo_seed.json        # Fixture JSON con datos ficticios
│   │
│   ├── management/               # 🔨 Comandos de gestión
│   │   └── commands/
│   │       ├── import_productos.py   # Importar productos desde Excel
│   │       └── seed_demo.py          # Cargar datos demo desde fixture
│   │
│   ├── migrations/               # 🗃️ Migraciones de base de datos
│   │   └── ...
│   │
│   ├── templates/                # 🎨 Templates HTML
│   │   └── inventario/
│   │       ├── base.html             # Layout principal (sidebar, navbar, PWA)
│   │       ├── dashboard.html        # Panel de control con métricas
│   │       ├── lista_productos.html  # Inventario (tabla, filtros, acciones)
│   │       ├── lista_facturas.html   # Registro de documentos tributarios
│   │       ├── lista_clientes.html   # Directorio de clientes
│   │       ├── lista_compartida.html # Buzón compartido de facturas
│   │       ├── despacho.html         # Módulo de despacho de mercadería
│   │       ├── editar_producto.html  # Formulario de edición de producto
│   │       ├── editar_producto_masivo.html # Edición masiva de productos
│   │       ├── editar_cliente.html   # Formulario de edición de cliente
│   │       ├── editar_factura.html   # Formulario de edición de factura
│   │       ├── facturas_cliente.html # Facturas pendientes por cliente
│   │       ├── guia_despacho.html    # Vista de guía de despacho para impresión
│   │       ├── historial_despachos.html # Historial de despachos realizados
│   │       ├── modal_factura.html    # Modal para ver detalle de factura
│   │       └── stock_vendedores.html # Vista simplificada para vendedores
│   │
│   └── templatetags/             # 🏷️ Filtros de template personalizados
│       ├── __init__.py
│       └── custom_filters.py     # price_format (separador de miles chileno)
│
├── static/                       # 🎨 Archivos estáticos
│   ├── css/
│   │   ├── bootstrap.min.css     # Bootstrap 5 compilado
│   │   ├── bootstrap-icons.css   # Bootstrap Icons
│   │   └── style.css             # Estilos personalizados (tema claro/oscuro)
│   ├── js/
│   │   ├── bootstrap.bundle.min.js # Bootstrap 5 JS
│   │   ├── inventario.js         # Lógica principal del frontend
│   │   ├── api.js                # Sincronización offline y API calls
│   │   ├── offline-db.js         # Configuración de IndexedDB (localforage)
│   │   └── localforage.min.js    # Librería de almacenamiento offline
│   └── img/                      # Imágenes y favicon
│       ├── logo.webp             # Logo genérico
│       └── favicon.ico           # Favicon genérico
│
└── media/                        # 📁 Archivos subidos por usuarios (dinámico)
    ├── compartida/               # Buzón de entrada de facturas
    ├── compartida_procesadas/    # Facturas procesadas con éxito
    └── compartida_errores/       # Facturas con errores de procesamiento
```

---

## 🏗️ Arquitectura de la Aplicación

### Patrón MTV (Model-Template-View)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NAVEGADOR (Cliente)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │ Bootstrap 5  │  │  Vanilla JS  │  │   PWA (Service Workers)   │  │
│  │   + Icons    │  │  + AJAX      │  │   + localforage           │  │
│  └─────────────┘  └──────────────┘  └───────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTP/HTTPS
┌─────────────────────────────▼───────────────────────────────────────┐
│                      DJANGO (Backend)                              │
│                                                                     │
│  ┌──────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │
│  │   Views (MTV)     │  │  REST API (DRF)   │  │   Admin Panel   │  │
│  │   - Dashboard     │  │  - /api/clientes/ │  │   /admin/       │  │
│  │   - CRUD Ops      │  │  - /api/productos/│  │                 │  │
│  │   - Despacho      │  │  - /api/facturas/ │  │                 │  │
│  │   - Buzón         │  │  - /api/upload/   │  │                 │  │
│  └────────┬─────────┘  └────────┬──────────┘  └────────┬────────┘  │
│           │                     │                       │           │
│  ┌────────▼─────────────────────▼───────────────────────▼────────┐  │
│  │                    Models (ORM Django)                         │  │
│  │  Producto │ Cliente │ Factura │ DetalleFactura │ Despacho     │  │
│  │  Sucursal │ Bodega  │ GuíaAbast │ HistorialStock              │  │
│  └────────────────────────────┬──────────────────────────────────┘  │
│                               │                                     │
│  ┌────────────────────────────▼──────────────────────────────────┐  │
│  │                     PostgreSQL                                │  │
│  │                  (Base de datos)                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              Utils (Procesamiento de Documentos)               │  │
│  │  - procesar_factura_xml() → Parser XML del SII (DTE)          │  │
│  │  - procesar_factura_pdf() → Parser PDF impreso (pdfplumber)   │  │
│  │  - parsear_guia_abastecimiento() → Parser Guías XML/PDF       │  │
│  │  - calcular_dv() → Validación RUT chileno                     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Modelos de Datos

### Diagrama Entidad-Relación

```
┌───────────────────────┐          ┌───────────────────────┐
│       Sucursal         │          │       Bodega           │
├───────────────────────┤          ├───────────────────────┤
│ id (PK)               │ 1    N   │ id (PK)               │
│ nombre (unique)       │◄────────│ nombre                │
│ codigo (unique)       │          │ codigo                │
│ direccion             │          │ sucursal_id (FK)      │
│ activa                │          │ activa                │
│ fecha_creacion        │          │ fecha_creacion        │
└───────────────────────┘          └───────────────────────┘

┌───────────────────────┐          ┌───────────────────────┐
│       Cliente          │          │       Producto         │
├───────────────────────┤          ├───────────────────────┤
│ id (PK)               │          │ id (PK)               │
│ rut (unique)          │          │ codigo (unique)       │
│ razon_social          │          │ codigo_alternativo    │
│ giro                  │          │ cant_alternativo      │
│ direccion             │          │ codigo_alternativo_2  │
│ comuna                │          │ cant_alternativo_2    │
│ ciudad                │          │ codigo_alternativo_3  │
│ telefono              │          │ cant_alternativo_3    │
└────────┬──────────────┘          │ descripcion           │
         │ 1                       │ unidad_medida         │
         │                         │ stock_actual          │
         │ N                       │ stock_real            │
┌────────▼──────────────┐          │ stock_minimo          │
│       Factura          │          │ stock_sistema         │
├───────────────────────┤          │ precio_venta          │
│ id (PK)               │          │ activo                │
│ usuario_creador (FK)  │          │ fecha_creacion        │
│ numero                │          │ fecha_actualizacion   │
│ tipo_documento        │          └────────┬──────────────┘
│ fecha_emision         │                   │
│ cliente_id (FK)       │                   │
│ neto                  │          ┌────────▼──────────────┐
│ iva                   │          │   DetalleFactura       │
│ total                 │          ├───────────────────────┤
│ fecha_subida          │ 1    N   │ id (PK)               │
│ archivo_origen        │◄────────│ factura_id (FK)       │
│ estado_despacho       │          │ producto_id (FK)      │
└────────┬──────────────┘          │ cantidad              │
         │ 1                       │ precio_unitario       │
         │                         │ total_linea           │
         │ 1                       └───────────────────────┘
┌────────▼──────────────┐
│       Despacho         │          ┌───────────────────────┐
├───────────────────────┤          │   HistorialStock       │
│ id (PK)               │          ├───────────────────────┤
│ factura_id (FK, 1:1)  │          │ id (PK)               │
│ usuario_id (FK)       │          │ producto_id (FK)      │
│ fecha_despacho        │          │ fecha                 │
└───────────────────────┘          │ stock_actual_anterior │
                                   │ stock_actual_nuevo    │
┌───────────────────────┐          │ stock_real_anterior   │
│ GuíaAbastecimiento     │          │ stock_real_nuevo      │
├───────────────────────┤          │ detalle               │
│ id (PK)               │          │ usuario_id (FK)       │
│ numero (unique)       │          └───────────────────────┘
│ fecha_registro        │
│ usuario_id (FK)       │
└────────┬──────────────┘
         │ 1
         │ N
┌────────▼──────────────┐
│ DetalleGuíaAbastec.    │
├───────────────────────┤
│ id (PK)               │
│ guia_id (FK)          │
│ producto_id (FK)      │
│ cantidad              │
└───────────────────────┘
```

---

## ⚡ Características Principales

### 1. Panel de Control (Dashboard)
- Métricas consolidadas por período (ventas, facturas, guías, notas de crédito).
- Filtrado flexible: semana actual, mes, año, rango personalizado, relativo.
- Indicadores de documentos despachados vs. pendientes.
- Últimos 10 documentos subidos y documentos del período seleccionado.

### 2. Gestión de Inventario (Productos)
- CRUD completo de productos con múltiples códigos (principal + 3 alternativos).
- Cada código alternativo tiene un multiplicador configurable para embalajes.
- Seguimiento de 4 niveles de stock: Actual, Real, Mínimo y Sistema.
- Edición masiva de productos (campos comunes editables, campos distintos bloqueados).
- Historial de modificaciones de stock con trazabilidad de usuario.
- Importación desde archivos Excel con mapeo de columnas dinámico.

### 3. Procesamiento de Documentos Tributarios (DTE)
- **XML del SII:** Parsing automático de DTEs electrónicos (Tipo 33, 34, 52, 61).
- **PDF impreso:** Extracción de datos de facturas escaneadas con regex avanzados.
- **Tipos soportados:**
  - Factura Electrónica (Tipo 33)
  - Factura Electrónica Exenta (Tipo 34)
  - Guía de Despacho (Tipo 52)
  - Nota de Crédito (Tipo 61)
- Detección de duplicados por número + tipo de documento.
- Creación automática de clientes a partir de datos del DTE.
- Modificación automática de stock según tipo de documento.

### 4. Despacho de Mercadería
- Buscador de facturas pendientes por número.
- Confirmación de despacho con descuento automático de stock.
- Historial de despachos con registro de usuario y fecha.
- Generación de guías de despacho para impresión.

### 5. Buzón Compartido (Carpeta Compartida)
- Monitoreo de carpeta local/red para facturas depositadas.
- Procesamiento automático con clasificación en éxito/error.
- Archivos `.err` con registro del motivo de fallo.
- Subida manual vía AJAX desde el navegador.
- Configuración dinámica de rutas de carpetas.

### 6. Guías de Abastecimiento
- Parsing de guías de traslado (XML/PDF) con coincidencia de productos.
- Incremento automático de stock al confirmar una guía de entrada.
- Historial de guías procesadas con detalle de productos.

### 7. API REST
- Endpoints CRUD para Clientes, Productos, Facturas y Detalles.
- Endpoint de subida de archivos (PDF/XML) vía API.
- Respuestas JSON para integración con sistemas externos.

### 8. PWA (Progressive Web App)
- Service Worker con estrategia Network-First y fallback offline.
- Botón "Preparar Offline" para pre-cargar assets.
- Cola de operaciones pendientes en IndexedDB (localforage).
- Sincronización automática al recuperar conexión.

### 9. Sistema de Reset Demo (JavaScript)
- Endpoint API para restaurar datos de demostración.
- Frontend JavaScript que invoca el reset sin recarga completa.
- Datos ficticios sin información real de empresas.
- Restauración de productos, clientes, facturas y despachos a su estado original.

### 10. Temas (Claro/Oscuro)
- Soporte nativo de tema claro y oscuro.
- Switch en sidebar para cambiar de tema.
- Persistencia de preferencia en localStorage.
- CSS Variables para tematización completa.

---

## 🔧 Configuración y Despliegue

### Variables de Entorno (.env)

```env
# === Seguridad ===
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# === Base de Datos PostgreSQL ===
DB_NAME=opendte_db
DB_USER=opendte_user
DB_PASSWORD=tu-contraseña-aqui
DB_HOST=localhost
DB_PORT=5432
```

### Requisitos Previos
1. Python 3.12+
2. PostgreSQL 15+
3. Node.js 18+ (para localforage)
4. Git

### Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/opendte.git
cd opendte

# 2. Crear y activar entorno virtual
python -m venv env
# Windows:
env\Scripts\activate
# Linux/Mac:
source env/bin/activate

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Instalar dependencias JavaScript
npm install

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus datos

# 6. Crear la base de datos PostgreSQL
# (Asegúrate de tener PostgreSQL corriendo)
# En psql:
# CREATE DATABASE opendte_db;
# CREATE USER opendte_user WITH PASSWORD 'tu-contraseña';
# GRANT ALL PRIVILEGES ON DATABASE opendte_db TO opendte_user;

# 7. Ejecutar migraciones
python manage.py migrate

# 8. Cargar datos de demostración
python manage.py seed_demo

# 9. Crear superusuario (admin)
python manage.py createsuperuser

# 10. Iniciar el servidor
python manage.py runserver
```

---

## 🎨 Diseño y UI/UX

### Sistema de Diseño
- **Framework:** Bootstrap 5.3 con tema personalizado.
- **Iconografía:** Bootstrap Icons (SVG).
- **Layout:** Sidebar fijo en escritorio, offcanvas en móvil.
- **Tipografía:** Hereda del sistema operativo (system-ui).
- **Paleta de colores:**
  - **Primario:** `#F9EA15` (amarillo corporativo, configurable).
  - **Fondo claro:** `#f4f6f9` / **Fondo oscuro:** `#121316`.
  - **Cards:** `#ffffff` (claro) / `#1e2025` (oscuro).
  - **Sidebar:** `#ffffff` (claro) / `#111215` (oscuro).

### Componentes Reutilizables
1. **Sidebar** — Navegación principal con ítems activos y badge de buzón.
2. **Cards métricas** — Dashboard con indicadores y sub-indicadores.
3. **Tablas responsivas** — Con filtrado, búsqueda y acciones por fila.
4. **Modales** — Para CRUD, subida de archivos y confirmaciones.
5. **Toasts** — Notificaciones en tiempo real (éxito/error).
6. **Formularios** — Bootstrap forms con validación frontend y backend.

---

## 🌐 Accesibilidad (WCAG 2.1)

OpenDTE implementa las siguientes mejoras de accesibilidad respecto al proyecto original:

- **Atributos ARIA** en navegación, modales y formularios.
- **Labels** descriptivos en todos los inputs de formularios.
- **Contraste** de colores verificado para ambos temas.
- **Navegación por teclado** soportada en todos los elementos interactivos.
- **Texto alternativo** en imágenes y logos.
- **Focus visible** personalizado para elementos interactivos.
- **Landmark roles** semánticos (`main`, `nav`, `aside`, `header`).

---

## 🗺️ Rutas y Endpoints

### Vistas Web (Frontend)
| Ruta | Vista | Descripción |
|---|---|---|
| `/` | `dashboard` | Panel de control principal |
| `/productos/` | `lista_productos` | Inventario de productos |
| `/productos/crear/` | `crear_producto` | Crear nuevo producto |
| `/productos/editar/<id>/` | `editar_producto` | Editar producto existente |
| `/productos/editar-masivo/` | `editar_producto_masivo` | Edición masiva de productos |
| `/productos/eliminar/<id>/` | `eliminar_producto` | Eliminar producto |
| `/stock-vendedores/` | `stock_vendedores` | Vista simplificada para vendedores |
| `/clientes/` | `lista_clientes` | Directorio de clientes |
| `/clientes/editar/<id>/` | `editar_cliente` | Editar cliente |
| `/clientes/eliminar/<id>/` | `eliminar_cliente` | Eliminar cliente |
| `/facturas/` | `lista_facturas` | Registro histórico de documentos |
| `/facturas/editar/<id>/` | `editar_factura` | Editar factura |
| `/facturas/eliminar/<id>/` | `eliminar_factura` | Eliminar factura |
| `/facturas/ver/<id>/` | `ver_factura` | Ver detalle (modal) |
| `/clientes/<id>/facturas/` | `facturas_cliente` | Facturas pendientes de un cliente |
| `/despacho/` | `preparar_despacho` | Módulo de despacho |
| `/despacho/confirmar/<id>/` | `confirmar_despacho` | Confirmar despacho |
| `/despacho/historial/` | `historial_despachos` | Historial de despachos |
| `/despachos/guia/<id>/` | `ver_guia_despacho` | Guía de despacho para impresión |
| `/compartida/` | `lista_compartida` | Buzón compartido |
| `/subir/` | `subir_documento` | Subir documento manualmente |

### API REST
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/clientes/` | Listar clientes |
| POST | `/api/clientes/` | Crear cliente |
| GET/PUT/DELETE | `/api/clientes/<id>/` | CRUD individual |
| GET | `/api/productos/` | Listar productos |
| POST | `/api/productos/` | Crear producto |
| GET/PUT/DELETE | `/api/productos/<id>/` | CRUD individual |
| GET | `/api/facturas/` | Listar facturas |
| GET | `/api/detalles-factura/` | Listar detalles |
| POST | `/api/upload-factura/` | Subir factura PDF/XML |
| GET | `/api/producto-por-codigo/?codigo=X` | Buscar por código |

### API Interna (AJAX)
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/compartida/subir-archivo/` | Subir archivo al buzón |
| POST | `/compartida/importar/` | Importar factura del buzón |
| POST | `/compartida/eliminar/` | Eliminar archivo del buzón |
| GET | `/compartida/api/status/` | Estado del buzón + auto-procesamiento |
| POST | `/compartida/configurar/guardar/` | Guardar configuración de rutas |
| POST | `/productos/guia/analizar/` | Analizar guía de abastecimiento |
| POST | `/productos/guia/procesar/` | Procesar guía confirmada |
| POST | `/productos/importar-excel/analizar/` | Analizar Excel para importación |
| POST | `/productos/importar-excel/procesar/` | Ejecutar importación Excel |
| POST | `/api/demo/reset/` | **Restaurar datos de demostración** |

---

## 🧩 Extensibilidad

OpenDTE fue diseñado para ser extendido y adaptado:

1. **Multi-empresa:** Agregar un modelo `Empresa` y campo `empresa` en cada modelo.
2. **Multi-país:** Adaptar los parsers XML/PDF a otros formatos de facturación electrónica.
3. **Roles y permisos:** Implementar `@login_required` y grupos de usuarios (Admin, Operario, Vendedor).
4. **Integraciones:** Los endpoints REST permiten integración con ERP externos, apps móviles, etc.
5. **Personalización visual:** Las CSS Variables permiten cambiar la paleta completa sin tocar componentes.

---

## 📝 Changelog

### v1.0.0 (Julio 2026) — Versión Inicial
- Fork genérico del proyecto OpenDTE ERP.
- Migración de SQLite a PostgreSQL.
- Eliminación de datos empresariales reales.
- Implementación de datos demo ficticios con reset via JavaScript.
- Mejoras de accesibilidad (WCAG 2.1).
- Documentación completa del proyecto.

---

## 📜 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

Basado en el trabajo original de [schiesscl/opendte](https://github.com/schiesscl/opendte).
