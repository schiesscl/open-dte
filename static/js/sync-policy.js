(function (root) {
    const recentNotifications = new Map();

    function esArchivoNoDte(filename) {
        const name = String(filename || '').split(/[\\/]/).pop()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[_-]/g, ' ').replace(/\s+/g, ' ').toUpperCase();
        return /\b(?:LIBRO (?:DE )?(?:VENTAS|COMPRAS|GUIAS?)|RESUMEN (?:DE )?VENTAS|REGISTRO (?:DE )?VENTAS|REPORTES?|BALANCE|CARTOLA|COTIZACION|COTIZ|PRESUPUESTO)\b/.test(name);
    }

    function shouldUpload(storage, key, filename, now = Date.now()) {
        if (esArchivoNoDte(filename)) {
            if (!storage.getItem(key)) console.debug('[Buzón Sync] Archivo omitido:', filename);
            storage.setItem(key, 'ignored_non_dte');
            return false;
        }
        const state = storage.getItem(key);
        if (state?.startsWith('retry:')) return now >= Number(state.slice(6));
        return !state;
    }

    function recordResult(storage, key, result, now = Date.now()) {
        storage.setItem(key, result.exito ? 'true' : result.retryable ? `retry:${now + 60000}` : 'failed');
    }

    function allowNotification(message, type, now = Date.now()) {
        if (!String(message || '').trim()) return false;
        for (const [key, time] of recentNotifications) {
            if (now - time >= 15000) recentNotifications.delete(key);
        }
        const key = `${type === 'error' ? 'danger' : type}:${String(message).trim()}`;
        if (recentNotifications.has(key)) return false;
        recentNotifications.set(key, now);
        if (recentNotifications.size > 50) recentNotifications.delete(recentNotifications.keys().next().value);
        return true;
    }

    root.syncPolicy = { esArchivoNoDte, shouldUpload, recordResult, allowNotification };
})(globalThis);
