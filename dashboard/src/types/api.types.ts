/**
 * API Response Types
 * Types matching the Barcelona Housing Demographics backend data structure
 */

export interface Barrio {
  barrio_id: number;
  barrio_nombre: string;
  distrito_nombre: string;
  geometry_json?: string; // GeoJSON string for mapping
}

export interface Demographics {
  barrio_id: number;
  anio: number;
  poblacion: number;
  sexo?: string;
  grupo_edad?: string;
  nacionalidad?: string;
}

export interface HousingPrice {
  barrio_id: number;
  anio: number;
  trimestre?: number;
  precio_venta_m2?: number;
  precio_alquiler_m2?: number;
  superficie_media?: number;
}

export interface Rent {
  barrio_id: number;
  anio: number;
  renta_euros: number;
  renta_mediana?: number;
  num_secciones?: number;
}

export interface DataQualityMetric {
  metric_name: string;
  value: number;
  target: number;
  status: 'success' | 'warning' | 'error';
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}
