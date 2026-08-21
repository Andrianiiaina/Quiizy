export const APP_CONFIG = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  appName: 'LMS',
  version: '0.1.0',
} as const
