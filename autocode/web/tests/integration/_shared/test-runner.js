/**
 * Test Runner compartido para integration tests
 *
 * Responsabilidad única: ejecutar tests, assertions y reportar resultados.
 * Soporta agrupación visual (suites) y expansión de detalles.
 */

export class TestRunner {
    constructor(options = {}) {
        this.resultsContainer = options.resultsContainer || document.getElementById('results');
        this.summaryContainer = options.summaryContainer || document.getElementById('summary');
        this.serverStatusContainer = options.serverStatusContainer || document.getElementById('serverStatus');

        this.passed = 0;
        this.failed = 0;
        this.skipped = 0;
        this.testQueue = [];
        this.serverAvailable = false;
        
        // Estado para agrupación
        this.currentGroup = null;
    }

    // ============================================
    // ASSERTIONS
    // ============================================

    assertEqual(actual, expected, msg = '') {
        if (actual !== expected) {
            throw new Error(`Expected "${expected}", got "${actual}". ${msg}`);
        }
    }

    assertTrue(value, msg = '') {
        if (!value) throw new Error(`Expected truthy value. ${msg}`);
    }

    assertFalse(value, msg = '') {
        if (value) throw new Error(`Expected falsy value. ${msg}`);
    }

    assertContains(text, substring, msg = '') {
        if (!text?.includes?.(substring)) {
            throw new Error(`Expected "${text}" to contain "${substring}". ${msg}`);
        }
    }

    assertThrows(fn, expectedError = null, msg = '') {
        let threw = false;
        let error = null;
        try {
            fn();
        } catch (e) {
            threw = true;
            error = e;
        }
        if (!threw) {
            throw new Error(`Expected function to throw. ${msg}`);
        }
        if (expectedError && !error.message.includes(expectedError)) {
            throw new Error(`Expected error to contain "${expectedError}", got "${error.message}". ${msg}`);
        }
    }

    // ============================================
    // TEST REGISTRATION & GROUPING
    // ============================================

    /**
     * Define un grupo visual de tests
     * @param {string} name - Nombre del grupo
     * @param {Function} fn - Función que contiene las llamadas a test()
     */
    group(name, fn) {
        if (!this.resultsContainer) {
            fn();
            return;
        }

        // Contenedor principal del grupo
        const groupContainer = document.createElement('div');
        groupContainer.className = 'mb-6 border border-gray-200 rounded-lg overflow-hidden shadow-sm bg-white';

        // Header del grupo (FUERA del details para garantizar visibilidad)
        const header = document.createElement('div');
        header.className = 'p-3 bg-gray-100 flex items-center justify-between border-b border-gray-200';
        
        const title = document.createElement('h3');
        title.className = 'm-0 text-base font-bold text-gray-900 flex items-center gap-2';
        title.innerHTML = `<span>🧩</span> ${name}`;
        
        const badgeSpan = document.createElement('span');
        badgeSpan.className = 'text-xs font-normal text-gray-500 bg-gray-200 px-2 py-1 rounded-full';
        badgeSpan.textContent = 'Pending';

        header.appendChild(title);
        header.appendChild(badgeSpan);
        groupContainer.appendChild(header);

        // Contenedor de tests (usando details para poder colapsar si se quiere, pero el título queda fijo)
        const details = document.createElement('details');
        details.open = true;
        details.className = 'bg-white';

        const summary = document.createElement('summary');
        summary.className = 'p-2 text-xs text-gray-500 cursor-pointer hover:bg-gray-50 border-b border-gray-100 select-none';
        summary.textContent = 'Ver/Ocultar detalles de los tests';
        
        const content = document.createElement('div');
        content.className = 'p-2 space-y-2 bg-gray-50/50';

        details.appendChild(summary);
        details.appendChild(content);
        groupContainer.appendChild(details);
        
        this.resultsContainer.appendChild(groupContainer);

        // Establecer contexto actual
        this.currentGroup = {
            element: groupContainer, // Referencia al contenedor principal para bordes de estado
            summary: header, // Referencia al header para badges (no es summary tag real, pero sirve para updateGroupStatus)
            content: content,
            name: name,
            total: 0,
            passed: 0,
            failed: 0,
            skipped: 0
        };

        // Ejecutar bloque de registro
        fn();

        // Limpiar contexto
        this.currentGroup = null;
    }

    test(name, fn, options = {}) {
        const group = this.currentGroup;
        if (group) group.total++; // Contabilizar total esperado del grupo

        this.testQueue.push({ name, fn, options, group });
    }

    // ============================================
    // UTILITIES
    // ============================================

    async waitForElement(tagName, timeout = 5000) {
        const start = Date.now();
        while (!customElements.get(tagName)) {
            if (Date.now() - start > timeout) {
                throw new Error(`Timeout waiting for <${tagName}> to be defined`);
            }
            await new Promise(r => setTimeout(r, 50));
        }
    }

    async sleep(ms) {
        return new Promise(r => setTimeout(r, ms));
    }

    // ============================================
    // SERVER CHECK
    // ============================================

