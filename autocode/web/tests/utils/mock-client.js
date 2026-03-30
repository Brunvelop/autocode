/**
 * mock-client.js
 * Utilidad para mockear RefractClient.prototype.call en tests de componentes web.
 *
 * Los componentes usan `this._client = new RefractClient()` y llaman a
 * `this._client.call(funcName, params)` directamente. Este helper parchea
 * el prototype para interceptar TODAS las instancias.
 *
 * @example
 * import { mockRefractCall } from '../../utils/mock-client.js';
 *
 * const mock = await mockRefractCall(async (funcName, params) => {
 *     if (funcName === 'get_git_log') return MOCK_GIT_LOG;
 *     if (funcName === 'list_commit_plans') return [];
 *     // Return undefined to fall through to the real implementation
 * });
 *
 * // ... import components and run tests ...
 *
 * // Optionally change handler mid-test (e.g. to simulate errors):
 * mock.setHandler(async (funcName) => {
 *     if (funcName === 'list_commit_plans') throw new Error('Network error');
 * });
 *
 * // Optionally restore original behaviour after tests:
 * mock.restore();
 */

/**
 * Patches RefractClient.prototype.call with a custom handler function.
 *
 * The handler receives (funcName, params, funcInfo) and should return:
 * - mock data (any value including null/false/0) → used as the call result
 * - undefined → falls through to the original RefractClient.prototype.call
 *
 * @param {Function} handler - async (funcName, params, funcInfo) => mockData | undefined
 * @returns {Promise<{ setHandler: Function, restore: Function }>}
 */
export async function mockRefractCall(handler) {
    const { RefractClient } = await import('/refract/client.js');
    const originalCall = RefractClient.prototype.call;

    const mock = {
        handler,

        /**
         * Replaces the active handler. Useful to change mock behaviour mid-test
         * (e.g. to simulate a network error for a specific test case).
         *
         * @param {Function} newHandler
         */
        setHandler(newHandler) {
            mock.handler = newHandler;
        },

        /**
         * Restores RefractClient.prototype.call to its original implementation.
         * Call this if you need to clean up after tests (usually not required
         * since each page load starts fresh).
         */
        restore() {
            RefractClient.prototype.call = originalCall;
        },
    };

    RefractClient.prototype.call = async function(funcName, params, funcInfo) {
        const result = await mock.handler.call(this, funcName, params, funcInfo);
        if (result !== undefined) return result;
        return originalCall.call(this, funcName, params, funcInfo);
    };

    return mock;
}
