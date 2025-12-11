/**
 * Housing Prices & Rent API Service
 */
import apiClient from './api';
import { HousingPrice, Rent } from '@/types/api.types';
import { Filter } from '@/types/common.types';

export const housingService = {
  /**
   * Get housing prices with optional filters
   */
  async getHousingPrices(filters?: Filter): Promise<HousingPrice[]> {
    const response = await apiClient.get<HousingPrice[]>('/housing/prices', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get rent data with optional filters
   */
  async getRentData(filters?: Filter): Promise<Rent[]> {
    const response = await apiClient.get<Rent[]>('/housing/rent', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get housing price trends over time for a specific barrio
   */
  async getPriceTrends(barrioId: number, yearStart?: number, yearEnd?: number): Promise<HousingPrice[]> {
    const response = await apiClient.get<HousingPrice[]>(`/housing/prices/trends/${barrioId}`, {
      params: { year_start: yearStart, year_end: yearEnd },
    });
    return response.data;
  },

  /**
   * Calculate gross yield (rental return on investment)
   */
  async getGrossYield(barrioId: number, year: number): Promise<{ barrio_id: number; year: number; yield: number }> {
    const response = await apiClient.get(`/housing/yield/${barrioId}`, {
      params: { year },
    });
    return response.data;
  },
};
