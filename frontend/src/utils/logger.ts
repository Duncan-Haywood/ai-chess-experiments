import { createLogger, format, transports } from 'winston';

const logger = createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  format: format.combine(
    format.timestamp(),
    format.errors({ stack: true }),
    format.splat(),
    format.json()
  ),
  defaultMeta: { service: 'chess-frontend' },
  transports: [
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.printf(({ timestamp, level, message, ...meta }) => {
          return `${timestamp} [${level}]: ${message} ${
            Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''
          }`;
        })
      ),
    }),
  ],
});

// Browser console transport
if (typeof window !== 'undefined') {
  logger.add(
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.simple()
      ),
    })
  );
}

// Error tracking
const errorHandler = (error: Error): void => {
  logger.error('Unhandled error:', error);
  // Here you could add error reporting service integration (e.g., Sentry)
};

if (typeof window !== 'undefined') {
  window.addEventListener('error', (event) => {
    errorHandler(event.error);
  });

  window.addEventListener('unhandledrejection', (event) => {
    errorHandler(event.reason);
  });
}

export const logMove = (from: string, to: string, piece: string, capture?: boolean): void => {
  logger.info('Move made', {
    from,
    to,
    piece,
    capture,
    timestamp: new Date().toISOString(),
  });
};

export const logGameState = (fen: string, status: string): void => {
  logger.debug('Game state updated', {
    fen,
    status,
    timestamp: new Date().toISOString(),
  });
};

export const logError = (error: Error, context?: Record<string, unknown>): void => {
  logger.error('Error occurred', {
    error: error.message,
    stack: error.stack,
    context,
    timestamp: new Date().toISOString(),
  });
};

export const logAPIRequest = (
  method: string,
  url: string,
  duration: number,
  status?: number,
  error?: Error
): void => {
  logger.info('API Request', {
    method,
    url,
    duration,
    status,
    error: error?.message,
    timestamp: new Date().toISOString(),
  });
};

export default logger; 