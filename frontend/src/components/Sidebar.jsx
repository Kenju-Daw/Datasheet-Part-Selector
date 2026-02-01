import { NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { datasheetAPI } from '../api/client';

/**
 * Sidebar Component
 * 
 * Implements UI-010: Intuitive navigation
 */
function Sidebar() {
  const [datasheets, setDatasheets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDatasheets();
  }, []);

  const loadDatasheets = async () => {
    try {
      const response = await datasheetAPI.list(1, 5);
      setDatasheets(response.items || []);
    } catch (error) {
      console.error('Failed to load datasheets:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <span className="logo-icon">📊</span>
          <span className="logo-text">Part Selector</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🏠</span>
          <span className="nav-label">Dashboard</span>
        </NavLink>

        <NavLink to="/guided" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🤖</span>
          <span className="nav-label">Guided Selector</span>
        </NavLink>

        <NavLink to="/upload" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">📤</span>
          <span className="nav-label">Upload</span>
        </NavLink>

        <NavLink to="/search" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">🔍</span>
          <span className="nav-label">Search</span>
        </NavLink>

        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">⚙️</span>
          <span className="nav-label">Settings</span>
        </NavLink>
      </nav>

      <div className="sidebar-section">
        <div className="section-header">
          <span className="section-title">DATASHEETS</span>
        </div>

        <div className="datasheet-list">
          {loading ? (
            <div className="skeleton" style={{ height: '40px', marginBottom: '8px' }}></div>
          ) : datasheets.length === 0 ? (
            <p className="text-muted text-sm">No datasheets yet</p>
          ) : (
            datasheets.map(ds => (
              <NavLink
                key={ds.id}
                to={`/configure/${ds.id}`}
                className={({ isActive }) => `datasheet-item ${isActive ? 'active' : ''}`}
              >
                <span className="ds-status" data-status={ds.status}></span>
                <span className="ds-name">{ds.name}</span>
              </NavLink>
            ))
          )}
        </div>
      </div>

      <style>{`
        .sidebar {
          width: var(--sidebar-width);
          height: 100vh;
          position: fixed;
          left: 0;
          top: 0;
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-subtle);
          display: flex;
          flex-direction: column;
          overflow-y: auto;
        }

        .sidebar-header {
          padding: var(--space-5);
          border-bottom: 1px solid var(--border-subtle);
        }

        .logo {
          display: flex;
          align-items: center;
          gap: var(--space-3);
        }

        .logo-icon {
          font-size: 1.5rem;
        }

        .logo-text {
          font-weight: 600;
          font-size: 1rem;
          color: var(--text-primary);
        }

        .sidebar-nav {
          padding: var(--space-4);
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          transition: all var(--transition-fast);
          margin-bottom: var(--space-1);
        }

        .nav-item:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: var(--bg-tertiary);
          color: var(--accent-primary);
          border-left: 3px solid var(--accent-primary);
          margin-left: -3px;
        }

        .nav-icon {
          font-size: 1rem;
        }

        .sidebar-section {
          padding: var(--space-4);
          margin-top: auto;
        }

        .section-header {
          padding: var(--space-2) var(--space-4);
        }

        .section-title {
          font-size: 0.625rem;
          font-weight: 600;
          letter-spacing: 0.1em;
          color: var(--text-muted);
        }

        .datasheet-list {
          padding: var(--space-2);
        }

        .datasheet-item {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius-sm);
          color: var(--text-secondary);
          font-size: 0.875rem;
          transition: all var(--transition-fast);
        }

        .datasheet-item:hover {
          background: var(--bg-tertiary);
          color: var(--text-primary);
        }

        .datasheet-item.active {
          color: var(--accent-primary);
        }

        .ds-status {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--text-muted);
        }

        .ds-status[data-status="complete"] {
          background: var(--success);
        }

        .ds-status[data-status="processing"],
        .ds-status[data-status="parsing"],
        .ds-status[data-status="extracting"] {
          background: var(--warning);
          animation: pulse 1s infinite;
        }

        .ds-status[data-status="error"] {
          background: var(--error);
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .ds-name {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        @media (max-width: 768px) {
          .sidebar {
            display: none;
          }
        }
      `}</style>
    </aside>
  );
}

export default Sidebar;
