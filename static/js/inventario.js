/**
 * static/js/inventario.js
 * Script orquestador principal de la vista de Inventario para OpenDTE.
 * Delega responsabilidades a los módulos: TableSort, GuiaAbastecimiento, ExcelImport.
 */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Leer configuración de datos incrustada en el HTML
    const configEl = document.getElementById('inventario-config');
    if (!configEl) return;

    let config;
    try {
        config = JSON.parse(configEl.textContent);
    } catch (e) {
        console.error('Error al analizar la configuración del inventario:', e);
        return;
    }

    // 1. Doble clic en filas para editar producto
    const tablaProductos = document.getElementById('tabla-productos');
    const filas = tablaProductos ? tablaProductos.querySelectorAll('tr') : [];

    filas.forEach(fila => {
        fila.addEventListener('dblclick', function() {
            const productoId = this.getAttribute('data-producto-id');
            if (productoId) {
                window.location.href = `/productos/editar/${productoId}/`;
            }
        });
    });

    // 2. Inicializar Ordenación de Tablas y Filtro de Búsqueda
    if (window.OpenDTETableSort) {
        window.OpenDTETableSort.init('#tabla-productos', '#buscar-productos');
    }

    // 3. Inicializar Módulo de Guías de Abastecimiento
    if (window.OpenDTEGuiaAbastecimiento) {
        window.OpenDTEGuiaAbastecimiento.init(config);
    }

    // 4. Inicializar Módulo de Importación desde Excel
    if (window.OpenDTEExcelImport) {
        window.OpenDTEExcelImport.init(config);
    }
});
