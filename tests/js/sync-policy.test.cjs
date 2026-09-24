const assert = require('node:assert/strict');
const { test } = require('node:test');
require('../../static/js/sync-policy.js');
const policy = globalThis.syncPolicy;

function storage() {
    const values = new Map();
    return { getItem: key => values.get(key) || null, setItem: (key, value) => values.set(key, value) };
}

test('rechazos y archivos no DTE no se reintentan; modificar el archivo permite reintentar', () => {
    const state = storage();
    assert.equal(policy.shouldUpload(state, 'reporte', 'Libro_de_Ventas.pdf'), false);
    assert.equal(state.getItem('reporte'), 'ignored_non_dte');
    assert.equal(policy.esArchivoNoDte('Cotización.pdf'), true);
    assert.equal(policy.esArchivoNoDte('balanceador.xml'), false);
    assert.equal(policy.shouldUpload(state, 'dte-v1', 'factura.pdf'), true);
    policy.recordResult(state, 'dte-v1', { exito: false });
    assert.equal(policy.shouldUpload(state, 'dte-v1', 'factura.pdf'), false);
    assert.equal(policy.shouldUpload(state, 'dte-v2', 'factura.pdf'), true);
});

test('errores transitorios esperan un minuto y éxitos no se repiten', () => {
    const state = storage();
    policy.recordResult(state, 'dte', { exito: false, retryable: true }, 0);
    assert.equal(policy.shouldUpload(state, 'dte', 'guia.xml', 59999), false);
    assert.equal(policy.shouldUpload(state, 'dte', 'guia.xml', 60000), true);
    policy.recordResult(state, 'dte', { exito: true });
    assert.equal(policy.shouldUpload(state, 'dte', 'guia.xml', 120000), false);
});

test('notificaciones idénticas se deduplican durante quince segundos', () => {
    assert.equal(policy.allowNotification(' Error ', 'error', 0), true);
    assert.equal(policy.allowNotification('Error', 'danger', 14999), false);
    assert.equal(policy.allowNotification('Error', 'danger', 15000), true);
    assert.equal(policy.allowNotification('', 'danger', 15000), false);
});
