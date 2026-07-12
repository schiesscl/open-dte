window.DB = window.DB || {};

try {
    localforage.config({
        name: 'OpenDTE',
        version: 1.0,
        storeName: 'bodega_store', // Should be alphanumeric, with underscores.
        description: 'Almacenamiento offline de la bodega Full Sello'
    });
} catch (e) {
    console.warn("Error configurando localforage:", e);
}

const DBInterno = {
    // Clientes
    guardarCliente: async (cliente) => {
        const clientes = await localforage.getItem('clientes') || [];
        const index = clientes.findIndex(c => c.id === cliente.id);
        if (index !== -1) clientes[index] = cliente;
        else clientes.push(cliente);
        await localforage.setItem('clientes', clientes);
    },
    obtenerClientes: async () => {
        return await localforage.getItem('clientes') || [];
    },

    // Facturas Offline Upload
    guardarFacturaOffline: async (fileObject) => {
        console.log("📦 [IndexedDB] Guardando factura offline en la cola local:", fileObject ? fileObject.name : 'Desconocido');
        const queue = await localforage.getItem('facturas_sync_queue') || [];
        queue.push({
            id_temporal: crypto.randomUUID ? crypto.randomUUID() : new Date().getTime().toString(),
            timestamp: new Date().getTime(),
            file: fileObject, // El archivo PDF directo
            filename: fileObject.name
        });
        await localforage.setItem('facturas_sync_queue', queue);
    },
    obtenerQueueFacturas: async () => {
        return await localforage.getItem('facturas_sync_queue') || [];
    },
    limpiarQueueFacturas: async () => {
        await localforage.setItem('facturas_sync_queue', []);
    },

    // --- NUEVO: Despachos Offline ---
    guardarDespachoOffline: async (facturaId, csrfToken) => {
        const queue = await localforage.getItem('despachos_sync_queue') || [];
        queue.push({
            id_temporal: crypto.randomUUID ? crypto.randomUUID() : new Date().getTime().toString(),
            timestamp: new Date().getTime(),
            factura_id: facturaId,
            csrfToken: csrfToken
        });
        await localforage.setItem('despachos_sync_queue', queue);
    },
    obtenerQueueDespachos: async () => {
        return await localforage.getItem('despachos_sync_queue') || [];
    },
    removerDespachoDeQueue: async (id_temporal) => {
        let queue = await localforage.getItem('despachos_sync_queue') || [];
        queue = queue.filter(item => item.id_temporal !== id_temporal);
        await localforage.setItem('despachos_sync_queue', queue);
    },

    // --- NUEVO: Peticiones Genéricas (Formularios) Offline ---
    guardarPeticionGenerica: async (requestData) => {
        const queue = await localforage.getItem('generic_sync_queue') || [];
        queue.push({
            id_temporal: crypto.randomUUID ? crypto.randomUUID() : new Date().getTime().toString(),
            timestamp: new Date().getTime(),
            url: requestData.url,
            method: requestData.method,
            body: requestData.body,
            headers: requestData.headers,
            isFormData: requestData.isFormData
        });
        await localforage.setItem('generic_sync_queue', queue);
    },
    obtenerQueueGenerica: async () => {
        return await localforage.getItem('generic_sync_queue') || [];
    },
    removerPeticionGenerica: async (id_temporal) => {
        let queue = await localforage.getItem('generic_sync_queue') || [];
        queue = queue.filter(item => item.id_temporal !== id_temporal);
        await localforage.setItem('generic_sync_queue', queue);
    }
};

Object.assign(window.DB, DBInterno);
