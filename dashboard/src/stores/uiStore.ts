/**
 * UI State Store (Zustand)
 * Manages UI-related state (sidebar, theme, loading)
 */
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  isLoading: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleTheme: () => void;
  setLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: 'light',
  isLoading: false,
  
  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  setSidebarOpen: (open) =>
    set({ sidebarOpen: open }),
  
  toggleTheme: () =>
    set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
  
  setLoading: (loading) =>
    set({ isLoading: loading }),
}));
