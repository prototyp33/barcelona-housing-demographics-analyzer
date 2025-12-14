/**
 * Custom Hook: useHousingPrices
 * Fetch housing prices and rent data
 */
import { useQuery } from '@tanstack/react-query';
import { housingService } from '@/services/housing.service';
import type { HousingPrice, Rent } from '@/types/api.types';
import type { Filter } from '@/types/common.types';

export const useHousingPrices = (filters?: Filter) => {
  return useQuery<HousingPrice[], Error>({
    queryKey: ['housing', 'prices', filters],
    queryFn: () => housingService.getHousingPrices(filters),
    enabled: !!filters,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const useRentData = (filters?: Filter) => {
  return useQuery<Rent[], Error>({
    queryKey: ['housing', 'rent', filters],
    queryFn: () => housingService.getRentData(filters),
    enabled: !!filters,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const usePriceTrends = (
  barrioId: number | undefined,
  yearStart?: number,
  yearEnd?: number
) => {
  return useQuery<HousingPrice[], Error>({
    queryKey: ['housing', 'prices', 'trends', barrioId, yearStart, yearEnd],
    queryFn: () => housingService.getPriceTrends(barrioId!, yearStart, yearEnd),
    enabled: !!barrioId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
