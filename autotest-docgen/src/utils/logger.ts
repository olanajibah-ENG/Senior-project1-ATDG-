/// <reference types="vite/client" />

/**
 * Dev-only logger — silent in production builds.
 * Usage: import logger from './utils/logger';
 *        logger.log('message', data);
 */
const isDev = import.meta.env.DEV;

const logger = {
  log: (...args: unknown[]) => { if (isDev) console.log(...args); },
  warn: (...args: unknown[]) => { if (isDev) console.warn(...args); },
  error: (...args: unknown[]) => { if (isDev) console.error(...args); },
};

export default logger;
