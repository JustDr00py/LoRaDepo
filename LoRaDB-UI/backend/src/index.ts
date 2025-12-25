import express from 'express';
import morgan from 'morgan';
import { config } from './config/env';
import { corsMiddleware } from './middleware/cors';
import { securityHeaders } from './middleware/security';
import { apiLimiter, authLimiter } from './middleware/rateLimiter';
import { errorHandler, notFoundHandler } from './middleware/errorHandler';
import authRoutes from './routes/auth';
import proxyRoutes from './routes/proxy';

const app = express();

// Security headers (should be first)
app.use(securityHeaders);

// Logging middleware
app.use(morgan(config.nodeEnv === 'development' ? 'dev' : 'combined'));

// CORS middleware
app.use(corsMiddleware);

// Body parsing middleware with size limits
app.use(express.json({ limit: '10mb' })); // Limit JSON payload size
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Apply general rate limiting to all routes
app.use('/api', apiLimiter);

// Routes
app.get('/', (_req, res) => {
  res.json({
    name: 'LoRaDB UI Backend',
    version: '1.0.0',
    status: 'running',
  });
});

// Auth routes with stricter rate limiting
app.use('/api/auth', authLimiter, authRoutes);

// Proxy routes
app.use('/api', proxyRoutes);

// Error handlers (must be last)
app.use(notFoundHandler);
app.use(errorHandler);

// Start server
const server = app.listen(config.port, () => {
  console.log(`\n🚀 LoRaDB UI Backend running on port ${config.port}`);
  console.log(`   Environment: ${config.nodeEnv}`);
  console.log(`   LoRaDB API: ${config.loradbApiUrl}`);
  console.log(`\nSecurity Features:`);
  console.log(`   ✓ Helmet security headers enabled`);
  console.log(`   ✓ Rate limiting active`);
  console.log(`   ✓ CORS protection enabled`);
  console.log(`   ✓ Request size limits: 10MB`);
  console.log(`   ✓ Input validation enabled`);
  console.log(`\nEndpoints:`);
  console.log(`   GET  /               - Server info`);
  console.log(`   POST /api/auth/generate-token - Generate JWT token`);
  console.log(`   POST /api/auth/verify-token   - Verify JWT token`);
  console.log(`   GET  /api/health     - LoRaDB health check`);
  console.log(`   POST /api/query      - Execute query`);
  console.log(`   GET  /api/devices    - List devices`);
  console.log(`   GET  /api/devices/:dev_eui - Get device info\n`);
});

// Graceful shutdown
const gracefulShutdown = (signal: string) => {
  console.log(`\n${signal} signal received: closing server gracefully`);
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });

  // Force close after 10 seconds
  setTimeout(() => {
    console.error('Forced shutdown after timeout');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));
