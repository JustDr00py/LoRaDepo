import cors from 'cors';
import { config } from '../config/env';

/**
 * Parse CORS origins from environment variable
 * Supports comma-separated list of origins
 */
const getAllowedOrigins = (): string[] => {
  const origins = config.corsOrigin.split(',').map(origin => origin.trim());
  return origins;
};

/**
 * Validate origin against allowed list
 */
const originValidator = (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
  const allowedOrigins = getAllowedOrigins();

  // Allow requests with no origin (like mobile apps, curl, Postman)
  if (!origin) {
    callback(null, true);
    return;
  }

  if (allowedOrigins.includes(origin) || allowedOrigins.includes('*')) {
    callback(null, true);
  } else {
    console.warn('CORS: Blocked request from unauthorized origin:', origin);
    callback(new Error('Not allowed by CORS'));
  }
};

export const corsMiddleware = cors({
  origin: originValidator,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  exposedHeaders: ['RateLimit-Limit', 'RateLimit-Remaining', 'RateLimit-Reset'],
  maxAge: 86400, // 24 hours
});
