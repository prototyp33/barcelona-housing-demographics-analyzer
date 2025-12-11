/**
 * Geography & Barrios API Service
 */
import apiClient from './api';
import type { Barrio } from '@/types/api.types';

export const geographyService = {
  /**
   * Get all barrios (neighborhoods)
   */
  async getBarrios(): Promise<Barrio[]> {
    const response = await apiClient.get<Barrio[]>('/barrios');
    return response.data;
  },

  /**
   * Get a specific barrio by ID
   */
  async getBarrioById(barrioId: number): Promise<Barrio> {
    const response = await apiClient.get<Barrio>(`/barrios/${barrioId}`);
    return response.data;
  },

  /**
   * Get barrios with GeoJSON geometries for mapping
   */
  async getBarriosWithGeometry(): Promise<Barrio[]> {
    const response = await apiClient.get<Barrio[]>('/barrios?include_geometry=true');
    return response.data;
  },
};
