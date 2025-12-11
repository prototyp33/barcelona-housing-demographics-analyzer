/**
 * Prices Page - Housing Price Analysis
 */
import React from 'react';
import { Card } from '@/components/common/Card';

export const PricesPage: React.FC = () => {
  return (
    <div className="prices-page">
      <h1>Precios de Vivienda</h1>
      <p className="page-description">
        Evolución de precios de venta y alquiler por m² en Barcelona
      </p>

      <Card title="Precio de Venta (€/m²)">
        <p>Gráfica de evolución temporal próximamente...</p>
      </Card>

      <Card title="Precio de Alquiler (€/m²)">
        <p>Comparativa por distritos y barrios</p>
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
