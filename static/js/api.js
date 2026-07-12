// Lógica de sincronización y conexión a la API
const ApiService = {
    // API Endpoints
    URLS: {
        clientes: '/api/clientes/',
        productos: '/api/productos/',
        facturas: '/api/facturas/',
        uploadFactura: '/api/upload-factura/'
    },

    /**
     * Lee las cookies para inyectar el CSRF Token a Django en llamadas POST/PUT
     */
    getCSRFToken: () => {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    },

    /**
     * Sincroniza datos maestros desde el servidor hacia la base de datos local (IndexedDB)
     */
    sincronizarDatosMaestros: async () => {
        if (!navigator.onLine) {
            console.log("Modo offline: Saltando sincronización maestra.");
            return;
        }
        
        try {
            // Sincronizar clientes
            const respClientes = await fetch(ApiService.URLS.clientes);
            if(respClientes.ok) {
                const clientes = await respClientes.json();
                await localforage.setItem('clientes', clientes);
            }
            
            // Sincronizar productos
            const respProductos = await fetch(ApiService.URLS.productos);
            if(respProductos.ok) {
                const productos = await respProductos.json();
                await localforage.setItem('productos', productos);
            }

            console.log("¡Datos maestros sincronizados correctamente para modo offline!");
        } catch (error) {
            console.error('Error sincronizando datos maestros:', error);
        }
    },

    /**
     * Se ejecuta periódicamente o al recuperar la conexión para mandar facturas encoladas
     */
    procesarColaFacturasOffline: async () => {
        if (window.isOfflineMode()) return; 
        
        const queue = await window.DB.obtenerQueueFacturas();
        if (queue.length === 0) return;

        console.log(`Procesando ${queue.length} facturas guardadas offline...`);

        let subidasCorrectamente = 0;
        let nuevas_colas = [];

        for (let task of queue) {
            try {
                let form = new FormData();
                form.append('archivo_factura', task.file, task.filename);

                const response = await fetch(ApiService.URLS.uploadFactura, {
                    method: 'POST',
                    body: form,
                    headers: { 'X-CSRFToken': ApiService.getCSRFToken() }
                });

                if (response.ok) {
                    subidasCorrectamente++;
                } else {
                    console.error("Fallo subida desde cola", response.status);
                    // Solo encolamos de nuevo si es error de servidor. Si es 400 (ej. duplicado), lo descartamos.
                    if (response.status >= 500) {
                        nuevas_colas.push(task); 
                    }
                }
            } catch (error) {
                console.error("Fallo de red en subida asíncrona", error);
                nuevas_colas.push(task); 
            }
        }
        
        await localforage.setItem('facturas_sync_queue', nuevas_colas);
        if (subidasCorrectamente > 0) {
            console.log(`¡${subidasCorrectamente} facturas subidas exitosamente de la cola offline!`);
            // Alertamos al UI con la nueva Notificación Flotante
            if(window.mostrarNotificacion) {
                window.mostrarNotificacion(`Sincronización: ${subidasCorrectamente} facturas locales subidas al servidor.`, "success");
            }
            setTimeout(() => { window.location.reload(); }, 3500);
        }
    }
};

// --- NUEVO: Función Global de Sincronización en Segundo Plano para Despachos ---
async function sincronizarDespachosOffline() {
    if (window.isOfflineMode()) return; // Si sigue offline cortamos
    
    // Obtener cola
    const cola = await window.DB.obtenerQueueDespachos();
    if (cola.length === 0) return;
    
    console.log(`Intentando sincronizar ${cola.length} despachos almacenados offline...`);
    
    let despachosSincronizados = 0;
    for (let despachoLocal of cola) {
        try {
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', despachoLocal.csrfToken);
            
            // Llamamos a la URL usando el ID guardado
            const response = await fetch(`/despacho/confirmar/${despachoLocal.factura_id}/`, {
                method: 'POST',
                body: formData,
                redirect: 'follow'
            });
            
            if (response.ok) {
                // Si el servidor lo recibió correctamente y actualizó la BD, lo quitamos de la cola
                console.log(`Despacho de factura ID: ${despachoLocal.factura_id} sincronizado.`);
                await window.DB.removerDespachoDeQueue(despachoLocal.id_temporal);
                despachosSincronizados++;
            }
        } catch (error) {
            console.error('Error al sincronizar despacho:', error);
            // Quedará en la cola para el próximo intento
        }
    }
    
    if (despachosSincronizados > 0) {
        // Opción: Notificar usuario que los despachos offline se enviaron a Gerencia usando Tostada
        if(window.mostrarNotificacion) {
            window.mostrarNotificacion(`Sincronización Automática: Se enviaron ${despachosSincronizados} despachos pendientes guardados sin internet.`, "success");
        }
        if(window.location.href.includes('historial') || window.location.href.includes('despacho')) {
            setTimeout(() => { window.location.reload(); }, 4000); 
        }
    }
}

