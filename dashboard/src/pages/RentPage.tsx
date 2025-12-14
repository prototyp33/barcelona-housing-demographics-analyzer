/**
 * Rent Page - Affordability and Rent Analysis
 */
import React from 'react';
import { Card } from '@/components/common/Card';

export const RentPage: React.FC = () => {
  return (
    <div className="rent-page">
      <h1>Análisis de Renta</h1>
      <p className="page-description">
        Distribución de renta disponible por barrios y análisis de asequibilidad
      </p>

      <Card title="Renta Media por Barrio">
        <p>Visualización de datos de renta próximamente...</p>
      </Card>

      <Card title="Índice de Asequibilidad">
        <p>Ratio precio vivienda / renta disponible por barrio</p>
      </Card>

      <style>{`
        .page-description {
          color: #6b7280;
          margin-bottom: 2rem;
        }
      `}</style>
    </div>
  );
};
