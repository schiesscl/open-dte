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
                if (contentType?.includes("application/json")) {
                    data = await response.json();
                }

                if (!response.ok || !data?.exito) {
                    showAlert(data?.mensaje || `Error al analizar el archivo de Excel (${response.status})`);
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
                th.scope = 'col';
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

        function obtenerColumnasExcel() {
            return {
                columna_codigo: selectMapCodigo?.value || '',
                columna_stock_actual: selectMapActual?.value || '',
                columna_stock_real: selectMapReal?.value || '',
                columna_stock_minimo: selectMapMinimo?.value || '',
                columna_stock_sistema: selectMapSistema?.value || '',
            };
        }

        function validarColumnasExcel(columnas) {
            if (!columnas.columna_codigo) {
                showAlert('Debes seleccionar la columna del código de producto.', 'warning');
                return false;
            }
            if (!Object.entries(columnas).some(([key, value]) => key !== 'columna_codigo' && value)) {
                showAlert('Debes seleccionar al menos una columna de stock para importar.', 'warning');
                return false;
            }
            const asignadas = Object.values(columnas).filter(Boolean);
            if (new Set(asignadas).size !== asignadas.length) {
                showAlert('No puedes asignar la misma columna de Excel a más de un campo del sistema.', 'warning');
                return false;
            }
            return true;
        }

        function crearFormDataImportacion(columnas) {
            const formData = new FormData();
            formData.append('archivo', excelFileObject);
            Object.entries(columnas).forEach(([key, value]) => formData.append(key, value));
            formData.append('opcion_no_numericos', document.querySelector('input[name="excel-no-numericos"]:checked')?.value || 'mantener');
            formData.append('csrfmiddlewaretoken', config.csrfToken);
            return formData;
        }

        function mostrarProcesamientoExcel(procesando) {
            document.getElementById('excel-paso-procesando')?.classList.toggle('d-none', !procesando);
            [paso2Excel, btnConfirmarExcel, btnAtrasExcel].forEach(el => el?.classList.toggle('d-none', procesando));
        }

        function simularProgresoImportacion(progressBar, progressDetail) {
            const totalFilas = excelTotalFilas || 100;
            let progress = 0;
            const timer = setInterval(() => {
                progress = Math.min(95, progress + 95 / 30);
                if (progressBar) progressBar.style.width = `${Math.round(progress)}%`;
                if (progressDetail) progressDetail.textContent = `Procesando filas: ${Math.floor(totalFilas * progress / 100)} de ${totalFilas} (${Math.round(progress)}%)`;
                if (progress >= 95) clearInterval(timer);
            }, 40);
            return timer;
        }

        if (btnConfirmarExcel) {
            btnConfirmarExcel.addEventListener('click', async () => {
                if (alertContainerExcel) alertContainerExcel.innerHTML = '';
                const columnas = obtenerColumnasExcel();
                if (!validarColumnasExcel(columnas)) return;
                const formData = crearFormDataImportacion(columnas);

                const progressBar = document.getElementById('excel-progress-bar');
                const progressTitle = document.getElementById('excel-progress-title');
                const progressDetail = document.getElementById('excel-progress-detail');

                mostrarProcesamientoExcel(true);

                if (progressBar) progressBar.style.width = '0%';
                if (progressTitle) progressTitle.textContent = 'Procesando importación...';

                const timer = simularProgresoImportacion(progressBar, progressDetail);

                try {
                    const response = await fetch(config.urls.procesarExcel, {
                        method: 'POST',
                        body: formData
                    });

                    let data = null;
                    const contentType = response.headers.get("content-type");
                    if (contentType?.includes("application/json")) {
                        data = await response.json();
                    }

                    clearInterval(timer);

                    if (!response.ok || !data?.exito) {
                        showAlert(data?.mensaje || 'Ocurrió un error al procesar el archivo Excel.');
                        mostrarProcesamientoExcel(false);
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
                    mostrarProcesamientoExcel(false);
                }
            });
        }
    }

    return {
        init: init
    };
})();
