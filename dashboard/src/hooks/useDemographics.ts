/**
 * Custom Hook: useDemographics
 * Fetch demographics data with filters
 */
import { useQuery } from '@tanstack/react-query';
import { demographicsService } from '@/services/demographics.service';
import type { Demographics } from '@/types/api.types';
import type { Filter } from '@/types/common.types';

export const useDemographics = (filters?: Filter) => {
  return useQuery<Demographics[], Error>({
    queryKey: ['demographics', filters],
    queryFn: () => demographicsService.getDemographics(filters),
    enabled: !!filters, // Only fetch when filters are provided
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const useExtendedDemographics = (filters?: Filter) => {
  return useQuery<Demographics[], Error>({
    queryKey: ['demographics', 'extended', filters],
    queryFn: () => demographicsService.getExtendedDemographics(filters),
    enabled: !!filters,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const useDemographicTrends = (
  barrioId: number | undefined,
  yearStart?: number,
  yearEnd?: number
) => {
  return useQuery<Demographics[], Error>({
    queryKey: ['demographics', 'trends', barrioId, yearStart, yearEnd],
    queryFn: () => demographicsService.getDemographicTrends(barrioId!, yearStart, yearEnd),
    enabled: !!barrioId, // Only fetch when barrio ID is provided
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};
