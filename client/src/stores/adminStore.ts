import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AdminUser {
  username: string;
  role: 'admin' | 'viewer';
  loginTime: string;
  expiresAt: string;
}

interface AdminState {
  user: AdminUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AdminActions {
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => boolean;
  clearError: () => void;
}

type AdminStore = AdminState & AdminActions;

export const useAdminStore = create<AdminStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (username: string, password: string): Promise<boolean> => {
        set({ isLoading: true, error: null });

        try {
          // Try admin login first
          let response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
          });

          let data;
          if (response.ok) {
            data = await response.json();
          } else {
            // Try viewer login
            response = await fetch('/admin/viewer/login', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ username, password }),
            });

            if (!response.ok) {
              throw new Error('Invalid credentials');
            }

            data = await response.json();
          }

          const token = data.access_token;
          const decoded = JSON.parse(atob(token.split('.')[1])); // Decode JWT payload

          const user: AdminUser = {
            username: decoded.sub,
            role: decoded.role,
            loginTime: decoded.iat ? new Date(decoded.iat * 1000).toISOString() : new Date().toISOString(),
            expiresAt: decoded.exp ? new Date(decoded.exp * 1000).toISOString() : '',
          };

          // Store in localStorage for API calls
          localStorage.setItem('admin_token', token);

          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          return true;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed';
          set({
            isLoading: false,
            error: errorMessage,
          });
          return false;
        }
      },

      logout: () => {
        localStorage.removeItem('admin_token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      checkAuth: () => {
        const token = localStorage.getItem('admin_token');
        if (!token) {
          set({ isAuthenticated: false, user: null, token: null });
          return false;
        }

        try {
          // Check if token is expired
          const decoded = JSON.parse(atob(token.split('.')[1]));
          const now = Date.now() / 1000;

          if (decoded.exp && decoded.exp < now) {
            // Token expired
            localStorage.removeItem('admin_token');
            set({ isAuthenticated: false, user: null, token: null });
            return false;
          }

          // Token is valid
          const user: AdminUser = {
            username: decoded.sub,
            role: decoded.role,
            loginTime: decoded.iat ? new Date(decoded.iat * 1000).toISOString() : new Date().toISOString(),
            expiresAt: decoded.exp ? new Date(decoded.exp * 1000).toISOString() : '',
          };

          set({
            user,
            token,
            isAuthenticated: true,
          });

          return true;
        } catch (error) {
          // Invalid token
          localStorage.removeItem('admin_token');
          set({ isAuthenticated: false, user: null, token: null });
          return false;
        }
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'admin-store',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
