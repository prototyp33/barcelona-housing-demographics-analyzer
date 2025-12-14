/**
 * Demographics API Service
 */
import apiClient from './api';
import type { Demographics } from '@/types/api.types';
import type { Filter } from '@/types/common.types';

export const demographicsService = {
  /**
   * Get demographic data with optional filters
   */
  async getDemographics(filters?: Filter): Promise<Demographics[]> {
    const response = await apiClient.get<Demographics[]>('/demographics', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get extended demographic data (age groups, nationality)
   */
  async getExtendedDemographics(filters?: Filter): Promise<Demographics[]> {
    const response = await apiClient.get<Demographics[]>('/demographics/extended', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get demographic trends over time for a specific barrio
   */
  async getDemographicTrends(barrioId: number, yearStart?: number, yearEnd?: number): Promise<Demographics[]> {
    const response = await apiClient.get<Demographics[]>(`/demographics/trends/${barrioId}`, {
      params: { year_start: yearStart, year_end: yearEnd },
    });
    return response.data;
  },
};
