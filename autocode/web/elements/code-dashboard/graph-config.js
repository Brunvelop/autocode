/**
 * graph-config.js
 * Configuración de métricas para el grafo de dependencias.
 *
 * Centraliza todas las constantes de configuración: escalas de color,
 * métricas disponibles, presets de exclusión y límites de escala.
 * Módulo de datos puros — sin dependencias externas.
 */

// ============================================================================
// METRIC COLOR CONFIGURATIONS
// ============================================================================

/**
 * Color scale configuration per color metric.
 * Low instability = stable = good (like CC, inverted scale).
 */
export const METRIC_COLOR_CONFIGS = {
    mi: {
        domain: [0, 40, 70, 100],
        range:  ['#dc2626', '#eab308', '#22c55e', '#059669'],
        label:  'MI',
        legend: [
            { color: '#dc2626', text: 'MI bajo (0–40)' },
            { color: '#eab308', text: 'MI medio (40–70)' },
            { color: '#22c55e', text: 'MI bueno (70–100)' },
        ],
    },
    avg_complexity: {
        domain: [0, 5, 15, 25],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'],
        label:  'CC media',
        legend: [
            { color: '#059669', text: 'CC baja (0–5)' },
            { color: '#eab308', text: 'CC media (5–15)' },
            { color: '#dc2626', text: 'CC alta (>15)' },
        ],
    },
    max_complexity: {
        domain: [0, 10, 25, 50],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'],
        label:  'CC máx',
        legend: [
            { color: '#059669', text: 'CC máx baja (0–10)' },
            { color: '#eab308', text: 'CC máx media (10–25)' },
            { color: '#dc2626', text: 'CC máx alta (>25)' },
        ],
    },
    sloc: {
        domain: [0, 100, 500, 2000],
        range:  ['#dbeafe', '#93c5fd', '#3b82f6', '#1d4ed8'],
        label:  'SLOC',
        legend: [
            { color: '#dbeafe', text: 'Pequeño (<100)' },
            { color: '#3b82f6', text: 'Mediano (100–500)' },
            { color: '#1d4ed8', text: 'Grande (>500)' },
        ],
    },
    instability: {
        domain: [0, 0.3, 0.7, 1],
        range:  ['#059669', '#22c55e', '#eab308', '#dc2626'],
        label:  'Inestab.',
        legend: [
            { color: '#059669', text: 'Estable (0–0.3)' },
            { color: '#eab308', text: 'Parcial (0.3–0.7)' },
            { color: '#dc2626', text: 'Inestable (0.7–1)' },
        ],
    },
};

// ============================================================================
// METRIC LISTS
// ============================================================================

/** Métricas disponibles para el tamaño de los nodos. */
export const SIZE_METRICS = [
    { value: 'sloc',            label: 'SLOC' },
    { value: 'loc',             label: 'LOC' },
    { value: 'functions_count', label: 'Funciones' },
    { value: 'avg_complexity',  label: 'CC media' },
    { value: 'max_complexity',  label: 'CC máx' },
    { value: 'fan_in_out',      label: 'Fan-in+out' },
];

/** Métricas disponibles para el color de los nodos. */
export const COLOR_METRICS = [
    { value: 'mi',              label: 'MI' },
    { value: 'avg_complexity',  label: 'CC media' },
    { value: 'max_complexity',  label: 'CC máx' },
    { value: 'sloc',            label: 'SLOC' },
    { value: 'instability',     label: 'Inestabilidad' },
];

/** Presets de exclusión rápida por path pattern. */
export const EXCLUDE_PRESETS = [
    { label: '🧪 Tests',    pattern: 'test' },
    { label: '📦 Init',     pattern: '__init__' },
    { label: '⚙️ Config',   pattern: 'conftest' },
];

// ============================================================================
// SCALE BOUNDS
// ============================================================================

/** Límites de escala para el radio de los nodos (px). */
export const MIN_RADIUS = 8;
export const MAX_RADIUS = 35;

/** Límites de escala para el grosor de los enlaces (px). */
export const MIN_LINK_WIDTH = 1;
export const MAX_LINK_WIDTH = 4;
