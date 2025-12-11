/**
 * Global Filter Store (Zustand)
 * Manages application-wide filter state
 */
import { create } from 'zustand';
import { Filter, YearRange } from '@/types/common.types';

interface FilterState {
  filters: Filter;
  setBarrio: (barrioId: number | undefined) => void;
  setDistrito: (distrito: string | undefined) => void;
  setYear: (year: number | undefined) => void;
  setYearRange: (yearRange: YearRange | undefined) => void;
  clearFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  filters: {},
  
  setBarrio: (barrioId) =>
    set((state) => ({
      filters: { ...state.filters, barrio_id: barrioId },
    })),
  
  setDistrito: (distrito) =>
    set((state) => ({
      filters: { ...state.filters, distrito },
    })),
  
  setYear: (year) =>
    set((state) => ({
      filters: { ...state.filters, year },
    })),
  
  setYearRange: (yearRange) =>
    set((state) => ({
      filters: { ...state.filters, yearRange },
    })),
  
  clearFilters: () => set({ filters: {} }),
}));
