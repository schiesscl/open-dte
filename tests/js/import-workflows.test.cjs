const assert = require('node:assert/strict');
const { test } = require('node:test');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');

function element(value = '') {
    const classes = new Set();
    return {
        value, innerHTML: '', textContent: '', disabled: false, style: {}, events: {},
        classList: {
            add: name => classes.add(name), remove: name => classes.delete(name),
            contains: name => classes.has(name),
            toggle(name, enabled) { enabled ? classes.add(name) : classes.delete(name); },
        },
        addEventListener(name, callback) { this.events[name] = callback; },
        appendChild() {}, scrollIntoView() {}, focus() {},
    };
}

function workflow(filename, ids, responses) {
    const elements = Object.fromEntries(ids.map(id => [id, element()]));
    const requests = [];
    const context = vm.createContext({
        window: { location: { reload() {} } }, console,
        document: {
            getElementById: id => elements[id] || null,
            querySelector: () => null, createElement: () => element(),
        },
        FormData: class {
            constructor() { this.values = new Map(); }
            append(key, value) { this.values.set(key, value); }
        },
        fetch: async (url, options) => {
            requests.push({ url, ...options });
            return { ok: true, headers: { get: () => 'application/json' }, json: async () => responses.shift() };
        },
        setInterval: () => 1, clearInterval() {}, setTimeout() {},
    });
    vm.runInContext(readFileSync(`${__dirname}/../../static/js/${filename}`, 'utf8'), context);
    return { elements, requests, context };
}

test('Excel valida mapeo y conserva archivo, columnas y CSRF al confirmar', async () => {
    const { elements: el, requests, context } = workflow('excel-import.js', [
        'modal-importar-excel', 'excel-alert-container', 'excel-file-input', 'btn-excel-confirmar',
        'excel-map-codigo', 'excel-map-actual', 'excel-map-real', 'excel-map-minimo', 'excel-map-sistema',
    ], [{ exito: true, columnas: [], vista_previa: [], total_filas: 2 }, { exito: true }]);
    context.window.OpenDTEExcelImport.init({ csrfToken: 'csrf-test', urls: { analizarExcel: '/analizar', procesarExcel: '/procesar' } });
    const file = { name: 'stock.xlsx' };
    el['excel-file-input'].events.change({ target: { files: [file] } });
    await new Promise(resolve => setImmediate(resolve));
    el['excel-map-codigo'].value = 'SKU';
    el['excel-map-actual'].value = 'SKU';
    await el['btn-excel-confirmar'].events.click();
    assert.equal(requests.length, 1);
    assert.match(el['excel-alert-container'].innerHTML, /misma columna/);
    el['excel-map-actual'].value = 'Stock';
    await el['btn-excel-confirmar'].events.click();
    assert.equal(requests.length, 2);
    const data = requests[1].body.values;
    assert.equal(data.get('archivo'), file);
    assert.equal(data.get('columna_codigo'), 'SKU');
    assert.equal(data.get('columna_stock_actual'), 'Stock');
    assert.equal(data.get('csrfmiddlewaretoken'), 'csrf-test');
});

test('Guía valida cantidades y recupera botón tras rechazo del servidor', async () => {
    const { elements: el, requests, context } = workflow('guia-abastecimiento.js', [
        'modal-guia', 'guia-alert-container', 'guia-folio', 'guia-tabla-items', 'btn-guia-confirmar',
    ], [{ exito: false, mensaje: 'Folio duplicado' }]);
    const cantidad = element('1.5');
    const producto = element('42');
    el['guia-tabla-items'].querySelectorAll = () => [{
        children: [{}, { textContent: 'Producto' }],
        querySelector: selector => selector === '.quantity-input' ? cantidad : producto,
    }];
    context.window.OpenDTEGuiaAbastecimiento.init({ csrfToken: 'csrf-test', urls: { procesarGuia: '/procesar' } });
    el['guia-folio'].value = '52';
    await el['btn-guia-confirmar'].events.click();
    assert.equal(requests.length, 0);
    assert.match(el['guia-alert-container'].innerHTML, /entero positivo/);
    cantidad.value = '3';
    await el['btn-guia-confirmar'].events.click();
    assert.deepEqual(JSON.parse(requests[0].body), {
        folio: 52, items: [{ producto_id: 42, cantidad: 3, descripcion_origen: 'Producto' }],
    });
    assert.equal(el['btn-guia-confirmar'].disabled, false);
    assert.match(el['guia-alert-container'].innerHTML, /Folio duplicado/);
});

test('Escaneo automático usa la política para evitar reenvíos del mismo archivo', async () => {
    const template = readFileSync(`${__dirname}/../../inventario/templates/inventario/base.html`, 'utf8');
    const code = template.slice(template.indexOf('window.globalSync = {'), template.indexOf('\n      document.addEventListener("DOMContentLoaded",', template.indexOf('window.globalSync = {')));
    const state = {};
    Object.defineProperties(state, {
        getItem: { value: key => state[key] || null },
        setItem: { value: (key, value) => { state[key] = value; } },
        removeItem: { value: key => { delete state[key]; } },
    });
    const context = vm.createContext({ window: {}, localStorage: state, console, verificarPermiso: async () => true, document: { visibilityState: 'hidden' } });
    vm.runInContext(readFileSync(`${__dirname}/../../static/js/sync-policy.js`, 'utf8'), context);
    context.window.syncPolicy = context.syncPolicy;
    vm.runInContext(code, context);
    const sync = context.window.globalSync;
    let uploads = 0;
    let modified = 1;
    sync.updateStatus = sync.logToPage = () => {};
    sync.uploadFile = async () => { uploads++; return { exito: false, mensaje: 'Documento inválido' }; };
    sync.dirHandle = { async *values() {
        for (const name of ['Libro Ventas.pdf', 'factura.pdf']) {
            yield { kind: 'file', getFile: async () => ({ name, size: 100, lastModified: modified }) };
        }
    } };
    await sync.scanDirectory();
    await sync.scanDirectory();
    assert.equal(uploads, 1);
    modified = 2;
    await sync.scanDirectory();
    assert.equal(uploads, 2);
});
