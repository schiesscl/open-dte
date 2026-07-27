/**
 * static/js/excel-import.js
 * Módulo para la importación y mapeo masivo de inventario desde Excel para OpenDTE.
 */

window.OpenDTEExcelImport = (function() {
    'use strict';

    function init(config) {
        const modalExcel = document.getElementById('modal-importar-excel');
        if (!modalExcel) return;

        const alertContainerExcel = document.getElementById('excel-alert-container');
        const dragZoneExcel = document.getElementById('excel-paso-1');
        const paso1Excel = document.getElementById('excel-paso-1');
        const paso2Excel = document.getElementById('excel-paso-2');
        const btnAtrasExcel = document.getElementById('btn-excel-atras');
        const btnConfirmarExcel = document.getElementById('btn-excel-confirmar');
        const btnCancelarExcel = document.getElementById('btn-excel-cancelar');
        const btnCerrarModalExcel = document.getElementById('btn-cerrar-modal-excel');
        const fileInputExcel = document.getElementById('excel-file-input');

        const selectMapCodigo = document.getElementById('excel-map-codigo');
        const selectMapActual = document.getElementById('excel-map-actual');
        const selectMapReal = document.getElementById('excel-map-real');
        const selectMapMinimo = document.getElementById('excel-map-minimo');
        const selectMapSistema = document.getElementById('excel-map-sistema');

        const previewHead = document.getElementById('excel-preview-head');
        const previewBody = document.getElementById('excel-preview-body');

        let excelFileObject = null;
        let excelTotalFilas = 0;

        function showAlert(mensaje, tipo = 'danger') {
            if (!alertContainerExcel) return;
            alertContainerExcel.innerHTML = `
                <div class="alert alert-${tipo} alert-dismissible fade show shadow-sm" role="alert">
                    <i class="bi bi-${tipo === 'danger' ? 'exclamation-octagon-fill' : 'exclamation-triangle-fill'} me-2"></i>
                    ${mensaje}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            alertContainerExcel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function resetModal() {
            excelFileObject = null;
            excelTotalFilas = 0;
            if (alertContainerExcel) alertContainerExcel.innerHTML = '';

            const pasoProcesando = document.getElementById('excel-paso-procesando');
            if (pasoProcesando) pasoProcesando.classList.add('d-none');

            if (paso1Excel) paso1Excel.classList.remove('d-none');
            if (paso2Excel) paso2Excel.classList.add('d-none');
            if (btnAtrasExcel) btnAtrasExcel.classList.add('d-none');
            if (btnConfirmarExcel) {
                btnConfirmarExcel.classList.add('d-none');
                btnConfirmarExcel.disabled = false;
                btnConfirmarExcel.innerHTML = '<i class="bi bi-check2-all me-1"></i> Confirmar y Reemplazar Stock';
            }
            if (btnCancelarExcel) btnCancelarExcel.classList.remove('d-none');
            if (btnCerrarModalExcel) btnCerrarModalExcel.classList.remove('d-none');

            if (fileInputExcel) fileInputExcel.value = '';

            const defaultRadio = document.getElementById('excel-opt-mantener');
            if (defaultRadio) defaultRadio.checked = true;

            const radioNonNumeric = document.querySelector('input[name="excel-no-numericos"][value="mantener"]');
            if (radioNonNumeric) radioNonNumeric.checked = true;
        }

        modalExcel.addEventListener('hidden.bs.modal', resetModal);

        if (btnAtrasExcel) {
            btnAtrasExcel.addEventListener('click', resetModal);
        }

        if (fileInputExcel) {
            fileInputExcel.addEventListener('change', (e) => {
                if (e.target.files && e.target.files.length) {
                    analizarArchivo(e.target.files[0]);
                }
            });
        }

        if (dragZoneExcel) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dragZoneExcel.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                dragZoneExcel.addEventListener(eventName, () => {
                    dragZoneExcel.classList.add('bg-light');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dragZoneExcel.addEventListener(eventName, () => {
                    dragZoneExcel.classList.remove('bg-light');
                }, false);
            });

            dragZoneExcel.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;

                if (files && files.length) {
                    const file = files[0];
                    const ext = file.name.split('.').pop().toLowerCase();
                    if (ext === 'xlsx' || ext === 'xls') {
                        analizarArchivo(file);
                    } else {
                        showAlert('Formato de archivo no soportado. Por favor sube un archivo Excel (.xlsx o .xls).');
                    }
                }
            });
        }

        async function analizarArchivo(file) {
            excelFileObject = file;
            if (alertContainerExcel) alertContainerExcel.innerHTML = '';

            const formData = new FormData();
            formData.append('archivo', file);
            formData.append('csrfmiddlewaretoken', config.csrfToken);

            try {
                const response = await fetch(config.urls.analizarExcel, {
                    method: 'POST',
                    body: formData
                });

                let data = null;
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    data = await response.json();
                }

                if (!response.ok || !data || !data.exito) {
                    showAlert((data && data.mensaje) || `Error al analizar el archivo de Excel (${response.status})`);
                    return;
                }

                excelTotalFilas = data.total_filas || 0;

                if (paso1Excel) paso1Excel.classList.add('d-none');
                if (paso2Excel) paso2Excel.classList.remove('d-none');
                if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
                if (btnConfirmarExcel) btnConfirmarExcel.classList.remove('d-none');

                populateDropdowns(data.columnas);
                renderPreview(data.columnas, data.vista_previa);

            } catch (error) {
                console.error(error);
                showAlert(`Error de red al comunicarse con el servidor: ${error.message || error}`);
            }
        }

        function populateDropdowns(columnas) {
            const addOption = (selectEl, text, val) => {
                if (!selectEl) return;
                const opt = document.createElement('option');
                opt.textContent = text;
                opt.value = val;
                selectEl.appendChild(opt);
            };

            [selectMapCodigo, selectMapActual, selectMapReal, selectMapMinimo, selectMapSistema].forEach(sel => {
                if (sel) sel.innerHTML = '';
            });

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

            const colCodigoDefault = columnas.find(c => ['cod. producto', 'codigo', 'sku', 'cod_producto'].includes(c.toLowerCase().trim()));
            if (colCodigoDefault && selectMapCodigo) selectMapCodigo.value = colCodigoDefault;

            const colActualDefault = columnas.find(c => ['principal', 'stock principal', 'temuco', 'stock temuco', 'cantidad', 'stock_actual'].includes(c.toLowerCase().trim()));
            if (colActualDefault && selectMapActual) selectMapActual.value = colActualDefault;

            const colRealDefault = columnas.find(c => ['contabilizado', 'real', 'fisico', 'stock_real', 'stock real'].includes(c.toLowerCase().trim()));
            if (colRealDefault && selectMapReal) selectMapReal.value = colRealDefault;

            const colMinimoDefault = columnas.find(c => ['minimo reposicion', 'minimo', 'stock_minimo', 'mínimo'].includes(c.toLowerCase().trim()));
            if (colMinimoDefault && selectMapMinimo) selectMapMinimo.value = colMinimoDefault;

            const colSistemaDefault = columnas.find(c => ['sistema', 'stock_sistema', 'stock sistema'].includes(c.toLowerCase().trim()));
            if (colSistemaDefault && selectMapSistema) selectMapSistema.value = colSistemaDefault;
        }

        function renderPreview(columnas, rows) {
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

                const colCodigo = selectMapCodigo ? selectMapCodigo.value : '';
                const colActual = selectMapActual ? selectMapActual.value : '';
                const colReal = selectMapReal ? selectMapReal.value : '';
                const colMinimo = selectMapMinimo ? selectMapMinimo.value : '';
                const colSistema = selectMapSistema ? selectMapSistema.value : '';

                if (!colActual && !colReal && !colMinimo && !colSistema) {
                    showAlert('Debes seleccionar al menos una columna de stock para importar (Stock Principal, Mínimo o Sistema ERP).', 'warning');
                    return;
                }

                const mappedCols = [colCodigo, colActual, colReal, colMinimo, colSistema].filter(c => c !== '');
                const colSet = new Set(mappedCols);
                if (colSet.size !== mappedCols.length) {
                    showAlert('No puedes asignar la misma columna de Excel a más de un campo del sistema.', 'warning');
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

                if (progressBar) progressBar.style.width = '0%';
                if (progressTitle) progressTitle.textContent = 'Procesando importación...';

                const totalFilas = excelTotalFilas || 100;
                const duration = 1200;
                const intervalTime = 40;
                const steps = duration / intervalTime;
                const rowsPerStep = Math.ceil(totalFilas / steps);

                let currentFilas = 0;
                let progress = 0;

                const timer = setInterval(() => {
                    progress += (95 / steps);
                    currentFilas += rowsPerStep;
                    if (currentFilas > totalFilas * 0.95) currentFilas = Math.floor(totalFilas * 0.95);

                    if (progressBar) progressBar.style.width = `${Math.min(95, Math.round(progress))}%`;
                    if (progressDetail) progressDetail.textContent = `Procesando filas: ${currentFilas} de ${totalFilas} (${Math.min(95, Math.round(progress))}%)`;

                    if (progress >= 95) clearInterval(timer);
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

                    if (!response.ok || !data || !data.exito) {
                        showAlert((data && data.mensaje) || 'Ocurrió un error al procesar el archivo Excel.');
                        if (pasoProcesando) pasoProcesando.classList.add('d-none');
                        if (paso2Excel) paso2Excel.classList.remove('d-none');
                        if (btnConfirmarExcel) btnConfirmarExcel.classList.remove('d-none');
                        if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
                        return;
                    }

                    if (progressBar) progressBar.style.width = '100%';
                    if (progressTitle) progressTitle.textContent = '¡Importación completada con éxito!';
                    if (progressDetail) progressDetail.textContent = `Se procesaron correctamente ${data.total_procesados || 0} productos.`;

                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);

                } catch (error) {
                    clearInterval(timer);
                    console.error(error);
                    showAlert(`Error de red al procesar el Excel: ${error.message || error}`);
                    if (pasoProcesando) pasoProcesando.classList.add('d-none');
                    if (paso2Excel) paso2Excel.classList.remove('d-none');
                    if (btnConfirmarExcel) btnConfirmarExcel.classList.remove('d-none');
                    if (btnAtrasExcel) btnAtrasExcel.classList.remove('d-none');
                }
            });
        }
    }

    return {
        init: init
    };
})();
