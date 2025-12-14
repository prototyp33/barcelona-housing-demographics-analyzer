/**
 * Overview Page - Market Cockpit
 */
import React from 'react';
import { Card } from '@/components/common/Card';
import { Loading } from '@/components/common/Loading';
import { useBarrios } from '@/hooks/useBarrios';

export const OverviewPage: React.FC = () => {
  const { data: barrios, isLoading, error } = useBarrios();

  if (isLoading) return <Loading message="Cargando datos generales..." />;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="overview-page">
      <h1>Vista General</h1>
      <p className="page-description">
        Dashboard principal con KPIs clave del mercado inmobiliario de Barcelona
      </p>

      <div className="kpi-grid">
        <Card title="Total Barrios">
          <div className="kpi-value">{barrios?.length || 0}</div>
          <div className="kpi-label">Barrios analizados</div>
        </Card>

        <Card title="Estado del Sistema">
          <div className="kpi-value success">✓</div>
          <div className="kpi-label">Sistema operativo</div>
        </Card>

        <Card title="Última Actualización">
          <div className="kpi-value">2025</div>
          <div className="kpi-label">Año más reciente</div>
        </Card>
      </div>

      <Card title="Próximas funcionalidades">
        <ul>
          <li>📊 Análisis de rentabilidad bruta (Gross Yield)</li>
          <li>📈 Variación interanual de precios (YoY)</li>
          <li>🗺️ Mapas de calor de precios</li>
          <li>💹 Correlaciones demográficas</li>
        </ul>
      </Card>

      <style>{`
        .overview-page {
          max-width: 1400px;
        }
        .page-description {
          color: #6b7280;
          margin-bottom: 2rem;
        }
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }
        .kpi-value {
          font-size: 2.5rem;
          font-weight: 700;
          color: #1a1a1a;
          margin-bottom: 0.5rem;
        }
        .kpi-value.success {
          color: #10b981;
        }
        .kpi-label {
          font-size: 0.875rem;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
      `}</style>
    </div>
  );
};
