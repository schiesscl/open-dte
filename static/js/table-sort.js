/**
 * static/js/table-sort.js
 * Módulo de ordenación de columnas y filtrado multi-palabra para tablas de OpenDTE.
 */

window.OpenDTETableSort = (function() {
    'use strict';

    function initTableSort(tablaSelector, inputBuscarSelector) {
        const tablaProductos = document.querySelector(tablaSelector);
        if (!tablaProductos) return;

        const filas = tablaProductos.querySelectorAll('tr');
        const buscarInput = document.querySelector(inputBuscarSelector);

        // Filtrado en tiempo real con búsqueda multi-palabra
        if (buscarInput) {
            buscarInput.addEventListener('input', function() {
                const termino = this.value.toLowerCase().trim();
                const palabras = termino.split(/\s+/).filter(p => p.length > 0);

                filas.forEach(fila => {
                    if (fila.textContent.includes('No hay productos registrados') || fila.textContent.includes('Aún no hay')) {
                        return;
                    }

                    const textoFila = fila.textContent.toLowerCase();

                    if (termino === '') {
                        fila.style.display = '';
                    } else {
                        const todasEncontradas = palabras.every(palabra => textoFila.includes(palabra));
                        fila.style.display = todasEncontradas ? '' : 'none';
                    }
                });

                const filasVisibles = Array.from(filas).filter(fila => {
                    return fila.style.display !== 'none' && !fila.textContent.includes('No hay productos') && !fila.textContent.includes('Aún no hay');
                });

                const filaVacia = tablaProductos.querySelector('tr:has(td[colspan])');
                if (filasVisibles.length === 0 && filaVacia) {
                    filaVacia.style.display = '';
                } else if (filaVacia) {
                    filaVacia.style.display = 'none';
                }
            });
        }

        // Ordenación por columnas
        const tabla = tablaProductos.closest('table');
        if (!tabla) return;

        const headers = tabla.querySelectorAll('thead th');
        let direccionOrden = {};

        headers.forEach((header, index) => {
            const texto = header.textContent.trim().toLowerCase();
            if (index === 0 && header.querySelector('input[type="checkbox"]')) {
                return;
            }
            if (texto === 'acciones' || texto === 'eliminar') {
                return;
            }

            header.style.cursor = 'pointer';
            header.classList.add('user-select-none');

            let iconSpan = header.querySelector('.sort-icon');
            if (!iconSpan) {
                iconSpan = document.createElement('span');
                iconSpan.className = 'ms-1 text-muted sort-icon';
                iconSpan.innerHTML = '<i class="bi bi-arrow-down-up small opacity-50"></i>';
                header.appendChild(iconSpan);
            }

            header.addEventListener('click', () => {
                const actualDir = direccionOrden[index] || 1;
                const nuevaDir = actualDir === 1 ? -1 : 1;
                direccionOrden = {};
                direccionOrden[index] = nuevaDir;

                tabla.querySelectorAll('thead th .sort-icon').forEach(span => {
                    span.innerHTML = '<i class="bi bi-arrow-down-up small opacity-50"></i>';
                });

                iconSpan.innerHTML = nuevaDir === 1 
                    ? '<i class="bi bi-arrow-up text-primary"></i>' 
                    : '<i class="bi bi-arrow-down text-primary"></i>';

                sortTabla(tablaProductos, index, nuevaDir);
            });
        });
    }

    function sortTabla(tbody, columnaIdx, direccion) {
        if (!tbody) return;

        const filas = Array.from(tbody.querySelectorAll('tr')).filter(f => !f.textContent.includes('No hay productos') && !f.textContent.includes('Aún no hay'));

        filas.sort((a, b) => {
            const tdA = a.children[columnaIdx];
            const tdB = b.children[columnaIdx];

            if (!tdA || !tdB) return 0;

            let valA = tdA.textContent.trim();
            let valB = tdB.textContent.trim();

            // Intento numérico (para stock, precios, etc)
            const numA = parseFloat(valA.replace(/\$/g, '').replace(/\./g, '').replace(',', '.'));
            const numB = parseFloat(valB.replace(/\$/g, '').replace(/\./g, '').replace(',', '.'));

            if (!isNaN(numA) && !isNaN(numB)) {
                return (numA - numB) * direccion;
            }

            return valA.localeCompare(valB, 'es', { sensitivity: 'base' }) * direccion;
        });

        filas.forEach(fila => tbody.appendChild(fila));
    }

    return {
        init: initTableSort
    };
})();
