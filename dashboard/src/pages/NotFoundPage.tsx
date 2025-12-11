/**
 * 404 Not Found Page
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/common/Card';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="not-found-page" style={{ maxWidth: '600px', margin: '4rem auto', textAlign: 'center' }}>
      <Card>
        <h1 style={{ fontSize: '4rem', margin: '0 0 1rem 0' }}>404</h1>
        <h2>Página No Encontrada</h2>
        <p style={{ color: '#6b7280', margin: '1.5rem 0' }}>
          La página que buscas no existe o ha sido movida.
        </p>
        <Link
          to="/"
          style={{
            display: 'inline-block',
            background: '#3b82f6',
            color: 'white',
            padding: '0.75rem 1.5rem',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 600,
          }}
        >
          Volver al inicio
        </Link>
      </Card>
    </div>
  );
};