    async checkServer() {
        if (!this.serverStatusContainer) return true;

        try {
            const response = await fetch('/health', {
                signal: AbortSignal.timeout(3000)
            });
            if (response.ok) {
                const data = await response.json();
                this.serverStatusContainer.innerHTML = `
                    <span class="text-green-800">✅ Servidor conectado - ${data.functions} funciones registradas</span>
                `;
                this.serverStatusContainer.className = 'mb-6 p-4 bg-green-100 border border-green-300 rounded-lg';
                return true;
            }
        } catch (e) {
            this.serverStatusContainer.innerHTML = `
                <span class="text-red-800">❌ Servidor no disponible. Ejecuta: <code class="bg-red-200 px-1 rounded">uv run uvicorn autocode.interfaces.api:app --reload</code></span>
            `;
            this.serverStatusContainer.className = 'mb-6 p-4 bg-red-100 border border-red-300 rounded-lg';
        }
        return false;
    }

    // ============================================
    // UI RENDERING HELPERS
    // ============================================

    _createTestCard(name, group) {
        // Determinar dónde insertar: en el grupo actual o en el root
        const parent = group ? group.content : this.resultsContainer;
        if (!parent) return { container: null, stage: null };

        const details = document.createElement('details');
        details.className = 'border border-gray-200 rounded bg-white overflow-hidden transition-all';
        // Por defecto colapsado para mantener limpieza

        const summary = document.createElement('summary');
        summary.className = 'p-2 cursor-pointer hover:bg-gray-50 flex items-center gap-2 text-sm font-medium text-gray-600 select-none';
        summary.innerHTML = `<span class="animate-spin">⏳</span> ${name}`;
        // Quitar marcador default de details si se desea CSS custom, pero native está bien

        const stage = document.createElement('div');
        stage.className = 'p-4 border-t border-gray-100 bg-gray-50'; // Área visual del componente
        
        details.appendChild(summary);
        details.appendChild(stage);
        parent.appendChild(details);

        return { container: details, stage, summary };
    }

    _updateTestCard(card, status, message = '') {
        if (!card.container) return;

        const { container, summary } = card;
        const testName = summary.textContent.replace('⏳ ', '').trim();

        if (status === 'passed') {
            container.className = 'border border-green-200 rounded bg-white';
            summary.className = 'p-2 cursor-pointer hover:bg-green-50 flex items-center gap-2 text-sm font-medium text-green-800';
            summary.innerHTML = `<span>✅</span> ${testName}`;
        } else if (status === 'failed') {
            container.className = 'border border-red-200 rounded bg-white';
            summary.className = 'p-2 cursor-pointer hover:bg-red-50 flex items-center gap-2 text-sm font-medium text-red-800';
            summary.innerHTML = `<span>❌</span> ${testName}`;
            
            // Expandir automáticamente si falla para ver el error
            container.open = true;

            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-xs text-red-600 font-mono bg-red-50 p-2 border-t border-red-100';
            errorDiv.textContent = message;
            // Insertar error antes del stage
            summary.after(errorDiv);
        } else if (status === 'skipped') {
            container.className = 'border border-gray-200 rounded bg-white opacity-60';
            summary.innerHTML = `<span>⏭️</span> ${testName} <span class="text-xs italic">(${message})</span>`;
        }
    }

    _updateGroupStatus(group) {
        if (!group) return;

        const { summary, passed, failed, total, skipped } = group;
        const completed = passed + failed + skipped;
        
        let statusBadge = '';
        let statusClass = '';

        if (failed > 0) {
            statusClass = 'bg-red-100 text-red-800 border border-red-200';
            statusBadge = `❌ ${passed}/${total} passed (${failed} failed)`;
            group.element.className = group.element.className.replace('border-gray-200', 'border-red-300'); // Resaltar borde grupo
        } else if (completed === total) {
            statusClass = 'bg-green-100 text-green-800 border border-green-200';
            statusBadge = `✅ ${passed}/${total} passed`;
             group.element.className = group.element.className.replace('border-gray-200', 'border-green-300');
        } else {
            statusClass = 'bg-blue-100 text-blue-800';
            statusBadge = `⏳ Running... ${completed}/${total}`;
        }

        // Actualizar solo el badge del summary
        const badgeEl = summary.querySelector('span:last-child');
        if (badgeEl) {
            badgeEl.className = `text-xs font-medium px-2 py-1 rounded-full ${statusClass}`;
            badgeEl.textContent = statusBadge;
        }
    }

    // ============================================
    // EXECUTION
    // ============================================

    async run() {
        this.serverAvailable = await this.checkServer();

        for (const { name, fn, options, group } of this.testQueue) {
            // Preparar UI del test
            const card = this._createTestCard(name, group);

            // Skip logic
            if (options.requiresServer && !this.serverAvailable) {
                this._updateTestCard(card, 'skipped', 'requiere servidor');
                this.skipped++;
                if (group) { group.skipped++; this._updateGroupStatus(group); }
                continue;
            }

            try {
                // Ejecutar test pasando el stage visual
                await fn(card.stage);
                this._updateTestCard(card, 'passed');
                this.passed++;
                if (group) { group.passed++; this._updateGroupStatus(group); }
            } catch (e) {
                this._updateTestCard(card, 'failed', e.message);
                this.failed++;
                if (group) { group.failed++; this._updateGroupStatus(group); }
            }
        }

        this._renderSummary();
    }

    _renderSummary() {
        if (!this.summaryContainer) return;

        const total = this.passed + this.failed + this.skipped;
        this.summaryContainer.innerHTML = `
            <div class="flex gap-6 items-center">
                <span class="text-2xl font-bold">${total} tests</span>
                <span class="text-green-600 font-medium">✅ ${this.passed} passed</span>
                <span class="text-red-600 font-medium">❌ ${this.failed} failed</span>
                <span class="text-gray-600 font-medium">⏭️ ${this.skipped} skipped</span>
            </div>
        `;
    }
}
