document.addEventListener('DOMContentLoaded', function() {
    // Leer configuración de datos incrustada en el HTML
    const configEl = document.getElementById('inventario-config');
    if (!configEl) {
        console.error('No se encontró el elemento de configuración del inventario.');
        return;
    }
    
    let config;
    try {
        config = JSON.parse(configEl.textContent);
    } catch (e) {
        console.error('Error al analizar la configuración del inventario:', e);
        return;
    }

    const buscarInput = document.getElementById('buscar-productos');
    const tablaProductos = document.getElementById('tabla-productos');
    const filas = tablaProductos ? tablaProductos.querySelectorAll('tr') : [];

    // Agregar listener para doble clic en filas
    filas.forEach(fila => {
        fila.addEventListener('dblclick', function() {
            const productoId = this.getAttribute('data-producto-id');
            if (productoId) {
                window.location.href = `/productos/editar/${productoId}/`;
            }
        });
    });

    if (buscarInput) {
        buscarInput.addEventListener('input', function() {
            const termino = this.value.toLowerCase().trim();
            const palabras = termino.split(/\s+/).filter(p => p.length > 0);

            filas.forEach(fila => {
                if (fila.textContent.includes('No hay productos registrados')) {
                    return;
                }

                const textoFila = fila.textContent.toLowerCase();

                if (termino === '') {
                    fila.style.display = '';
                } else {
                    const todasPalabrasEncontradas = palabras.every(palabra => textoFila.includes(palabra));
                    fila.style.display = todasPalabrasEncontradas ? '' : 'none';
                }
            });

            const filasVisibles = Array.from(filas).filter(fila => {
                return fila.style.display !== 'none' && !fila.textContent.includes('No hay productos registrados');
            });

            const filaVacia = tablaProductos ? tablaProductos.querySelector('tr:has(td[colspan])') : null;
            if (filasVisibles.length === 0 && filaVacia) {
                filaVacia.style.display = '';
            } else if (filaVacia) {
                filaVacia.style.display = 'none';
            }
        });
    }

    // Lógica de Ordenación de Columnas
    const headers = document.querySelectorAll('table th');
    let direccionOrden = {};

    headers.forEach((header, index) => {
        if (index === 0 || header.textContent.trim().toLowerCase() === 'acciones') {
            return;
        }

        header.style.cursor = 'pointer';
        header.classList.add('user-select-none');
        
        const iconSpan = document.createElement('span');
        iconSpan.className = 'ms-1 text-muted sort-icon';
        iconSpan.innerHTML = '<i class="bi bi-arrow-down-up small opacity-50"></i>';
        header.appendChild(iconSpan);

        header.addEventListener('click', () => {
            const actualDir = direccionOrden[index] || 1;
            const nuevaDir = actualDir === 1 ? -1 : 1;
            direccionOrden = {};
            direccionOrden[index] = nuevaDir;

            document.querySelectorAll('table th .sort-icon').forEach(span => {
                span.innerHTML = '<i class="bi bi-arrow-down-up small opacity-50"></i>';
            });

            iconSpan.innerHTML = nuevaDir === 1 
                ? '<i class="bi bi-arrow-up text-primary"></i>' 
                : '<i class="bi bi-arrow-down text-primary"></i>';

            sortTabla(index, nuevaDir);
        });
    });

    function sortTabla(columnaIdx, direccion) {
        if (!tablaProductos) return;
        const filasArray = Array.from(tablaProductos.querySelectorAll('tr'));
        const filasDeDatos = filasArray.filter(fila => {
            return !fila.textContent.includes('No hay productos registrados') && !fila.querySelector('td[colspan]');
        });

        filasDeDatos.sort((filaA, filaB) => {
            const celdaA = filaA.children[columnaIdx];
            const celdaB = filaB.children[columnaIdx];

            let valA = celdaA ? celdaA.textContent.trim() : '';
            let valB = celdaB ? celdaB.textContent.trim() : '';

            const esNumerica = columnaIdx >= 6 && columnaIdx <= 9;

            if (esNumerica) {
                let numA = parseFloat(valA.replace('+', '').trim());
                let numB = parseFloat(valB.replace('+', '').trim());

                if (isNaN(numA)) numA = 0;
                if (isNaN(numB)) numB = 0;

                return (numA - numB) * direccion;
            } else {
                return valA.localeCompare(valB, 'es', { numeric: true, sensitivity: 'base' }) * direccion;
            }
        });

        filasDeDatos.forEach(fila => tablaProductos.appendChild(fila));
        
        const filaVacia = tablaProductos.querySelector('tr:has(td[colspan])');
        if (filaVacia) {
            tablaProductos.appendChild(filaVacia);
        }
    }

    // --- LÓGICA DE SELECCIÓN MÚLTIPLE Y EDICIÓN MASIVA ---
    const selectAllCheckbox = document.getElementById('select-all-productos');
    const checkboxesProductos = document.querySelectorAll('.select-producto');
    const btnEditarMasivo = document.getElementById('btn-editar-masivo');
    const selectedCountSpan = document.getElementById('selected-count');

    function updateBulkEditState() {
        const checkedCount = document.querySelectorAll('.select-producto:checked').length;
        if (selectedCountSpan) {
            selectedCountSpan.textContent = checkedCount;
        }
        if (btnEditarMasivo) {
            if (checkedCount > 0) {
                btnEditarMasivo.removeAttribute('disabled');
            } else {
                btnEditarMasivo.setAttribute('disabled', 'true');
            }
        }
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            checkboxesProductos.forEach(cb => {
                const row = cb.closest('tr');
                if (row && row.style.display !== 'none') {
                    cb.checked = selectAllCheckbox.checked;
                }
            });
            updateBulkEditState();
        });
    }

    checkboxesProductos.forEach(cb => {
        cb.addEventListener('change', function(e) {
            e.stopPropagation();
            updateBulkEditState();
        });
        const td = cb.closest('td');
        if (td) {
            td.addEventListener('click', function(e) {
                e.stopPropagation();
            });
            td.addEventListener('dblclick', function(e) {
                e.stopPropagation();
            });
        }
    });

    if (btnEditarMasivo) {
        btnEditarMasivo.addEventListener('click', function() {
            const selectedIds = [];
            document.querySelectorAll('.select-producto:checked').forEach(cb => {
                selectedIds.push(cb.getAttribute('data-id'));
            });
            if (selectedIds.length > 0) {
                window.location.href = `/productos/editar-masivo/?ids=` + selectedIds.join(',');
            }
        });
    }

    // --- LÓGICA DE INGRESO DE GUÍAS DE ABASTECIMIENTO ---
    const allProducts = config.productos || [];

    const modalGuiaEl = document.getElementById('modal-guia');
    const dragZone = document.getElementById('guia-paso-1');
    const fileInput = document.getElementById('guia-file-input');
    const passo1 = document.getElementById('guia-paso-1');
    const passo2 = document.getElementById('guia-paso-2');
    const btnAtras = document.getElementById('btn-guia-atras');
    const btnConfirmar = document.getElementById('btn-guia-confirmar');
    const btnCancelar = document.getElementById('btn-guia-cancelar');
    const inputFolio = document.getElementById('guia-folio');
    const tablaItemsBody = document.getElementById('guia-tabla-items');
    const btnAgregarItem = document.getElementById('btn-agregar-item-guia');
    const alertContainerGuia = document.getElementById('guia-alert-container');

    // Drag and Drop
    if (dragZone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dragZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dragZone.style.backgroundColor = 'var(--sidebar-hover-bg)';
                dragZone.style.borderColor = 'var(--fs-yellow)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dragZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dragZone.style.backgroundColor = '';
                dragZone.style.borderColor = '';
            }, false);
        });

        dragZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                procesarArchivoGuia(files[0]);
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (fileInput.files.length) {
                procesarArchivoGuia(fileInput.files[0]);
            }
        });
    }

    if (modalGuiaEl) {
        modalGuiaEl.addEventListener('hidden.bs.modal', () => {
            resetModalGuia();
        });
    }

    function resetModalGuia() {
        if (fileInput) fileInput.value = '';
        if (inputFolio) inputFolio.value = '';
        if (tablaItemsBody) tablaItemsBody.innerHTML = '';
        if (alertContainerGuia) alertContainerGuia.innerHTML = '';
        if (passo1) passo1.classList.remove('d-none');
        if (passo2) passo2.classList.add('d-none');
        if (btnAtras) btnAtras.classList.add('d-none');
        if (btnConfirmar) btnConfirmar.classList.add('d-none');
        if (btnCancelar) btnCancelar.classList.remove('d-none');
    }

    if (btnAtras) {
        btnAtras.addEventListener('click', () => {
            resetModalGuia();
        });
    }

    function showAlertGuia(msg, type = 'danger') {
        if (alertContainerGuia) {
            alertContainerGuia.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${msg}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        }
    }

    async function procesarArchivoGuia(file) {
        if (alertContainerGuia) alertContainerGuia.innerHTML = '';
        const formData = new FormData();
        formData.append('archivo', file);
        formData.append('csrfmiddlewaretoken', config.csrfToken);

        if (dragZone) {
            dragZone.innerHTML = `
                <div class="spinner-border text-fs-yellow mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
                <h4 class="fw-bold">Analizando archivo...</h4>
                <p class="text-muted">Extrayendo ítems e identificando coincidencias en catálogo</p>
            `;
        }

        try {
            const response = await fetch(config.urls.analizarGuia, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (dragZone) {
                dragZone.innerHTML = `
                    <input type="file" id="guia-file-input" accept=".xml,.pdf" class="d-none">
                    <i class="bi bi-cloud-arrow-up-fill text-fs-grey mb-3" style="font-size: 4rem;"></i>
                    <h4 class="fw-bold">Arrastra tu guía de abastecimiento aquí</h4>
                    <p class="text-muted">Soporta archivos de formato XML (DTE) y PDF (Facturas o Guías de Traslado)</p>
                    <button type="button" class="btn btn-fs-yellow px-4 py-2 mt-2" onclick="document.getElementById('guia-file-input').click();">
                        <i class="bi bi-folder2-open me-2"></i> Seleccionar Archivo
                    </button>
                `;
                const newFileInput = document.getElementById('guia-file-input');
                if (newFileInput) {
                    newFileInput.addEventListener('change', (e) => {
                        if (newFileInput.files.length) {
                            procesarArchivoGuia(newFileInput.files[0]);
                        }
                    });
                }
            }

            if (!response.ok || !data.exito) {
                showAlertGuia(data.mensaje || 'Error al analizar el archivo de guía.');
                return;
            }

            if (passo1) passo1.classList.add('d-none');
            if (passo2) passo2.classList.remove('d-none');
            if (btnAtras) btnAtras.classList.remove('d-none');
            if (btnConfirmar) btnConfirmar.classList.remove('d-none');
            if (btnCancelar) btnCancelar.classList.add('d-none');

            if (data.folio && inputFolio) {
                inputFolio.value = data.folio;
            }

            if (tablaItemsBody) {
                tablaItemsBody.innerHTML = '';
                if (data.items && data.items.length > 0) {
                    data.items.forEach(item => {
                        agregarFilaItem(item);
                    });
                } else {
                    showAlertGuia('No se encontraron ítems en el documento. Puedes agregarlos de forma manual.', 'warning');
                }
            }

        } catch (error) {
            console.error(error);
            showAlertGuia('Error de red al comunicarse con el servidor.');
        }
    }

    if (btnAgregarItem) {
        btnAgregarItem.addEventListener('click', () => {
            agregarFilaItem({
                codigo_origen: '',
                descripcion_origen: '',
                cantidad: 1,
                producto_id: null,
                producto_codigo: null,
                producto_descripcion: null
            });
        });
    }

    function agregarFilaItem(item) {
        if (!tablaItemsBody) return;
        
        const tr = document.createElement('tr');
        tr.className = 'item-fila';

        const tdCodigo = document.createElement('td');
        tdCodigo.textContent = item.codigo_origen || '-';
        tr.appendChild(tdCodigo);

        const tdDesc = document.createElement('td');
        tdDesc.textContent = item.descripcion_origen || 'Ingresado manualmente';
        tr.appendChild(tdDesc);

        const tdSelector = document.createElement('td');
        
        const searchContainer = document.createElement('div');
        searchContainer.className = 'position-relative product-search-container';
        
        const inputSearch = document.createElement('input');
        inputSearch.type = 'text';
        inputSearch.className = 'form-control form-control-sm search-input';
        inputSearch.placeholder = 'Escriba código o descripción...';
        inputSearch.autocomplete = 'off';

        const hiddenId = document.createElement('input');
        hiddenId.type = 'hidden';
        hiddenId.className = 'product-id-val';
        
        if (item.producto_id) {
            hiddenId.value = item.producto_id;
            inputSearch.value = `${item.producto_codigo} - ${item.producto_descripcion}`;
            inputSearch.classList.add('is-valid');
        } else {
            inputSearch.classList.add('is-invalid');
        }

        const resultsDropdown = document.createElement('div');
        resultsDropdown.className = 'product-results-dropdown d-none position-absolute w-100 shadow-lg';

        searchContainer.appendChild(inputSearch);
        searchContainer.appendChild(hiddenId);
        searchContainer.appendChild(resultsDropdown);
        tdSelector.appendChild(searchContainer);
        tr.appendChild(tdSelector);

        const tdCant = document.createElement('td');
        tdCant.className = 'text-end';
        const inputCant = document.createElement('input');
        inputCant.type = 'number';
        inputCant.className = 'form-control form-control-sm text-end quantity-input';
        inputCant.value = item.cantidad || 1;
        inputCant.min = '1';
        inputCant.step = '1';
        tdCant.appendChild(inputCant);
        tr.appendChild(tdCant);

        const tdDel = document.createElement('td');
        tdDel.className = 'text-center';
        const btnDel = document.createElement('button');
        btnDel.type = 'button';
        btnDel.className = 'btn btn-sm btn-outline-danger';
        btnDel.innerHTML = '<i class="bi bi-trash"></i>';
        btnDel.addEventListener('click', () => {
            tr.remove();
        });
        tdDel.appendChild(btnDel);
        tr.appendChild(tdDel);

        inputSearch.addEventListener('focus', () => {
            mostrarResultados(inputSearch.value, resultsDropdown, inputSearch, hiddenId);
        });

        inputSearch.addEventListener('input', () => {
            mostrarResultados(inputSearch.value, resultsDropdown, inputSearch, hiddenId);
        });

        document.addEventListener('click', (e) => {
            if (!searchContainer.contains(e.target)) {
                resultsDropdown.classList.add('d-none');
                
                const matched = allProducts.find(p => `${p.codigo} - ${p.descripcion}`.toLowerCase() === inputSearch.value.toLowerCase().trim());
                if (matched) {
                    hiddenId.value = matched.id;
                    inputSearch.value = `${matched.codigo} - ${matched.descripcion}`;
                    inputSearch.classList.remove('is-invalid');
                    inputSearch.classList.add('is-valid');
                } else if (!inputSearch.value.trim()) {
                    hiddenId.value = '';
                    inputSearch.classList.remove('is-valid');
                    inputSearch.classList.add('is-invalid');
                }
            }
        });

        tablaItemsBody.appendChild(tr);
    }

    function mostrarResultados(query, dropdown, inputEl, hiddenEl) {
        dropdown.innerHTML = '';
        const q = query.toLowerCase().trim();
        const words = q.split(/\s+/).filter(w => w.length > 0);
        
        let filtered = [];
        if (words.length === 0) {
            filtered = allProducts.slice(0, 10);
        } else {
            filtered = allProducts.filter(p => {
                const searchStr = `${p.codigo} ${p.descripcion}`.toLowerCase();
                return words.every(w => searchStr.includes(w));
            });
            filtered = filtered.slice(0, 15);
        }

        if (filtered.length === 0) {
            const noRes = document.createElement('div');
            noRes.className = 'text-muted p-2 small text-center';
            noRes.textContent = 'Sin coincidencias en catálogo. Cree el producto en inventario si es nuevo.';
            dropdown.appendChild(noRes);
        } else {
            filtered.forEach(p => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'dropdown-item px-3 py-2 border-bottom';
                itemDiv.innerHTML = `<strong>${p.codigo}</strong> - ${p.descripcion}`;
                itemDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    inputEl.value = `${p.codigo} - ${p.descripcion}`;
                    hiddenEl.value = p.id;
                    inputEl.classList.remove('is-invalid');
                    inputEl.classList.add('is-valid');
                    dropdown.classList.add('d-none');
                });
                dropdown.appendChild(itemDiv);
            });
        }
        dropdown.classList.remove('d-none');
    }

    if (btnConfirmar) {
        btnConfirmar.addEventListener('click', async () => {
            if (alertContainerGuia) alertContainerGuia.innerHTML = '';
            const folioVal = inputFolio ? inputFolio.value.trim() : '';
            if (!folioVal) {
                showAlertGuia('El Folio / Número de guía es requerido.');
                if (inputFolio) inputFolio.focus();
                return;
            }

            const filas = tablaItemsBody ? tablaItemsBody.querySelectorAll('.item-fila') : [];
            if (filas.length === 0) {
                showAlertGuia('Debe haber al menos un ítem para poder ingresar la guía.');
                return;
            }

            const itemsToSend = [];
            let validationFailed = false;

            for (let i = 0; i < filas.length; i++) {
                const fila = filas[i];
                const searchInput = fila.querySelector('.search-input');
                const productIdVal = fila.querySelector('.product-id-val').value;
                const quantityVal = fila.querySelector('.quantity-input').value;
                const descFila = fila.children[1].textContent;

                if (!productIdVal) {
                    showAlertGuia(`El ítem en la fila ${i+1} ("${descFila}") no tiene un producto del catálogo asociado.`);
                    if (searchInput) {
                        searchInput.focus();
                        searchInput.classList.add('is-invalid');
                    }
                    validationFailed = true;
                    break;
                }

                const q = parseInt(quantityVal);
                if (isNaN(q) || q <= 0) {
                    showAlertGuia(`La cantidad del ítem en la fila ${i+1} debe ser un entero positivo.`);
                    fila.querySelector('.quantity-input').focus();
                    validationFailed = true;
                    break;
                }

                itemsToSend.push({
                    producto_id: parseInt(productIdVal),
                    cantidad: q,
                    descripcion_origen: descFila
                });
            }

            if (validationFailed) return;

            btnConfirmar.disabled = true;
            btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Procesando...';

            try {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : config.csrfToken;
                const response = await fetch(config.urls.procesarGuia, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        folio: parseInt(folioVal),
                        items: itemsToSend
                    })
                });

                const data = await response.json();

                if (response.ok && data.exito) {
                    window.location.reload();
                } else {
                    showAlertGuia(data.mensaje || 'Error al procesar la guía de abastecimiento.');
                    btnConfirmar.disabled = false;
                    btnConfirmar.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar e Incrementar Stock';
                }
            } catch (error) {
                console.error(error);
                showAlertGuia('Error de red al intentar guardar los datos.');
                btnConfirmar.disabled = false;
                btnConfirmar.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar e Incrementar Stock';
            }
        });
    }

    // --- LÓGICA DE DETALLE DE GUÍAS DE ABASTECIMIENTO ---
    const guiasDetalles = config.guiasDetalles || {};

    const modalDetalleGuiaEl = document.getElementById('modal-detalle-guia');
    const modalDetalleGuia = modalDetalleGuiaEl ? new bootstrap.Modal(modalDetalleGuiaEl) : null;
    const detGuiaFolio = document.getElementById('det-guia-folio');
    const detGuiaFecha = document.getElementById('det-guia-fecha');
    const detGuiaUsuario = document.getElementById('det-guia-usuario');
    const detGuiaTablaItems = document.getElementById('det-guia-tabla-items');

    document.querySelectorAll('.btn-ver-detalle-guia').forEach(btn => {
        btn.addEventListener('click', function() {
            const guiaId = this.getAttribute('data-guia-id');
            const row = this.closest('tr');
            const folio = row.cells[0].textContent;
            const fecha = row.cells[1].textContent;
            const usuario = row.cells[2].textContent;

            if (detGuiaFolio) detGuiaFolio.textContent = folio;
            if (detGuiaFecha) detGuiaFecha.textContent = fecha;
            if (detGuiaUsuario) detGuiaUsuario.textContent = usuario;

            if (detGuiaTablaItems) {
                detGuiaTablaItems.innerHTML = '';
                const details = guiasDetalles[guiaId] || [];
                details.forEach(item => {
                    const tr = document.createElement('tr');
                    
                    const tdCod = document.createElement('td');
                    tdCod.innerHTML = `<strong>${item.codigo}</strong>`;
                    tr.appendChild(tdCod);
                    
                    const tdDesc = document.createElement('td');
                    tdDesc.textContent = item.descripcion;
                    tr.appendChild(tdDesc);
                    
                    const tdCant = document.createElement('td');
                    tdCant.className = 'text-end fw-bold';
                    tdCant.textContent = item.cantidad;
                    tr.appendChild(tdCant);
                    
                    detGuiaTablaItems.appendChild(tr);
                });
            }

            if (modalDetalleGuia) {
                modalDetalleGuia.show();
            }
        });
    });

    const buscarGuiasInput = document.getElementById('buscar-guias');
    const tablaGuiasBody = document.getElementById('tabla-guias');
    const guiasFilas = tablaGuiasBody ? tablaGuiasBody.querySelectorAll('.guia-row') : [];

    if (buscarGuiasInput) {
        buscarGuiasInput.addEventListener('input', function() {
            const termino = this.value.toLowerCase().trim();
            const palabras = termino.split(/\s+/).filter(p => p.length > 0);

            guiasFilas.forEach(fila => {
                const textoFila = fila.textContent.toLowerCase();
                if (termino === '') {
                    fila.style.display = '';
                } else {
                    const todasPalabrasEncontradas = palabras.every(palabra => textoFila.includes(palabra));
                    fila.style.display = todasPalabrasEncontradas ? '' : 'none';
                }
            });
        });
    }

    // --- LÓGICA DE IMPORTACIÓN DE INVENTARIO DESDE EXCEL ---
    const modalExcelEl = document.getElementById('modal-importar-excel');
    const dragZoneExcel = document.getElementById('excel-paso-1');
    const fileInputExcel = document.getElementById('excel-file-input');
    
    const paso1Excel = document.getElementById('excel-paso-1');
    const paso2Excel = document.getElementById('excel-paso-2');
    const paso3Excel = document.getElementById('excel-paso-3');
    
    const btnAtrasExcel = document.getElementById('btn-excel-atras');
    const btnConfirmarExcel = document.getElementById('btn-excel-confirmar');
    const btnCancelarExcel = document.getElementById('btn-excel-cancelar');
    const btnFinalizarExcel = document.getElementById('btn-excel-finalizar');
    const btnCerrarModalExcel = document.getElementById('btn-cerrar-modal-excel');
    
    const selectMapCodigo = document.getElementById('excel-map-codigo');
    const selectMapActual = document.getElementById('excel-map-actual');
    const selectMapReal = document.getElementById('excel-map-real');
    const selectMapMinimo = document.getElementById('excel-map-minimo');
    const selectMapSistema = document.getElementById('excel-map-sistema');
    
    const previewHead = document.getElementById('excel-preview-head');
    const previewBody = document.getElementById('excel-preview-body');
    const alertContainerExcel = document.getElementById('excel-alert-container');
    
    const resResumen = document.getElementById('excel-res-resumen');
    const containerOmitidos = document.getElementById('excel-container-omitidos');
    const listOmitidos = document.getElementById('excel-list-omitidos');

    let excelFileObject = null;
    let excelTotalFilas = 0;

    if (modalExcelEl) {
        modalExcelEl.addEventListener('hidden.bs.modal', () => {
            resetModalExcel();
        });
    }

    function resetModalExcel() {
        excelFileObject = null;
        excelTotalFilas = 0;
        if (fileInputExcel) fileInputExcel.value = '';
        if (alertContainerExcel) alertContainerExcel.innerHTML = '';
        if (previewHead) previewHead.innerHTML = '';
        if (previewBody) previewBody.innerHTML = '';
        if (selectMapCodigo) selectMapCodigo.innerHTML = '';
        if (selectMapActual) selectMapActual.innerHTML = '';
        if (selectMapReal) selectMapReal.innerHTML = '';
        if (selectMapMinimo) selectMapMinimo.innerHTML = '';
        if (selectMapSistema) selectMapSistema.innerHTML = '';
        
        if (paso1Excel) paso1Excel.classList.remove('d-none');
        if (paso2Excel) paso2Excel.classList.add('d-none');
        if (paso3Excel) paso3Excel.classList.add('d-none');
        
        const pasoProcesando = document.getElementById('excel-paso-procesando');
        if (pasoProcesando) pasoProcesando.classList.add('d-none');
        
        if (btnAtrasExcel) btnAtrasExcel.classList.add('d-none');
        if (btnConfirmarExcel) btnConfirmarExcel.classList.add('d-none');
        if (btnFinalizarExcel) btnFinalizarExcel.classList.add('d-none');
        if (btnCancelarExcel) btnCancelarExcel.classList.remove('d-none');
        if (btnCerrarModalExcel) btnCerrarModalExcel.classList.remove('d-none');
    }

    if (dragZoneExcel) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dragZoneExcel.addEventListener(eventName, (e) => {
                e.preventDefault();
                dragZoneExcel.style.backgroundColor = 'var(--sidebar-hover-bg)';
                dragZoneExcel.style.borderColor = 'var(--fs-yellow)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dragZoneExcel.addEventListener(eventName, (e) => {
                e.preventDefault();
                dragZoneExcel.style.backgroundColor = '';
                dragZoneExcel.style.borderColor = '';
            }, false);
        });

        dragZoneExcel.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                analizarArchivoExcel(files[0]);
            }
        });
    }

    if (fileInputExcel) {
        fileInputExcel.addEventListener('change', (e) => {
            if (fileInputExcel.files.length) {
                analizarArchivoExcel(fileInputExcel.files[0]);
            }
        });
    }

    if (btnAtrasExcel) {
        btnAtrasExcel.addEventListener('click', () => {
            resetModalExcel();
        });
    }

    function showAlertExcel(msg, type = 'danger') {
        if (alertContainerExcel) {
            alertContainerExcel.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${msg}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        }
    }

    async function analizarArchivoExcel(file) {
        if (alertContainerExcel) alertContainerExcel.innerHTML = '';
        excelFileObject = file;
        const formData = new FormData();
        formData.append('archivo', file);
        formData.append('csrfmiddlewaretoken', config.csrfToken);

        if (dragZoneExcel) {
            dragZoneExcel.innerHTML = `
                <div class="spinner-border text-success mb-3" style="width: 3rem; height: 3rem;" role="status"></div>
                <h4 class="fw-bold">Analizando archivo Excel...</h4>
                <p class="text-muted">Cargando hojas y extrayendo cabeceras de columnas</p>
            `;
        }

        try {
            const response = await fetch(config.urls.analizarExcel, {
                method: 'POST',
                body: formData
            });

            if (dragZoneExcel) {
                dragZoneExcel.innerHTML = `
                    <input type="file" id="excel-file-input" accept=".xlsx,.xls" class="d-none">
                    <i class="bi bi-file-earmark-excel-fill text-success mb-3" style="font-size: 4rem;"></i>
                    <h4 class="fw-bold">Arrastra tu archivo Excel aquí</h4>
                    <p class="text-muted">Soporta formatos .xlsx y .xls (Hoja 1, fila 1 cabeceras)</p>
                    <button type="button" class="btn btn-success px-4 py-2 mt-2" onclick="document.getElementById('excel-file-input').click();">
                        <i class="bi bi-folder2-open me-2"></i> Seleccionar Archivo
                    </button>
                `;
                const newFileInputExcel = document.getElementById('excel-file-input');
                if (newFileInputExcel) {
                    newFileInputExcel.addEventListener('change', (e) => {
                        if (newFileInputExcel.files.length) {
                            analizarArchivoExcel(newFileInputExcel.files[0]);
                        }
                    });
                }
            }

            let data = null;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            }

            if (!response.ok) {
                const msg = (data && data.mensaje) ? data.mensaje : `Error del servidor (Código de estado: ${response.status})`;
                showAlertExcel(msg);
                return;
            }

            if (!data || !data.exito) {
                showAlertExcel((data && data.mensaje) || 'Error al analizar el archivo de Excel.');
                return;
            }

            excelTotalFilas = data.total_filas || 0;

            if (paso1Excel) paso1Excel.classList.add('d-none');
            if (paso2Excel) paso2Excel.classList.remove('d-none');
            if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
            if (btnConfirmarExcel) btnConfirmarExcel.classList.remove('d-none');
            if (btnCancelarExcel) btnCancelarExcel.classList.add('d-none');

            populateExcelDropdowns(data.columnas);
            renderExcelPreview(data.columnas, data.vista_previa);

        } catch (error) {
            console.error(error);
            showAlertExcel(`Error de red al comunicarse con el servidor: ${error.message || error}`);
        }
    }

    function populateExcelDropdowns(columnas) {
        if (selectMapCodigo) selectMapCodigo.innerHTML = '';
        if (selectMapActual) selectMapActual.innerHTML = '';
        if (selectMapReal) selectMapReal.innerHTML = '';
        if (selectMapMinimo) selectMapMinimo.innerHTML = '';
        if (selectMapSistema) selectMapSistema.innerHTML = '';

        const addOption = (selectEl, text, val) => {
            if (!selectEl) return;
            const opt = document.createElement('option');
            opt.textContent = text;
            opt.value = val;
            selectEl.appendChild(opt);
        };

        if (selectMapActual) addOption(selectMapActual, '-- No importar --', '');
        if (selectMapReal) addOption(selectMapReal, '-- No importar --', '');
        if (selectMapMinimo) addOption(selectMapMinimo, '-- No importar --', '');
        if (selectMapSistema) addOption(selectMapSistema, '-- No importar --', '');

        columnas.forEach(col => {
            if (selectMapCodigo) addOption(selectMapCodigo, col, col);
            if (selectMapActual) addOption(selectMapActual, col, col);
            if (selectMapReal) addOption(selectMapReal, col, col);
            if (selectMapMinimo) addOption(selectMapMinimo, col, col);
            if (selectMapSistema) addOption(selectMapSistema, col, col);
        });

        const colCodigoDefault = columnas.find(c => ['cod. producto', 'codigo', 'sku', 'cod_producto', 'codigo opendte_config'].includes(c.toLowerCase().trim()));
        if (colCodigoDefault) {
            selectMapCodigo.value = colCodigoDefault;
        }

        const colActualDefault = columnas.find(c => ['principal', 'stock principal', 'temuco', 'stock temuco', 'cantidad', 'stock_actual', 'contabilizado', 'real', 'fisico', 'stock_real', 'stock real'].includes(c.toLowerCase().trim()));
        if (colActualDefault && selectMapActual) {
            selectMapActual.value = colActualDefault;
        }

        const colRealDefault = columnas.find(c => ['contabilizado', 'real', 'fisico', 'stock_real', 'stock real'].includes(c.toLowerCase().trim()));
        if (colRealDefault && selectMapReal) {
            selectMapReal.value = colRealDefault;
        }

        const colMinimoDefault = columnas.find(c => ['minimo reposicion', 'minimo', 'stock_minimo', 'mínimo'].includes(c.toLowerCase().trim()));
        if (colMinimoDefault && selectMapMinimo) {
            selectMapMinimo.value = colMinimoDefault;
        }

        const colSistemaDefault = columnas.find(c => ['sistema', 'sistema opendte_config', 'opendte_config', 'stock_sistema', 'stock sistema'].includes(c.toLowerCase().trim()));
        if (colSistemaDefault && selectMapSistema) {
            selectMapSistema.value = colSistemaDefault;
        }
    }

    function renderExcelPreview(columnas, rows) {
        if (!previewHead || !previewBody) return;

        previewHead.innerHTML = '';
        columnas.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            previewHead.appendChild(th);
        });

        previewBody.innerHTML = '';
        rows.forEach(row => {
            const tr = document.createElement('tr');
            columnas.forEach(col => {
                const td = document.createElement('td');
                const val = row[col];
                td.textContent = (val !== null && val !== undefined) ? val : '';
                tr.appendChild(td);
            });
            previewBody.appendChild(tr);
        });
    }

    if (btnConfirmarExcel) {
        btnConfirmarExcel.addEventListener('click', async () => {
            if (alertContainerExcel) alertContainerExcel.innerHTML = '';

            const colCodigo = selectMapCodigo.value;
            const colActual = selectMapActual.value;
            const colReal = selectMapReal ? selectMapReal.value : '';
            const colMinimo = selectMapMinimo.value;
            const colSistema = selectMapSistema ? selectMapSistema.value : '';
            
            if (!colActual && !colReal && !colMinimo && !colSistema) {
                showAlertExcel('Debes seleccionar al menos una columna de stock para importar (Stock Principal, Mínimo o Sistema ERP).', 'warning');
                return;
            }

            const mappedCols = [colCodigo, colActual, colReal, colMinimo, colSistema].filter(c => c !== '');
            const colSet = new Set(mappedCols);
            if (colSet.size !== mappedCols.length) {
                showAlertExcel('No puedes asignar la misma columna de Excel a más de un campo del sistema.', 'warning');
                return;
            }

            const radioNonNumeric = document.querySelector('input[name="excel-no-numericos"]:checked');
            const nonNumericOption = radioNonNumeric ? radioNonNumeric.value : 'mantener';

            const formData = new FormData();
            formData.append('archivo', excelFileObject);
            formData.append('columna_codigo', colCodigo);
            formData.append('columna_stock_actual', colActual);
            formData.append('columna_stock_real', colReal);
            formData.append('columna_stock_minimo', colMinimo);
            formData.append('columna_stock_sistema', colSistema);
            formData.append('opcion_no_numericos', nonNumericOption);
            formData.append('csrfmiddlewaretoken', config.csrfToken);

            const pasoProcesando = document.getElementById('excel-paso-procesando');
            const progressBar = document.getElementById('excel-progress-bar');
            const progressTitle = document.getElementById('excel-progress-title');
            const progressDetail = document.getElementById('excel-progress-detail');

            if (paso2Excel) paso2Excel.classList.add('d-none');
            if (pasoProcesando) pasoProcesando.classList.remove('d-none');

            if (btnConfirmarExcel) btnConfirmarExcel.classList.add('d-none');
            if (btnAtrasExcel) btnAtrasExcel.classList.add('d-none');
            if (btnCancelarExcel) btnCancelarExcel.classList.add('d-none');
            if (btnCerrarModalExcel) btnCerrarModalExcel.classList.add('d-none');

            progressBar.style.width = '0%';
            progressTitle.textContent = 'Procesando importación...';
            
            const totalFilas = excelTotalFilas || 100;
            const duration = 1200; // Duración estimada en ms para la animación
            const intervalTime = 40;
            const steps = duration / intervalTime;
            const rowsPerStep = Math.ceil(totalFilas / steps);
            
            let currentFilas = 0;
            let progress = 0;
            
            const timer = setInterval(() => {
                progress += (95 / steps);
                currentFilas += rowsPerStep;
                if (currentFilas > totalFilas * 0.95) {
                    currentFilas = Math.floor(totalFilas * 0.95);
                }
                
                progressBar.style.width = `${Math.min(95, Math.round(progress))}%`;
                progressDetail.textContent = `Procesando filas: ${currentFilas} de ${totalFilas} (${Math.min(95, Math.round(progress))}%)`;
                
                if (progress >= 95) {
                    clearInterval(timer);
                }
            }, intervalTime);

            try {
                const response = await fetch(config.urls.procesarExcel, {
                    method: 'POST',
                    body: formData
                });

                let data = null;
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    data = await response.json();
                }

                clearInterval(timer);

                if (!response.ok) {
                    const msg = (data && data.mensaje) ? data.mensaje : `Error del servidor (Código de estado: ${response.status})`;
                    showAlertExcel(msg);
                    
                    if (pasoProcesando) pasoProcesando.classList.add('d-none');
                    if (paso2Excel) paso2Excel.classList.remove('d-none');
                    
                    if (btnConfirmarExcel) {
                        btnConfirmarExcel.classList.remove('d-none');
                        btnConfirmarExcel.disabled = false;
                        btnConfirmarExcel.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar y Reemplazar Stock';
                    }
                    if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
                    if (btnCancelarExcel) btnCancelarExcel.classList.remove('d-none');
                    if (btnCerrarModalExcel) btnCerrarModalExcel.classList.remove('d-none');
                    return;
                }

                if (!data || !data.exito) {
                    showAlertExcel((data && data.mensaje) || 'Ocurrió un error al procesar el archivo Excel.');
                    
                    if (pasoProcesando) pasoProcesando.classList.add('d-none');
                    if (paso2Excel) paso2Excel.classList.remove('d-none');
                    
                    if (btnConfirmarExcel) {
                        btnConfirmarExcel.classList.remove('d-none');
                        btnConfirmarExcel.disabled = false;
                        btnConfirmarExcel.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar y Reemplazar Stock';
                    }
                    if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
                    if (btnCancelarExcel) btnCancelarExcel.classList.remove('d-none');
                    if (btnCerrarModalExcel) btnCerrarModalExcel.classList.remove('d-none');
                    return;
                }

                // Éxito: Completar la barra
                progressBar.style.width = '100%';
                progressDetail.textContent = `Procesando filas: ${totalFilas} de ${totalFilas} (100%)`;
                progressTitle.textContent = '¡Importación completada!';

                // Esperar 400ms para mostrar transición al 100%
                await new Promise(resolve => setTimeout(resolve, 400));

                if (pasoProcesando) pasoProcesando.classList.add('d-none');
                if (paso3Excel) paso3Excel.classList.remove('d-none');
                
                if (btnConfirmarExcel) btnConfirmarExcel.classList.add('d-none');
                if (btnAtrasExcel) btnAtrasExcel.classList.add('d-none');
                if (btnCancelarExcel) btnCancelarExcel.classList.add('d-none');
                if (btnCerrarModalExcel) btnCerrarModalExcel.classList.add('d-none');
                if (btnFinalizarExcel) btnFinalizarExcel.classList.remove('d-none');

                if (resResumen) {
                    resResumen.textContent = `Se actualizaron correctamente ${data.actualizados} productos. Se omitieron ${data.omitidos} filas.`;
                }

                if (data.codigos_no_encontrados && data.codigos_no_encontrados.length > 0) {
                    if (containerOmitidos) containerOmitidos.classList.remove('d-none');
                    if (listOmitidos) {
                        listOmitidos.innerHTML = '';
                        data.codigos_no_encontrados.forEach(cod => {
                            const li = document.createElement('li');
                            li.className = 'col-sm-3 col-6 text-danger mb-1 font-monospace small';
                            li.innerHTML = `<i class="bi bi-x-circle me-1"></i>${cod}`;
                            listOmitidos.appendChild(li);
                        });
                    }
                } else {
                    if (containerOmitidos) containerOmitidos.classList.add('d-none');
                }

            } catch (error) {
                console.error(error);
                showAlertExcel(`Error de red al procesar el archivo: ${error.message || error}`);
                btnConfirmarExcel.disabled = false;
                btnConfirmarExcel.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar y Reemplazar Stock';
                if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
            }
        });
    }
});
