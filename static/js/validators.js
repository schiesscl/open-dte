/**
 * static/js/validators.js
 * Módulo de validaciones y algoritmos locales para OpenDTE.
 * Incluye verificación Módulo 11 de RUT chileno, formateo en tiempo real y retroalimentación visual.
 */

window.OpenDTEValidators = (function() {
    'use strict';

    /**
     * Calcula el dígito verificador para un cuerpo de RUT chileno.
     * @param {string|number} rutSinDv 
     * @returns {string} '0'-'9' o 'K'
     */
    function calcularDV(rutSinDv) {
        const str = String(rutSinDv).replace(/\./g, '').replace(/-/g, '').trim();
        let suma = 0;
        let multiplicador = 2;

        for (let i = str.length - 1; i >= 0; i--) {
            suma += parseInt(str.charAt(i), 10) * multiplicador;
            multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
        }

        const resto = suma % 11;
        const dv = 11 - resto;

        if (dv === 11) return '0';
        if (dv === 10) return 'K';
        return String(dv);
    }

    /**
     * Valida si un string de RUT chileno es válido según el Módulo 11.
     * @param {string} rut 
     * @returns {boolean}
     */
    function validarRutChileno(rut) {
        if (!rut || typeof rut !== 'string') return false;

        const limpio = rut.replace(/\./g, '').replace(/-/g, '').trim().toUpperCase();
        if (limpio.length < 2) return false;

        const cuerpo = limpio.slice(0, -1);
        const dvIngresado = limpio.slice(-1);

        if (!/^\d+$/.test(cuerpo)) return false;

        const dvCalculado = calcularDV(cuerpo);
        return dvIngresado === dvCalculado;
    }

    /**
     * Formatea un string de RUT a 'XX.XXX.XXX-Y'
     * @param {string} rut 
     * @returns {string}
     */
    function formatearRutChileno(rut) {
        if (!rut || typeof rut !== 'string') return rut || '';

        const limpio = rut.replace(/\./g, '').replace(/-/g, '').trim().toUpperCase();
        if (limpio.length < 2) return rut;

        const cuerpo = limpio.slice(0, -1);
        const dv = limpio.slice(-1);

        if (!/^\d+$/.test(cuerpo)) return rut;

        const cuerpoFormateado = Number(cuerpo).toLocaleString('es-CL');
        return `${cuerpoFormateado}-${dv}`;
    }

    /**
     * Conecta el formateo y la validación en tiempo real a los elementos <input> de RUT.
     * @param {HTMLInputElement} inputEl 
     */
    function attachRutValidation(inputEl) {
        if (!inputEl || inputEl.dataset.rutAttached) return;
        inputEl.dataset.rutAttached = 'true';

        // Buscar o crear contenedor de mensaje de error
        let feedbackEl = inputEl.nextElementSibling;
        if (!feedbackEl || !feedbackEl.classList.contains('invalid-feedback')) {
            feedbackEl = document.createElement('div');
            feedbackEl.className = 'invalid-feedback small fw-bold';
            feedbackEl.textContent = 'El RUT ingresado no es válido (verifique el dígito verificador).';
            inputEl.parentNode.insertBefore(feedbackEl, inputEl.nextSibling);
        }

        const handler = function() {
            const val = inputEl.value;
            if (!val.trim()) {
                inputEl.classList.remove('is-valid', 'is-invalid');
                return;
            }

            const esValido = validarRutChileno(val);
            if (esValido) {
                inputEl.value = formatearRutChileno(val);
                inputEl.classList.remove('is-invalid');
                inputEl.classList.add('is-valid');
            } else {
                inputEl.classList.remove('is-valid');
                inputEl.classList.add('is-invalid');
            }
        };

        inputEl.addEventListener('input', handler);
        inputEl.addEventListener('blur', handler);

        // Formatear valor inicial si viene pre-poblado
        if (inputEl.value.trim()) {
            handler();
        }
    }

    /**
     * Auto-inicializa todos los inputs con clase .rut-input o name="rut" en la página.
     */
    function initAutoBind() {
        const selector = 'input.rut-input, input[name="rut"], input[id*="rut"]';
        document.querySelectorAll(selector).forEach(input => {
            if (!input.readOnly && !input.disabled) {
                attachRutValidation(input);
            }
        });
    }

    // Inicializar automáticamente al cargar el DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAutoBind);
    } else {
        initAutoBind();
    }

    return {
        calcularDV: calcularDV,
        validarRutChileno: validarRutChileno,
        formatearRutChileno: formatearRutChileno,
        attachRutValidation: attachRutValidation,
        initAutoBind: initAutoBind
    };
})();
