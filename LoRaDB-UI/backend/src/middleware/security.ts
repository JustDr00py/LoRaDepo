import helmet from 'helmet';
import { config } from '../config/env';

/**
 * Security headers middleware using Helmet
 * Protects against common web vulnerabilities
 */
export const securityHeaders = helmet({
    // Content Security Policy
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", 'data:', 'https:'],
            connectSrc: ["'self'", config.loradbApiUrl],
            fontSrc: ["'self'"],
            objectSrc: ["'none'"],
            mediaSrc: ["'self'"],
            frameSrc: ["'none'"],
        },
    },

    // Strict Transport Security (HSTS)
    hsts: {
        maxAge: 31536000, // 1 year
        includeSubDomains: true,
        preload: true,
    },

    // X-Frame-Options
    frameguard: {
        action: 'deny',
    },

    // X-Content-Type-Options
    noSniff: true,

    // X-XSS-Protection (legacy browsers)
    xssFilter: true,

    // Hide X-Powered-By header
    hidePoweredBy: true,

    // Referrer Policy
    referrerPolicy: {
        policy: 'strict-origin-when-cross-origin',
    },
});
