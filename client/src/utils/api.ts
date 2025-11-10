// API base URL configuration
const viteApiUrl = (import.meta as any).env?.VITE_API_URL;
export const API_BASE_URL = viteApiUrl || '/api';

// Helper function to build full API URLs
export const apiUrl = (endpoint: string): string => {
  // Remove leading slash from endpoint if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // If VITE_API_URL is set, use it as the full base URL
  if (viteApiUrl) {
    return `${viteApiUrl}/${cleanEndpoint}`;
  }

  // Otherwise use relative paths (for development proxy)
  return `/${cleanEndpoint}`;
};
