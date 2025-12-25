import dotenv from 'dotenv';

dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3001', 10),
  loradbApiUrl: process.env.LORADB_API_URL || 'http://localhost:8080',
  jwtSecret: process.env.JWT_SECRET || process.env.LORADB_API_JWT_SECRET || '',
  jwtExpirationHours: parseInt(process.env.JWT_EXPIRATION_HOURS || '1', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3000',
};

// Validate required config
if (!config.jwtSecret || config.jwtSecret.length < 32) {
  console.error('ERROR: JWT_SECRET must be set and at least 32 characters long');
  process.exit(1);
}

// Validate JWT secret complexity (should contain mix of characters)
const hasUpperCase = /[A-Z]/.test(config.jwtSecret);
const hasLowerCase = /[a-z]/.test(config.jwtSecret);
const hasNumbers = /[0-9]/.test(config.jwtSecret);
const hasSpecialChars = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(config.jwtSecret);

if (config.nodeEnv === 'production' && !(hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChars)) {
  console.warn('WARNING: JWT_SECRET should contain uppercase, lowercase, numbers, and special characters for better security');
}

// Validate LoRaDB API URL format
try {
  new URL(config.loradbApiUrl);
} catch (error) {
  console.error('ERROR: LORADB_API_URL must be a valid URL');
  process.exit(1);
}

// Log configuration (without sensitive data)
console.log('Configuration loaded:');
console.log(`- Port: ${config.port}`);
console.log(`- LoRaDB API: ${config.loradbApiUrl}`);
console.log(`- JWT Expiration: ${config.jwtExpirationHours} hour(s)`);
console.log(`- JWT Secret: ${config.jwtSecret.length} characters (hidden for security)`);
console.log(`- CORS Origin: ${config.corsOrigin}`);
console.log(`- Environment: ${config.nodeEnv}`);

// Production environment checks
if (config.nodeEnv === 'production') {
  console.log('\n🔒 Production mode security checks:');

  if (config.corsOrigin === 'http://localhost:3000') {
    console.warn('⚠️  WARNING: CORS_ORIGIN is set to localhost in production!');
  }

  if (config.loradbApiUrl.startsWith('http://localhost')) {
    console.warn('⚠️  WARNING: LORADB_API_URL is set to localhost in production!');
  }

  if (!config.loradbApiUrl.startsWith('https://')) {
    console.warn('⚠️  WARNING: LORADB_API_URL should use HTTPS in production!');
  }
}
