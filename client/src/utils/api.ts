// API base URL configuration
const viteApiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';
export const API_BASE_URL = viteApiUrl;

// Helper function to build full API URLs
export const apiUrl = (endpoint: string): string => {
  // Remove leading slash from endpoint if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;

  // Always use the API base URL for direct connection to backend
  const fullUrl = `${viteApiUrl}/${cleanEndpoint}`;
  console.log('API URL:', fullUrl, '(VITE_API_URL:', (import.meta as any).env?.VITE_API_URL || 'default', ')');
  return fullUrl;
};
