import { useState } from 'react';
import { Link } from 'react-router-dom';
import { partsAPI } from '../api/client';

/**
 * Search Page
 * 
 * Implements part search and filtering
 */
function Search() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const handleSearch = async (e) => {
        e?.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setSearched(true);

        try {
            const response = await partsAPI.search(query);
            setResults(response.items || []);
        } catch (error) {
            console.error('Search failed:', error);
            setResults([]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="search-page">
            <header className="page-header">
                <h1>Search Parts</h1>
                <p className="text-muted">Search for part numbers across all datasheets</p>
            </header>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="search-form">
                <div className="search-input-wrapper">
                    <input
                        type="text"
                        className="input search-input"
                        placeholder="Enter part number (e.g., D38999/24WB35P)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? <span className="spinner"></span> : '🔍 Search'}
                    </button>
                </div>
            </form>

            {/* Results */}
            {loading ? (
                <div className="card mt-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="skeleton" style={{ height: '60px', marginBottom: '8px' }}></div>
                    ))}
                </div>
            ) : searched && results.length === 0 ? (
                <div className="card mt-6">
                    <div className="empty-state">
                        <div className="empty-icon">🔍</div>
                        <h3>No results found</h3>
                        <p className="text-muted">Try a different search term or check your part number format</p>
                    </div>
                </div>
            ) : results.length > 0 ? (
                <div className="results-grid mt-6">
                    {results.map(part => (
                        <div key={part.id} className="result-card">
                            <div className="result-header">
                                <code className="part-number">{part.full_part_number}</code>
                            </div>
                            <div className="result-specs">
                                {Object.entries(part.field_values || {}).slice(0, 4).map(([key, value]) => (
                                    <div key={key} className="spec-item">
                                        <span className="spec-key">{key}:</span>
                                        <span className="spec-value">{value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            ) : !searched ? (
                <div className="card mt-6">
                    <div className="empty-state">
                        <div className="empty-icon">🔎</div>
                        <h3>Search for parts</h3>
                        <p className="text-muted">Enter a part number or keyword to find matching configurations</p>
                    </div>
                </div>
            ) : null}

            <style>{`
        .search-page {
          max-width: 900px;
        }

        .search-form {
          margin-bottom: var(--space-6);
        }

        .search-input-wrapper {
          display: flex;
          gap: var(--space-3);
        }

        .search-input {
          flex: 1;
          font-size: 1rem;
          padding: var(--space-4);
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: var(--space-4);
        }

        .result-card {
          padding: var(--space-4);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
          transition: all var(--transition-fast);
        }

        .result-card:hover {
          border-color: var(--accent-primary);
          box-shadow: var(--shadow-md);
        }

        .result-header {
          margin-bottom: var(--space-3);
        }

        .part-number {
          font-family: var(--font-mono);
          font-size: 1rem;
          color: var(--accent-secondary);
        }

        .result-specs {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-2);
        }

        .spec-item {
          font-size: 0.75rem;
          padding: 2px 6px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .spec-key {
          color: var(--text-muted);
        }

        .spec-value {
          color: var(--text-secondary);
          margin-left: 2px;
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

export default Search;
