/**
 * AppLayout Component - Main layout wrapper
 */
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useUIStore } from '@/stores/uiStore';
import './AppLayout.css';

export const AppLayout: React.FC = () => {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="app-layout">
      <Sidebar />
      <div className={`main-container ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <Header />
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
