/**
 * Common Shared Types
 */

export interface SelectOption {
  value: string | number;
  label: string;
}

export interface DateRange {
  start: Date | null;
  end: Date | null;
}

export interface YearRange {
  start: number;
  end: number;
}

export interface Filter {
  barrio_id?: number;
  distrito?: string;
  year?: number;
  yearRange?: YearRange;
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}
