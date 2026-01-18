/**
 * MAST Color Scheme - JavaScript API
 * Provides programmatic access to unified color palette
 */

const MAST_COLORS = {
    info: {
        bg: '#cff4fc',
        text: '#055160',
        border: '#9eeaf9'
    },
    success: {
        bg: '#d1e7dd',
        text: '#0f5132',
        border: '#a3cfbb'
    },
    warning: {
        bg: '#fff3cd',
        text: '#664d03',
        border: '#ffe69c'
    },
    danger: {
        bg: '#f8d7da',
        text: '#842029',
        border: '#f1aeb5'
    },
    primary: {
        bg: '#cfe2ff',
        text: '#084298',
        border: '#9ec5fe'
    },
    secondary: {
        bg: '#e2e3e5',
        text: '#41464b',
        border: '#c4c5c7'
    }
};

// Set up semantic aliases
MAST_COLORS.start = MAST_COLORS.primary;
MAST_COLORS.end = MAST_COLORS.success;
MAST_COLORS.error = MAST_COLORS.danger;

/**
 * Get MAST color for a specific type and property
 * @param {string} type - Color type (info, success, warning, danger, primary, start, end, error)
 * @param {string} property - Property to get (bg, text, border)
 * @returns {string} Color hex code
 */
function getMastColor(type, property = 'border') {
    const colorSet = MAST_COLORS[type] || MAST_COLORS.info;
    return colorSet[property] || colorSet.border;
}

/**
 * Get all color properties for a type
 * @param {string} type - Color type
 * @returns {object} Object with bg, text, and border properties
 */
function getMastColors(type) {
    return MAST_COLORS[type] || MAST_COLORS.info;
}

/**
 * Get Bootstrap icon class for notification type
 * @param {string} type - Notification type
 * @returns {string} Bootstrap icon class
 */
function getMastIcon(type) {
    const iconMap = {
        info: 'bi-info-circle-fill',
        error: 'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        start: 'bi-play-circle-fill',
        end: 'bi-check-circle-fill',
        success: 'bi-check-circle-fill',
        danger: 'bi-x-circle-fill',
        primary: 'bi-info-circle-fill'
    };
    return iconMap[type] || iconMap.info;
}
