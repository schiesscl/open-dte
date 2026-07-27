# OpenDTE — Sistema Genérico de Documentos Tributarios Electrónicos (DTE)

OpenDTE es una versión limpia, genérica y libre de datos sensibles de **Full-Sello ERP**, adaptada para ser compatible con PostgreSQL y optimizada para servir como base de un sistema de facturación electrónica y gestión de inventario en Chile.

## Características Clave

- **Base de datos:** PostgreSQL en lugar de SQLite3.
- **Demo Reset:** Restauración de base de datos desde el navegador mediante JavaScript/AJAX (sin necesidad de comandos Python).
- **Procesamiento de Facturas:** Lectura volátil en memoria de PDFs y XMLs emitidos bajo el estándar del SII.
- **Validación de RUT:** Verificación en tiempo real y backend mediante el algoritmo oficial Módulo 11 con formateo automático (XX.XXX.XXX-Y).
- **Frontend Modular:** Arquitectura de scripts JavaScript dividida en módulos con responsabilidades únicas (validators.js, table-sort.js, excel-import.js, guia-abastecimiento.js).
- **PWA Offline:** Capacidad de operar sin internet con IndexedDB (`localforage`) y sincronización automática.
- **Diseño Accesible:** Cumplimiento con pautas básicas WCAG 2.1 para navegación por teclado y contraste adaptativo claro/oscuro.

---

## Requisitos Previos

1. **Python 3.12+**
2. **PostgreSQL 15+**
3. **Node.js** (para dependencias frontend)

---

## Instalación y Puesta en Marcha

1. **Clonar e ingresar al proyecto:**

   ```bash
   git clone https://github.com/schiesscl/open-dte.git
   cd open-dte
   ```

2. **Crear y activar entorno virtual:**

   ```bash
   python -m venv env
   # Windows:
   env\Scripts\activate
   # Linux/Mac:
   source env/bin/activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   npm install
   ```

4. **Configurar el archivo `.env`:**

   ```bash
   cp .env.example .env
   # Edita el archivo .env configurando los accesos a tu PostgreSQL local
   ```

5. **Preparar la Base de Datos en PostgreSQL:**

   ```sql
   CREATE DATABASE opendte_db;
   CREATE USER opendte_user WITH PASSWORD 'tu_password';
   GRANT ALL PRIVILEGES ON DATABASE opendte_db TO opendte_user;
   ```

6. **Ejecutar migraciones y cargar semillas demo:**

   ```bash
   python manage.py migrate
   python manage.py seed_demo
   ```

7. **Crear superusuario administrador:**

   ```bash
   python manage.py createsuperuser
   ```

8. **Iniciar el servidor local:**

   ```bash
   python manage.py runserver
   ```

---

## Documentación Completa

Para una descripción exhaustiva del diseño de base de datos, mapeo de componentes del fork, endpoints de la API, flujos de sincronización offline y arquitectura general, consulte el archivo [DOCUMENTACION.md](file:///e:/opendte/DOCUMENTACION.md).

## Licencia

Este proyecto es de código abierto bajo la licencia MIT.
