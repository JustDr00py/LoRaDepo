/**
 * Sanitize HTML string to prevent XSS attacks
 * Escapes potentially dangerous characters
 */
export const sanitizeHtml = (input: string): string => {
    const map: Record<string, string> = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    };

    return input.replace(/[&<>"'/]/g, (char) => map[char] || char);
};

/**
 * Sanitize user input for display
 * Removes potentially dangerous characters
 */
export const sanitizeInput = (input: string): string => {
    // Remove any HTML tags
    let sanitized = input.replace(/<[^>]*>/g, '');

    // Remove any script-like content
    sanitized = sanitized.replace(/javascript:/gi, '');
    sanitized = sanitized.replace(/on\w+\s*=/gi, '');

    return sanitized.trim();
};

/**
 * Validate and sanitize DevEUI
 * Must be exactly 16 hexadecimal characters
 */
export const sanitizeDevEUI = (devEUI: string): string | null => {
    const cleaned = devEUI.replace(/[^0-9A-Fa-f]/g, '');

    if (cleaned.length !== 16) {
        return null;
    }

    return cleaned.toUpperCase();
};

/**
 * Sanitize URL to prevent javascript: and data: URLs
 */
export const sanitizeUrl = (url: string): string => {
    const trimmed = url.trim();

    // Block dangerous protocols
    if (
        trimmed.toLowerCase().startsWith('javascript:') ||
        trimmed.toLowerCase().startsWith('data:') ||
        trimmed.toLowerCase().startsWith('vbscript:')
    ) {
        return '';
    }

    return trimmed;
};

/**
 * Safe JSON parse with error handling
 */
export const safeJsonParse = <T = unknown>(json: string, fallback: T): T => {
    try {
        return JSON.parse(json) as T;
    } catch {
        return fallback;
    }
};

/**
 * Validate and sanitize number input
 */
export const sanitizeNumber = (
    input: string | number,
    min?: number,
    max?: number
): number | null => {
    const num = typeof input === 'string' ? parseFloat(input) : input;

    if (isNaN(num) || !isFinite(num)) {
        return null;
    }

    if (min !== undefined && num < min) {
        return null;
    }

    if (max !== undefined && num > max) {
        return null;
    }

    return num;
};
