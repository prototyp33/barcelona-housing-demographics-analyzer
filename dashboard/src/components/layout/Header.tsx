/**
 * Header Component
 */
import React from 'react';
import { useUIStore } from '@/stores/uiStore';
import './Header.css';

export const Header: React.FC = () => {
  const { toggleTheme, theme } = useUIStore();

  return (
    <header className="header">
      <h1 className="header-title">Barcelona Housing Demographics Analyzer</h1>
      <div className="header-actions">
        <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
      </div>
    </header>
  );
};