// Listeners globales para conexión a la red
window.addEventListener('online', () => {
    console.log("Conexión recuperada. Sincronizando datos...");
    ApiService.sincronizarDatosMaestros();
    ApiService.procesarColaFacturasOffline();
    sincronizarDespachosOffline();
    sincronizarPeticionesGenericasOffline();
});

window.addEventListener('load', () => {
    // Al iniciar, intentar descargar listados (clientes/productos) y subir datos (Despachos)
    ApiService.sincronizarDatosMaestros();
    setTimeout(() => {
        ApiService.procesarColaFacturasOffline();
        sincronizarDespachosOffline();
        sincronizarPeticionesGenericasOffline();
    }, 3000); // 3 Segundos de margen para no trancar carga inicial
});

// --- NUEVO: Función Global de Sincronización para Cualquier Formulario ---
async function sincronizarPeticionesGenericasOffline() {
    if (window.isOfflineMode()) return;
    
    const cola = await window.DB.obtenerQueueGenerica();
    if (cola.length === 0) return;
    
    console.log(`Intentando sincronizar ${cola.length} peticiones genéricas almacenadas offline...`);
    
    let sincronizados = 0;
    for (let req of cola) {
        try {
            let options = {
                method: req.method,
                headers: req.headers || {},
                redirect: 'follow'
            };

            // Reconstruir FormData si es necesario
            if (req.isFormData && req.body) {
                const formData = new FormData();
                for (const key in req.body) {
                    formData.append(key, req.body[key]);
                }
                options.body = formData;
            } else if (req.body) {
                options.body = JSON.stringify(req.body);
                options.headers['Content-Type'] = 'application/json';
            }

            const response = await fetch(req.url, options);
            if (response.ok || response.type === 'opaqueredirect' || response.status < 400) {
                console.log(`Petición a ${req.url} sincronizada correctamente.`);
                await window.DB.removerPeticionGenerica(req.id_temporal);
                sincronizados++;
            }
        } catch (error) {
            console.error(`Error al sincronizar petición genérica (${req.url}):`, error);
        }
    }
    
    if (sincronizados > 0) {
        if(window.mostrarNotificacion) {
            window.mostrarNotificacion(`Sincronización Automática: Se procesaron ${sincronizados} acciones pendientes.`, "success");
        }
        setTimeout(() => { window.location.reload(); }, 3500); 
    }
}

// --- INTERCEPTOR DE FORMULARIOS OFFLINE ---
document.addEventListener('submit', async (e) => {
    if (window.isOfflineMode()) {
        const form = e.target;
        // Evitamos interceptar formularios que ya tienen lógica custom como el buscador o subir factura por JS
        if (form.classList.contains('no-offline-sync') || form.id === 'formSubirFactura') return;

        e.preventDefault();

        // Convertir elementos a FormData
        const formData = new FormData(form);
        const dataObj = {};
        formData.forEach((value, key) => dataObj[key] = value);

        const url = form.action || window.location.href;
        const method = (form.method || 'POST').toUpperCase();

        // Guardar petición en la cola de IndexedDB
        await window.DB.guardarPeticionGenerica({
            url: url,
            method: method,
            body: dataObj,
            isFormData: true,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if(window.mostrarNotificacion) {
            window.mostrarNotificacion("Estás sin conexión. La acción se ha guardado y se enviará automáticamente cuando recuperes el internet.", "warning");
            
            // Cerrar modales abiertos visualmente
            const modalesAbiertos = document.querySelectorAll('.modal.show');
            modalesAbiertos.forEach(m => {
                const modal = bootstrap.Modal.getInstance(m);
                if (modal) modal.hide();
            });
        }
    }
});
