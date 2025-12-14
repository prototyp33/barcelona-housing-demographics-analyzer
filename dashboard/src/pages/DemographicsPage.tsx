/**
 * Demographics Page - Population  Analysis
 */
import React from 'react';
import { Card } from '@/components/common/Card';

export const DemographicsPage: React.FC = () => {
  return (
    <div className="demographics-page">
      <h1>Análisis Demográfico</h1>
      <p className="page-description">
        Estructura poblacional, grupos de edad y migración
      </p>

      <Card title="Población Total">
        <p>Evolución poblacional por barrio</p>
      </Card>

      <Card title="Pirámide de Edades">
        <p>Distribución por grupos de edad y sexo</p>
      </Card>

      <Card title="Nacionalidad">
        <p>Composición por origen (Española, Extranjera UE, Resto)</p>
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
