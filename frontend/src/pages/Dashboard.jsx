import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { datasheetAPI } from '../api/client';

/**
 * Dashboard Page
 * 
 * Implements UI-003: Dashboard with datasheet overview
 * - Auto-polling when datasheets are processing
 * - Inline progress bars
 * - Refresh button
 */
function Dashboard() {
    const [datasheets, setDatasheets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({ total: 0, processing: 0, complete: 0 });
    const [lastRefresh, setLastRefresh] = useState(new Date());
    const intervalRef = useRef(null);

    // Initial load
    useEffect(() => {
        loadData();
    }, []);

    // Auto-polling when processing datasheets exist
    useEffect(() => {
        // Clear any existing interval
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        // Start polling if there are processing items
        if (stats.processing > 0) {
            console.log('[Dashboard] Starting auto-poll (processing:', stats.processing, ')');
            intervalRef.current = setInterval(() => {
                loadData(true); // silent refresh
            }, 3000); // Poll every 3 seconds
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [stats.processing]);

    const loadData = async (silent = false) => {
        if (!silent) setLoading(true);
        try {
            const response = await datasheetAPI.list(1, 20);
            setDatasheets(response.items || []);
            setLastRefresh(new Date());

            // Calculate stats
            const items = response.items || [];
            const processingStatuses = ['pending', 'parsing', 'extracting', 'processing_llm'];
            setStats({
                total: response.total || items.length,
                processing: items.filter(d => processingStatuses.includes(d.status)).length,
                complete: items.filter(d => d.status === 'complete').length,
            });
        } catch (error) {
            console.error('Dashboard load error:', error);
        } finally {
            if (!silent) setLoading(false);
        }
    };

    const isProcessing = (ds) => {
        return ['pending', 'parsing', 'extracting', 'processing_llm'].includes(ds.status);
    };

    const getStatusBadge = (status) => {
        const badges = {
            pending: { label: 'Pending', color: 'var(--text-muted)' },
            parsing: { label: 'Parsing', color: 'var(--warning)' },
            extracting: { label: 'Extracting', color: 'var(--warning)' },
            processing_llm: { label: 'Processing', color: 'var(--accent-primary)' },
            complete: { label: 'Ready', color: 'var(--success)' },
            error: { label: 'Error', color: 'var(--error)' },
        };
        const badge = badges[status] || badges.pending;
        return <span className="status-badge" style={{ background: badge.color }}>{badge.label}</span>;
    };

    const formatProgress = (ds) => {
        const percent = Math.round(ds.progress_percent || 0);
        return (
            <div className="progress-cell">
                <div className="mini-progress-bar">
                    <div
                        className="mini-progress-fill"
                        style={{ width: `${percent}%` }}
                    />
                </div>
                <span className="progress-text">{percent}%</span>
                {ds.progress_message && (
                    <span className="progress-message">{ds.progress_message}</span>
                )}
            </div>
        );
    };

    return (
        <div className="dashboard">
            <header className="page-header">
                <div>
                    <h1>Dashboard</h1>
                    <p className="text-muted">Manage your datasheet configurators</p>
                </div>
                <div className="header-actions">
                    <button
                        className="btn btn-ghost"
                        onClick={() => loadData()}
                        title="Refresh data"
                    >
                        🔄 Refresh
                    </button>
                    <Link to="/upload" className="btn btn-primary">
                        + Upload Datasheet
                    </Link>
                </div>
            </header>

            {/* Auto-refresh indicator */}
            {stats.processing > 0 && (
                <div className="auto-refresh-notice">
                    <span className="pulse-dot"></span>
                    Auto-refreshing... ({stats.processing} processing)
                    <span className="last-update">Last: {lastRefresh.toLocaleTimeString()}</span>
                </div>
            )}

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">📊</div>
                    <div className="stat-content">
                        <div className="stat-value">{stats.total}</div>
                        <div className="stat-label">Total Datasheets</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">⚡</div>
                    <div className="stat-content">
                        <div className="stat-value">{stats.processing}</div>
                        <div className="stat-label">Processing</div>
                    </div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">✅</div>
                    <div className="stat-content">
                        <div className="stat-value">{stats.complete}</div>
                        <div className="stat-label">Ready to Use</div>
                    </div>
                </div>
            </div>

            {/* Datasheets Table */}
            <div className="card mt-6">
                <div className="card-header">
                    <h3 className="card-title">Recent Datasheets</h3>
                </div>

                {loading ? (
                    <div className="skeleton-table">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="skeleton" style={{ height: '60px', marginBottom: '8px' }}></div>
                        ))}
                    </div>
                ) : datasheets.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-icon">📄</div>
                        <h3>No datasheets yet</h3>
                        <p className="text-muted">Upload your first PDF datasheet to get started</p>
                        <Link to="/upload" className="btn btn-primary mt-4">Upload Datasheet</Link>
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Manufacturer</th>
                                <th>Status</th>
                                <th>Progress</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {datasheets.map(ds => (
                                <tr key={ds.id}>
                                    <td className="font-medium">{ds.name}</td>
                                    <td className="text-muted">{ds.manufacturer || '—'}</td>
                                    <td>{getStatusBadge(ds.status)}</td>
                                    <td>
                                        {isProcessing(ds) ? formatProgress(ds) : (
                                            ds.status === 'complete' ? '✓ Done' : '—'
                                        )}
                                    </td>
                                    <td className="text-muted">{new Date(ds.created_at).toLocaleDateString()}</td>
                                    <td>
                                        {ds.status === 'complete' ? (
                                            <div className="action-buttons">
                                                <Link to={`/build/${ds.id}`} className="btn btn-primary btn-sm">
                                                    🔧 Build Part
                                                </Link>
                                                <Link to={`/configure/${ds.id}`} className="btn btn-secondary btn-sm">
                                                    Configure
                                                </Link>
                                            </div>
                                        ) : ds.status === 'error' ? (
                                            <button className="btn btn-ghost btn-sm" onClick={() => datasheetAPI.reprocess(ds.id).then(loadData)}>
                                                Retry
                                            </button>
                                        ) : (
                                            <span className="processing-indicator">
                                                <span className="spinner"></span>
                                                Processing...
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            <style>{`
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: var(--space-6);
        }

        .header-actions {
          display: flex;
          gap: var(--space-2);
        }

        .auto-refresh-notice {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-4);
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid var(--accent-primary);
          border-radius: var(--radius-sm);
          font-size: 0.75rem;
          color: var(--accent-primary);
          margin-bottom: var(--space-4);
        }

        .pulse-dot {
          width: 8px;
          height: 8px;
          background: var(--accent-primary);
          border-radius: 50%;
          animation: pulse 1.5s infinite;
        }

        .last-update {
          margin-left: auto;
          opacity: 0.7;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: var(--space-4);
        }

        .stat-card {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-5);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
        }

        .stat-icon {
          font-size: 2rem;
        }

        .stat-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--text-primary);
        }

        .stat-label {
          font-size: 0.875rem;
          color: var(--text-muted);
        }

        .data-table {
          width: 100%;
          border-collapse: collapse;
        }

        .data-table th,
        .data-table td {
          padding: var(--space-3) var(--space-4);
          text-align: left;
          border-bottom: 1px solid var(--border-subtle);
        }

        .data-table th {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted);
        }

        .data-table tr:hover {
          background: var(--bg-tertiary);
        }

        .status-badge {
          display: inline-block;
          padding: 2px 8px;
          font-size: 0.75rem;
          font-weight: 500;
          border-radius: var(--radius-full);
          color: white;
        }

        .progress-cell {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .mini-progress-bar {
          width: 100px;
          height: 6px;
          background: var(--bg-tertiary);
          border-radius: 3px;
          overflow: hidden;
        }

        .mini-progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
          border-radius: 3px;
          transition: width 0.3s ease;
        }

        .progress-text {
          font-size: 0.7rem;
          font-weight: 600;
          color: var(--accent-primary);
        }

        .progress-message {
          font-size: 0.65rem;
          color: var(--text-muted);
          max-width: 150px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .processing-indicator {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .spinner {
          width: 12px;
          height: 12px;
          border: 2px solid var(--border-subtle);
          border-top-color: var(--accent-primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .btn-sm {
          padding: var(--space-1) var(--space-3);
          font-size: 0.75rem;
        }

        .action-buttons {
          display: flex;
          gap: var(--space-2);
        }

        .font-medium {
          font-weight: 500;
        }

        .empty-state {
          text-align: center;
          padding: var(--space-10);
        }

        .empty-icon {
          font-size: 3rem;
          margin-bottom: var(--space-4);
        }
      `}</style>
        </div>
    );
}

export default Dashboard;
