/**
 * Sidebar Component - Navigation menu
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useUIStore } from '@/stores/uiStore';
import './Sidebar.css';

export const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  const navItems = [
    { path: '/', label: 'Vista General', icon: '📊' },
    { path: '/renta', label: 'Renta', icon: '💰' },
    { path: '/precios', label: 'Precios Vivienda', icon: '🏠' },
    { path: '/demografia', label: 'Demografía', icon: '👥' },
  ];

  return (
    <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <h2 className="sidebar-title">BCN Housing</h2>
        <button className="sidebar-toggle" onClick={toggleSidebar}>
          {sidebarOpen ? '‹' : '›'}
        </button>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
            end={item.path === '/'}
          >
            <span className="nav-icon">{item.icon}</span>
            {sidebarOpen && <span className="nav-label">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {sidebarOpen && <p className="sidebar-version">v0.1.0</p>}
      </div>
    </aside>
  );
};
