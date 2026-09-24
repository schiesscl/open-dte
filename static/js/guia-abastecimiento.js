/**
 * static/js/guia-abastecimiento.js
 * Módulo de guías de abastecimiento e incremento de stock para OpenDTE.
 */

window.OpenDTEGuiaAbastecimiento = (function() {
    'use strict';

    function init(config) {
        const modalGuia = document.getElementById('modal-guia');
        if (!modalGuia) return;

        const alertContainerGuia = document.getElementById('guia-alert-container');
        const paso1 = document.getElementById('guia-paso-1');
        const paso2 = document.getElementById('guia-paso-2');
        const fileInput = document.getElementById('guia-file-input');
        const btnAtras = document.getElementById('btn-guia-atras');
        const btnConfirmar = document.getElementById('btn-guia-confirmar');
        const btnCancelar = document.getElementById('btn-guia-cancelar');
        const btnAgregarManual = document.getElementById('btn-agregar-item-guia');
        const inputFolio = document.getElementById('guia-folio');
        const tablaItemsBody = document.getElementById('guia-tabla-items');

        const productosCatalogo = config.productosCatalogo || [];

        function mostrarPasoGuiaItems() {
            paso1?.classList.add('d-none');
            [paso2, btnAtras, btnConfirmar].forEach(el => el?.classList.remove('d-none'));
        }

        function restaurarBotonConfirmar() {
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = '<i class="bi bi-check2-all me-1" aria-hidden="true"></i> Confirmar e Incrementar Stock';
        }

        function validarFilasGuia() {
            const filas = [...(tablaItemsBody?.querySelectorAll('.item-fila') || [])];
            if (!filas.length) {
                showAlertGuia('Debe haber al menos un ítem para poder ingresar la guía.');
                return null;
            }
            const items = [];
            for (const [index, fila] of filas.entries()) {
                const productoId = fila.querySelector('.product-id-val').value;
                const cantidad = Number(fila.querySelector('.quantity-input').value);
                if (!productoId) {
                    showAlertGuia(`El ítem en la fila ${index + 1} no tiene un producto del catálogo asociado.`);
                    const input = fila.querySelector('.search-input');
                    input.focus();
                    input.classList.add('is-invalid');
                    return null;
                }
                if (!Number.isInteger(cantidad) || cantidad <= 0) {
                    showAlertGuia(`La cantidad del ítem en la fila ${index + 1} debe ser un entero positivo.`);
                    fila.querySelector('.quantity-input').focus();
                    return null;
                }
                items.push({ producto_id: Number(productoId), cantidad, descripcion_origen: fila.children[1].textContent });
            }
            return items;
        }

        function showAlertGuia(mensaje, tipo = 'danger') {
            if (!alertContainerGuia) return;
            alertContainerGuia.innerHTML = `
                <div class="alert alert-${tipo} alert-dismissible fade show shadow-sm" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${mensaje}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            alertContainerGuia.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function resetModalGuia() {
            if (alertContainerGuia) alertContainerGuia.innerHTML = '';
            if (inputFolio) inputFolio.value = '';
            if (tablaItemsBody) tablaItemsBody.innerHTML = '';

            if (paso1) paso1.classList.remove('d-none');
            if (paso2) paso2.classList.add('d-none');
            if (btnAtras) btnAtras.classList.add('d-none');
            if (btnConfirmar) {
                btnConfirmar.classList.add('d-none');
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar e Incrementar Stock';
            }
            if (btnCancelar) btnCancelar.classList.remove('d-none');
            if (fileInput) fileInput.value = '';
        }

        modalGuia.addEventListener('hidden.bs.modal', resetModalGuia);

        if (btnAtras) {
            btnAtras.addEventListener('click', resetModalGuia);
        }

        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length) {
                    procesarArchivoGuia(e.target.files[0]);
                }
            });
        }

        if (paso1) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                paso1.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                paso1.addEventListener(eventName, () => paso1.classList.add('bg-light'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                paso1.addEventListener(eventName, () => paso1.classList.remove('bg-light'), false);
            });

            paso1.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                if (dt.files && dt.files.length) {
                    procesarArchivoGuia(dt.files[0]);
                }
            });
        }

        async function procesarArchivoGuia(file) {
            if (alertContainerGuia) alertContainerGuia.innerHTML = '';

            const formData = new FormData();
            formData.append('archivo', file);
            formData.append('csrfmiddlewaretoken', config.csrfToken);

            try {
                const response = await fetch(config.urls.parseGuia, {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok || !data.exito) {
                    showAlertGuia(data.mensaje || 'Error al procesar el archivo de la guía.');
                    return;
                }

                if (inputFolio && data.folio) {
                    inputFolio.value = data.folio;
                }

                mostrarPasoGuiaItems();

                if (tablaItemsBody) {
                    tablaItemsBody.innerHTML = '';
                    if (data.items && data.items.length) {
                        data.items.forEach(item => {
                            agregarFilaItem(item.codigo, item.descripcion, item.cantidad, item.producto_id_match);
                        });
                    }
                }
            } catch (error) {
                console.error(error);
                showAlertGuia('Error de red al intentar leer el archivo.');
            }
        }

        function agregarFilaItem(codigo = '', descripcion = '', cantidad = 1, matchId = null) {
            if (!tablaItemsBody) return;

            const tr = document.createElement('tr');
            tr.className = 'item-fila';

            const tdCod = document.createElement('td');
            tdCod.textContent = codigo || '-';

            const tdDesc = document.createElement('td');
            tdDesc.textContent = descripcion || '-';

            const tdSelect = document.createElement('td');
            tdSelect.className = 'position-relative';

            let matchedProd = null;
            if (matchId) {
                matchedProd = productosCatalogo.find(p => p.id === matchId);
            }

            const initialText = matchedProd ? `${matchedProd.codigo} - ${matchedProd.descripcion}` : '';
            const initialVal = matchedProd ? matchedProd.id : '';

            tdSelect.innerHTML = `
                <div class="input-group input-group-sm">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control search-input" aria-label="Producto del catálogo" placeholder="Buscar por código o descripción..." autocomplete="off">
                    <input type="hidden" class="product-id-val" value="${initialVal}">
                    <button class="btn btn-outline-secondary btn-clear-select" type="button" title="Limpiar selección"><i class="bi bi-x"></i></button>
                </div>
                <div class="dropdown-menu w-100 search-dropdown shadow-sm style-scrollbar" style="max-height: 200px; overflow-y: auto;"></div>
            `;

            const tdCant = document.createElement('td');
            tdCant.innerHTML = '<input type="number" aria-label="Cantidad" class="form-control form-control-sm text-end quantity-input" min="1" step="1">';
            tdCant.querySelector('input').value = cantidad;
            tdSelect.querySelector('.search-input').value = initialText;

            const tdDel = document.createElement('td');
            tdDel.className = 'text-center';
            tdDel.innerHTML = '<button type="button" aria-label="Eliminar ítem" class="btn btn-sm btn-outline-danger btn-del-row"><i class="bi bi-trash" aria-hidden="true"></i></button>';

            tr.appendChild(tdCod);
            tr.appendChild(tdDesc);
            tr.appendChild(tdSelect);
            tr.appendChild(tdCant);
            tr.appendChild(tdDel);

            tablaItemsBody.appendChild(tr);

            setupFilaEvents(tr);
        }

        function setupFilaEvents(tr) {
            const searchInput = tr.querySelector('.search-input');
            const productIdVal = tr.querySelector('.product-id-val');
            const dropdown = tr.querySelector('.search-dropdown');
            const btnClear = tr.querySelector('.btn-clear-select');
            const btnDel = tr.querySelector('.btn-del-row');

            if (btnDel) {
                btnDel.addEventListener('click', () => tr.remove());
            }

            if (btnClear) {
                btnClear.addEventListener('click', () => {
                    searchInput.value = '';
                    productIdVal.value = '';
                    searchInput.classList.remove('is-invalid');
                });
            }

            if (searchInput) {
                searchInput.addEventListener('input', function() {
                    const term = this.value.toLowerCase().trim();
                    productIdVal.value = '';

                    if (!term) {
                        dropdown.classList.remove('show');
                        return;
                    }

                    const filtered = productosCatalogo.filter(p => 
                        p.codigo.toLowerCase().includes(term) || p.descripcion.toLowerCase().includes(term)
                    );

                    dropdown.innerHTML = '';

                    if (filtered.length === 0) {
                        dropdown.innerHTML = '<div class="dropdown-item text-muted disabled small">Sin coincidencias</div>';
                    } else {
                        filtered.slice(0, 10).forEach(p => {
                            const itemEl = document.createElement('button');
                            itemEl.type = 'button';
                            itemEl.className = 'dropdown-item small';
                            itemEl.textContent = `${p.codigo} - ${p.descripcion}`;
                            itemEl.addEventListener('click', () => {
                                searchInput.value = `${p.codigo} - ${p.descripcion}`;
                                productIdVal.value = p.id;
                                searchInput.classList.remove('is-invalid');
                                dropdown.classList.remove('show');
                            });
                            dropdown.appendChild(itemEl);
                        });
                    }
                    dropdown.classList.add('show');
                });

                document.addEventListener('click', (e) => {
                    if (!tr.contains(e.target)) {
                        dropdown.classList.remove('show');
                    }
                });
            }
        }

        if (btnAgregarManual) {
            btnAgregarManual.addEventListener('click', () => {
                mostrarPasoGuiaItems();
                agregarFilaItem('-', 'Ítem Manual', 1, null);
            });
        }

        if (btnConfirmar) {
            btnConfirmar.addEventListener('click', async () => {
                if (alertContainerGuia) alertContainerGuia.innerHTML = '';
                const folioVal = Number(inputFolio?.value.trim());

                if (!Number.isInteger(folioVal) || folioVal <= 0) {
                    showAlertGuia('El Folio / Número de guía es requerido.');
                    if (inputFolio) inputFolio.focus();
                    return;
                }

                const itemsToSend = validarFilasGuia();
                if (!itemsToSend) return;

                btnConfirmar.disabled = true;
                btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';

                try {
                    const response = await fetch(config.urls.procesarGuia, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': config.csrfToken
                        },
                        body: JSON.stringify({
                            folio: folioVal,
                            items: itemsToSend
                        })
                    });

                    const data = await response.json();

                    if (response.ok && data.exito) {
                        window.location.reload();
                    } else {
                        showAlertGuia(data.mensaje || 'Error al procesar la guía de abastecimiento.');
                        restaurarBotonConfirmar();
                    }
                } catch (error) {
                    console.error(error);
                    showAlertGuia('Error de red al intentar guardar los datos.');
                    restaurarBotonConfirmar();
                }
            });
        }
    }

    return {
        init: init
    };
})();
