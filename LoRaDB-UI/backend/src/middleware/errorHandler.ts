import { Request, Response, NextFunction } from 'express';

export interface AppError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

/**
 * Sanitize error message to prevent information leakage
 */
const sanitizeErrorMessage = (message: string, isProduction: boolean): string => {
  if (isProduction) {
    // In production, return generic messages for non-operational errors
    const safeMessages: Record<string, string> = {
      'ECONNREFUSED': 'Service temporarily unavailable',
      'ETIMEDOUT': 'Request timeout',
      'ENOTFOUND': 'Service unavailable',
      'ValidationError': message, // Keep validation errors as they're user-facing
      'TooManyRequests': message,
    };

    // Check if message contains any known safe patterns
    for (const [key, value] of Object.entries(safeMessages)) {
      if (message.includes(key)) {
        return value;
      }
    }

    return 'An error occurred while processing your request';
  }

  return message;
};

export const errorHandler = (
  err: AppError,
  req: Request,
  res: Response,
  _next: NextFunction
) => {
  const isProduction = process.env.NODE_ENV === 'production';
  const statusCode = err.statusCode || 500;

  // Log error details (always log full details server-side)
  console.error('Error occurred:', {
    timestamp: new Date().toISOString(),
    method: req.method,
    path: req.path,
    statusCode,
    message: err.message,
    stack: err.stack,
    isOperational: err.isOperational,
  });

  // Sanitize message for client
  const clientMessage = err.isOperational
    ? err.message
    : sanitizeErrorMessage(err.message, isProduction);

  const errorResponse: Record<string, unknown> = {
    error: err.name || 'Error',
    message: clientMessage,
  };

  // Only include stack trace in development mode
  if (!isProduction && err.stack) {
    errorResponse.stack = err.stack;
  }

  res.status(statusCode).json(errorResponse);
};

export const notFoundHandler = (req: Request, res: Response): void => {
  console.warn('Route not found:', {
    timestamp: new Date().toISOString(),
    method: req.method,
    path: req.path,
    ip: req.ip,
  });

  res.status(404).json({
    error: 'NotFound',
    message: `Route ${req.method} ${req.path} not found`,
  });
};
