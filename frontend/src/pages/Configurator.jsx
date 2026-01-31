import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { datasheetAPI, partsAPI } from '../api/client';

/**
 * Configurator Page
 * 
 * Implements:
 * - CFG-001: Dynamic field loading
 * - CFG-002: Live part number preview
 * - CFG-003: Compatibility validation
 * - CFG-005: Required/optional field indication
 * - CFG-006: Field tooltips
 * - CFG-007: Copy to clipboard
 * - CFG-010: Exploded part number view
 */
function Configurator() {
    const { datasheetId } = useParams();

    const [datasheet, setDatasheet] = useState(null);
    const [schema, setSchema] = useState(null);
    const [fieldValues, setFieldValues] = useState({});
    const [partNumber, setPartNumber] = useState('');
    const [validation, setValidation] = useState({ is_valid: true, errors: [] });
    const [loading, setLoading] = useState(true);
    const [copied, setCopied] = useState(false);
    const [activeField, setActiveField] = useState(null);

    useEffect(() => {
        loadData();
    }, [datasheetId]);

    useEffect(() => {
        if (schema && Object.keys(fieldValues).length > 0) {
            generatePartNumber();
        }
    }, [fieldValues]);

    const loadData = async () => {
        try {
            const [dsData, schemaData] = await Promise.all([
                datasheetAPI.get(datasheetId),
                partsAPI.getSchema(datasheetId).catch(() => null)
            ]);

            setDatasheet(dsData);
            setSchema(schemaData);

            // Initialize field values with defaults
            if (schemaData?.fields) {
                const initial = {};
                schemaData.fields.forEach(f => {
                    if (f.allowed_values?.[0]) {
                        initial[f.code] = f.allowed_values[0].code;
                    }
                });
                setFieldValues(initial);
            }
        } catch (error) {
            console.error('Failed to load configurator:', error);
        } finally {
            setLoading(false);
        }
    };

    const generatePartNumber = async () => {
        try {
            const result = await partsAPI.configure(schema.id, fieldValues);
            setPartNumber(result.full_part_number);
            setValidation({ is_valid: result.is_valid, errors: result.validation_errors });
        } catch (error) {
            console.error('Part number generation failed:', error);
        }
    };

    const handleFieldChange = (code, value) => {
        setFieldValues(prev => ({ ...prev, [code]: value }));
    };

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(partNumber);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (e) {
            console.error('Copy failed:', e);
        }
    };

    if (loading) {
        return (
            <div className="configurator">
                <div className="skeleton" style={{ height: '200px', marginBottom: '24px' }}></div>
                <div className="skeleton" style={{ height: '400px' }}></div>
            </div>
        );
    }

    if (!datasheet) {
        return (
            <div className="configurator">
                <div className="empty-state">
                    <h3>Datasheet not found</h3>
                    <Link to="/" className="btn btn-primary mt-4">Back to Dashboard</Link>
                </div>
            </div>
        );
    }

    if (!schema) {
        return (
            <div className="configurator">
                <h1>{datasheet.name}</h1>
                <div className="card mt-6">
                    <div className="empty-state">
                        <div className="empty-icon">⏳</div>
                        <h3>Schema not ready</h3>
                        <p className="text-muted">This datasheet is still processing. Check back soon.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="configurator">
            <header className="page-header">
                <div>
                    <h1>{datasheet.name}</h1>
                    <p className="text-muted">{datasheet.manufacturer || 'Configure your part number'}</p>
                </div>
            </header>

            {/* Part Number Builder (CFG-010) */}
            <div className="part-number-builder">
                <button className="copy-btn" onClick={handleCopy} title="Copy to clipboard">
                    {copied ? '✓' : '📋'}
                </button>

                <div className="part-number-display">{partNumber || schema.part_number_prefix || '—'}</div>

                {/* Exploded View (CFG-010) */}
                <div className="part-number-segments">
                    {schema.fields?.map(field => {
                        const value = fieldValues[field.code];
                        const valueInfo = field.allowed_values?.find(v => v.code === value);

                        return (
                            <div
                                key={field.code}
                                className={`part-segment ${activeField === field.code ? 'active' : ''}`}
                                onClick={() => setActiveField(field.code)}
                                title={valueInfo?.description || field.description}
                            >
                                <div className="segment-code">{value || '?'}</div>
                                <div className="segment-label">{field.name}</div>
                            </div>
                        );
                    })}
                </div>

                {!validation.is_valid && (
                    <div className="validation-errors">
                        {validation.errors.map((err, i) => (
                            <div key={i} className="error-item">⚠️ {err}</div>
                        ))}
                    </div>
                )}
            </div>

            {/* Field Selectors */}
            <div className="fields-grid mt-6">
                {schema.fields?.map(field => (
                    <div key={field.code} className="field-card">
                        <div className="field-header">
                            <label className="input-label">
                                {field.name}
                                {field.is_required && <span className="required">*</span>}
                            </label>
                            {field.description && (
                                <span className="field-tooltip" title={field.description}>ℹ️</span>
                            )}
                        </div>

                        <select
                            className="select"
                            value={fieldValues[field.code] || ''}
                            onChange={(e) => handleFieldChange(field.code, e.target.value)}
                        >
                            {!field.is_required && <option value="">— Select —</option>}
                            {field.allowed_values?.map(option => (
                                <option key={option.code} value={option.code}>
                                    {option.code} — {option.name}
                                </option>
                            ))}
                        </select>

                        {/* Current Selection Description */}
                        {fieldValues[field.code] && (
                            <div className="field-description">
                                {field.allowed_values?.find(v => v.code === fieldValues[field.code])?.description}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Toast for copy */}
            {copied && (
                <div className="toast success">
                    ✓ Part number copied to clipboard
                </div>
            )}

            <style>{`
        .configurator {
          max-width: 900px;
        }

        .validation-errors {
          margin-top: var(--space-4);
          padding: var(--space-3);
          background: rgba(248, 113, 113, 0.1);
          border-radius: var(--radius-sm);
        }

        .error-item {
          font-size: 0.875rem;
          color: var(--error);
        }

        .fields-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: var(--space-4);
        }

        .field-card {
          padding: var(--space-4);
          background: var(--bg-secondary);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-md);
        }

        .field-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-2);
        }

        .field-tooltip {
          cursor: help;
          opacity: 0.6;
        }

        .field-description {
          margin-top: var(--space-2);
          font-size: 0.75rem;
          color: var(--text-muted);
          font-style: italic;
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

export default Configurator;
