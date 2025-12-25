import { Request, Response, NextFunction } from 'express';
import { body, param, validationResult, ValidationChain } from 'express-validator';

/**
 * Middleware to handle validation errors
 */
export const handleValidationErrors = (
    req: Request,
    res: Response,
    next: NextFunction
): void => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        res.status(400).json({
            error: 'ValidationError',
            message: 'Invalid input data',
            details: errors.array().map(err => ({
                field: err.type === 'field' ? err.path : 'unknown',
                message: err.msg,
            })),
        });
        return;
    }
    next();
};

/**
 * Validation rules for username
 */
export const validateUsername = (): ValidationChain[] => [
    body('username')
        .trim()
        .notEmpty()
        .withMessage('Username is required')
        .isLength({ min: 3, max: 50 })
        .withMessage('Username must be between 3 and 50 characters')
        .matches(/^[a-zA-Z0-9_-]+$/)
        .withMessage('Username can only contain letters, numbers, underscores, and hyphens')
        .escape(),
];

/**
 * Validation rules for token expiration
 */
export const validateTokenExpiration = (): ValidationChain[] => [
    body('expirationHours')
        .optional()
        .isInt({ min: 1, max: 168 })
        .withMessage('Expiration hours must be between 1 and 168 (1 week)')
        .toInt(),
];

/**
 * Validation rules for DevEUI parameter
 */
export const validateDevEUI = (): ValidationChain[] => [
    param('dev_eui')
        .trim()
        .notEmpty()
        .withMessage('DevEUI is required')
        .matches(/^[0-9A-Fa-f]{16}$/)
        .withMessage('DevEUI must be exactly 16 hexadecimal characters')
        .toUpperCase(),
];

/**
 * Validation rules for application ID
 */
export const validateApplicationId = (): ValidationChain[] => [
    param('application_id')
        .trim()
        .notEmpty()
        .withMessage('Application ID is required')
        .matches(/^[a-zA-Z0-9_-]+$/)
        .withMessage('Application ID can only contain letters, numbers, underscores, and hyphens')
        .isLength({ min: 1, max: 100 })
        .withMessage('Application ID must be between 1 and 100 characters'),
];

/**
 * Validation rules for token ID
 */
export const validateTokenId = (): ValidationChain[] => [
    param('id')
        .trim()
        .notEmpty()
        .withMessage('Token ID is required')
        .matches(/^[a-zA-Z0-9_-]+$/)
        .withMessage('Token ID can only contain letters, numbers, underscores, and hyphens')
        .isLength({ min: 1, max: 100 })
        .withMessage('Token ID must be between 1 and 100 characters'),
];

/**
 * Validation rules for query body
 */
export const validateQuery = (): ValidationChain[] => [
    body('query')
        .optional()
        .isString()
        .withMessage('Query must be a string')
        .isLength({ max: 10000 })
        .withMessage('Query is too long (max 10000 characters)'),
];

/**
 * Validation rules for retention policy
 */
export const validateRetentionPolicy = (): ValidationChain[] => [
    body('retention_days')
        .optional()
        .isInt({ min: 1, max: 3650 })
        .withMessage('Retention days must be between 1 and 3650 (10 years)')
        .toInt(),
    body('enabled')
        .optional()
        .isBoolean()
        .withMessage('Enabled must be a boolean')
        .toBoolean(),
];

/**
 * Sanitize string input to prevent XSS
 */
export const sanitizeString = (input: string): string => {
    return input
        .replace(/[<>]/g, '') // Remove angle brackets
        .trim();
};
