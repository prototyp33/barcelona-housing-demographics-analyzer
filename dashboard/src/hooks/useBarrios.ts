/**
 * Custom Hook: useBarrios
 * Fetch and cache barrio list using React Query
 */
import { useQuery } from '@tanstack/react-query';
import { geographyService } from '@/services/geography.service';
import type { Barrio } from '@/types/api.types';

export const useBarrios = () => {
  return useQuery<Barrio[], Error>({
    queryKey: ['barrios'],
    queryFn: geographyService.getBarrios,
    staleTime: 1000 * 60 * 60, // 1 hour (barrios don't change often)
  });
};

export const useBarriosWithGeometry = () => {
  return useQuery<Barrio[], Error>({
    queryKey: ['barrios', 'geometry'],
    queryFn: geographyService.getBarriosWithGeometry,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
