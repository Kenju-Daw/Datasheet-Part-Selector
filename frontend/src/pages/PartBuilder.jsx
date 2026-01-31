import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const API_BASE = 'http://localhost:8000/api/parts';

// =============================================================================
// REFERENCE DATA - Contact sizes, connectors, finishes with detailed specs
// =============================================================================

const CONTACT_SIZES = [
    {
        code: '22D',
        label: '22D',
        awg: '24-28 AWG',
        amps: 5,
        description: 'Standard signal contact for low-power applications'
    },
    {
        code: '22',
        label: '22',
        awg: '22-26 AWG',
        amps: 5,
        description: 'General purpose signal contact'
    },
    {
        code: '20',
        label: '20',
        awg: '20-24 AWG',
        amps: 7.5,
        description: 'Enhanced signal contact for moderate power'
    },
    {
        code: '16',
        label: '16',
        awg: '16-20 AWG',
        amps: 13,
        description: 'Power contact for medium current applications'
    },
    {
        code: '12',
        label: '12',
        awg: '12-16 AWG',
        amps: 23,
        description: 'High-power contact for demanding applications'
    },
    {
        code: '10',
        label: '10 Power',
        awg: '10-14 AWG',
        amps: 33,
        description: 'Heavy-duty power contact'
    },
    {
        code: '8',
        label: '8 Power/Coax',
        awg: '8-12 AWG',
        amps: 46,
        description: 'Maximum power or coaxial contact'
    },
];

const CONNECTOR_TYPES = [
    {
        code: '20',
        name: 'Wall Mount Receptacle',
        is_standard: true,
        description: 'Panel-mounted receptacle with flange for wall/bulkhead installation'
    },
    {
        code: '24',
        name: 'Jam Nut Receptacle',
        is_standard: true,
        description: 'Panel-mounted with jam nut, most common receptacle style'
    },
    {
        code: '26',
        name: 'Straight Plug',
        is_standard: true,
        description: 'Cable-mounted plug that mates with receptacles'
    },
    {
        code: '21',
        name: 'Box Mount Receptacle (Hermetic)',
        is_standard: false,
        description: 'Sealed receptacle for pressure/vacuum environments'
    },
    {
        code: '23',
        name: 'Jam Nut Receptacle (Hermetic)',
        is_standard: false,
        description: 'Hermetically sealed jam nut receptacle'
    },
];

const SHELL_FINISHES = [
    {
        code: 'F',
        name: 'Electroless Nickel',
        rohs: true,
        description: 'Corrosion-resistant, RoHS compliant alternative to cadmium'
    },
    {
        code: 'T',
        name: 'Durmalon',
        rohs: true,
        description: 'Black non-reflective finish, ideal for stealth applications'
    },
    {
        code: 'W',
        name: 'Olive Drab Cadmium',
        rohs: false,
        description: 'Military standard finish, excellent salt spray resistance'
    },
    {
        code: 'K',
        name: 'Stainless Steel',
        rohs: true,
        description: 'Passivated stainless, best for marine environments'
    },
    {
        code: 'Z',
        name: 'Zinc-Nickel',
        rohs: true,
        description: 'High corrosion resistance, RoHS compliant'
    },
];

const KEY_POSITIONS = [
    { code: 'N', name: 'Normal', description: 'Standard keying position (0°)' },
    { code: 'A', name: 'Position A', description: 'Alternate keying (60°)' },
    { code: 'B', name: 'Position B', description: 'Alternate keying (120°)' },
    { code: 'C', name: 'Position C', description: 'Alternate keying (180°)' },
    { code: 'D', name: 'Position D', description: 'Alternate keying (240°)' },
    { code: 'E', name: 'Position E', description: 'Alternate keying (300°)' },
];

// =============================================================================
// TOOLTIP COMPONENT - Reusable info popup
// =============================================================================

function Tooltip({ children, content, position = 'top' }) {
    const [visible, setVisible] = useState(false);

    return (
        <div
            className="tooltip-wrapper"
            onMouseEnter={() => setVisible(true)}
            onMouseLeave={() => setVisible(false)}
        >
            {children}
            {visible && content && (
                <div className={`tooltip-popup ${position}`}>
                    {content}
                </div>
            )}
        </div>
    );
}

// =============================================================================
// INFO BADGE - Shows details for selected options
// =============================================================================

function InfoBadge({ label, value, detail, icon = 'ℹ️' }) {
    return (
        <div className="info-badge">
            <span className="info-icon">{icon}</span>
            <span className="info-label">{label}:</span>
            <strong className="info-value">{value}</strong>
            {detail && <span className="info-detail">({detail})</span>}
        </div>
    );
}

// =============================================================================
// SELECTION CARD - Displays current selection with explanation
// =============================================================================

function SelectionSummary({ selections }) {
    if (!selections || selections.length === 0) return null;

    return (
        <div className="selection-summary">
            {selections.map((s, i) => (
                <div key={i} className="selection-item">
                    <span className="selection-label">{s.label}:</span>
                    <span className="selection-value">{s.value}</span>
                    <Tooltip content={s.explanation}>
                        <span className="selection-info">ℹ️</span>
                    </Tooltip>
                </div>
            ))}
        </div>
    );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PartBuilder() {
    const { datasheetId } = useParams();

    // State
    const [currentStep, setCurrentStep] = useState(1);
    const [contactRequirements, setContactRequirements] = useState([{ size: '22D', quantity: 10 }]);
    const [insertMatches, setInsertMatches] = useState([]);
    const [selectedInsert, setSelectedInsert] = useState(null);
    const [searching, setSearching] = useState(false);
    const [config, setConfig] = useState({
        connectorType: '24',
        finish: 'F',
        contactType: 'P',
        keyPosition: 'N',
        shellClass: 'E'
    });
    const [generatedPN, setGeneratedPN] = useState(null);
    const [builderData, setBuilderData] = useState(null);
    const [copied, setCopied] = useState(false);
    const [activeTooltip, setActiveTooltip] = useState(null);

    // Load reference data
    useEffect(() => {
        fetch(`${API_BASE}/builder-data/${datasheetId}`)
            .then(res => res.ok ? res.json() : null)
            .then(data => data && setBuilderData(data))
            .catch(console.error);
    }, [datasheetId]);

    // Computed values
    const totalContacts = contactRequirements.reduce((sum, r) => sum + r.quantity, 0);
    const connectorTypes = builderData?.connector_types || CONNECTOR_TYPES;
    const finishes = builderData?.finishes || SHELL_FINISHES;

    // Helper to get current selections with explanations
    const getCurrentSelections = () => {
        const selections = [];

        if (selectedInsert) {
            selections.push({
                label: 'Insert',
                value: selectedInsert.code,
                explanation: `Shell size ${selectedInsert.shell_size} with ${selectedInsert.total_contacts} positions`
            });
        }

        const ct = connectorTypes.find(t => t.code === config.connectorType);
        if (ct) {
            selections.push({
                label: 'Type',
                value: ct.name,
                explanation: ct.description
            });
        }

        const fin = finishes.find(f => f.code === config.finish);
        if (fin) {
            selections.push({
                label: 'Finish',
                value: fin.name,
                explanation: fin.description
            });
        }

        const key = KEY_POSITIONS.find(k => k.code === config.keyPosition);
        if (key) {
            selections.push({
                label: 'Key',
                value: key.name,
                explanation: key.description
            });
        }

        return selections;
    };

    // Handlers
    const addContactRow = () => {
        setContactRequirements([...contactRequirements, { size: '22D', quantity: 1 }]);
    };

    const removeContactRow = (index) => {
        setContactRequirements(contactRequirements.filter((_, i) => i !== index));
    };

    const updateContactRow = (index, field, value) => {
        const updated = [...contactRequirements];
        updated[index][field] = field === 'quantity' ? parseInt(value) || 0 : value;
        setContactRequirements(updated);
    };

    const searchInserts = async () => {
        setSearching(true);
        try {
            const res = await fetch(`${API_BASE}/search-inserts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ datasheet_id: datasheetId, requirements: contactRequirements })
            });
            if (res.ok) {
                const data = await res.json();
                setInsertMatches(data.matches);
                setCurrentStep(2);
            }
        } catch (e) {
            console.error('Insert search failed:', e);
        } finally {
            setSearching(false);
        }
    };

    const selectInsert = (insert) => {
        setSelectedInsert(insert);
        setCurrentStep(3);
    };

    const generatePartNumber = async () => {
        try {
            const res = await fetch(`${API_BASE}/generate-part-number`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    insert_code: selectedInsert.code,
                    connector_type: config.connectorType,
                    finish_code: config.finish,
                    contact_type: config.contactType,
                    key_position: config.keyPosition,
                    shell_class: config.shellClass
                })
            });
            if (res.ok) {
                const data = await res.json();
                setGeneratedPN(data);
                setCurrentStep(4);
            }
        } catch (e) {
            console.error('Part number generation failed:', e);
        }
    };

    const handleCopy = async () => {
        if (generatedPN) {
            await navigator.clipboard.writeText(generatedPN.full_part_number);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Get contact size info
    const getContactInfo = (code) => CONTACT_SIZES.find(c => c.code === code) || CONTACT_SIZES[0];

    // ==========================================================================
    // RENDER
    // ==========================================================================

    return (
        <div className="part-builder">
            {/* Header */}
            <header className="page-header">
                <div>
                    <Link to="/" className="back-link">← Dashboard</Link>
                    <h1>🔧 Part Builder</h1>
                    <p className="subtitle">D38999 Connector Configuration</p>
                </div>
            </header>

            {/* Progress Steps */}
            <nav className="step-progress">
                {[
                    { num: 1, label: 'Requirements', icon: '📋' },
                    { num: 2, label: 'Insert', icon: '🔍' },
                    { num: 3, label: 'Configure', icon: '⚙️' },
                    { num: 4, label: 'Result', icon: '✅' }
                ].map(step => (
                    <button
                        key={step.num}
                        className={`step ${currentStep >= step.num ? 'active' : ''} ${currentStep === step.num ? 'current' : ''}`}
                        onClick={() => step.num < currentStep && setCurrentStep(step.num)}
                        disabled={step.num > currentStep}
                    >
                        <span className="step-icon">{step.icon}</span>
                        <span className="step-label">{step.label}</span>
                    </button>
                ))}
            </nav>

            {/* ================================================================ */}
            {/* STEP 1: Contact Requirements */}
            {/* ================================================================ */}
            {currentStep === 1 && (
                <section className="card step-card">
                    <h2>📋 What contacts do you need?</h2>
                    <p className="help-text">Select contact sizes and quantities. AWG and current ratings shown.</p>

                    <table className="requirements-table">
                        <thead>
                            <tr>
                                <th>Contact Size</th>
                                <th>AWG Range</th>
                                <th>Current</th>
                                <th>Qty</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {contactRequirements.map((req, idx) => {
                                const info = getContactInfo(req.size);
                                return (
                                    <tr key={idx}>
                                        <td>
                                            <Tooltip content={info.description}>
                                                <select
                                                    value={req.size}
                                                    onChange={(e) => updateContactRow(idx, 'size', e.target.value)}
                                                    className="select"
                                                >
                                                    {CONTACT_SIZES.map(s => (
                                                        <option key={s.code} value={s.code}>
                                                            {s.label}
                                                        </option>
                                                    ))}
                                                </select>
                                            </Tooltip>
                                        </td>
                                        <td className="awg-cell">
                                            <span className="awg-badge">{info.awg}</span>
                                        </td>
                                        <td className="amps-cell">
                                            <span className="amps-badge">{info.amps}A</span>
                                        </td>
                                        <td>
                                            <input
                                                type="number"
                                                min="1"
                                                value={req.quantity}
                                                onChange={(e) => updateContactRow(idx, 'quantity', e.target.value)}
                                                className="input qty-input"
                                            />
                                        </td>
                                        <td>
                                            {contactRequirements.length > 1 && (
                                                <button
                                                    className="btn btn-ghost btn-sm"
                                                    onClick={() => removeContactRow(idx)}
                                                    title="Remove"
                                                >
                                                    ✕
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>

                    <div className="requirements-actions">
                        <button className="btn btn-ghost" onClick={addContactRow}>
                            + Add Size
                        </button>
                        <div className="total-badge">
                            Total: <strong>{totalContacts}</strong> contacts
                        </div>
                    </div>

                    <div className="step-nav">
                        <button
                            className="btn btn-primary"
                            onClick={searchInserts}
                            disabled={totalContacts === 0 || searching}
                        >
                            {searching ? '🔄 Searching...' : 'Find Inserts →'}
                        </button>
                    </div>
                </section>
            )}

            {/* ================================================================ */}
            {/* STEP 2: Insert Selection */}
            {/* ================================================================ */}
            {currentStep === 2 && (
                <section className="card step-card">
                    <h2>🔍 Select Insert Arrangement</h2>
                    <p className="help-text">
                        {insertMatches.length} compatible insert{insertMatches.length !== 1 && 's'} for {totalContacts} contacts
                    </p>

                    {insertMatches.length === 0 ? (
                        <div className="empty-state">
                            <p>No matches found. Try different contact requirements.</p>
                            <button className="btn btn-secondary" onClick={() => setCurrentStep(1)}>
                                ← Modify
                            </button>
                        </div>
                    ) : (
                        <div className="insert-grid">
                            {insertMatches.map(insert => {
                                const unavailable = !insert.is_standard && insert.match_type === 'over';
                                return (
                                    <Tooltip
                                        key={insert.code}
                                        content={`${insert.service_rating} service • ${insert.total_contacts} total positions`}
                                    >
                                        <div
                                            className={`insert-card ${insert.match_type} ${unavailable ? 'unavailable' : ''}`}
                                            onClick={() => !unavailable && selectInsert(insert)}
                                        >
                                            <header className="insert-header">
                                                <span className="insert-code">{insert.code}</span>
                                                <span className={`badge ${insert.match_type}`}>
                                                    {insert.match_type === 'exact' && '✓ Exact'}
                                                    {insert.match_type === 'close' && '≈ Close'}
                                                    {insert.match_type === 'over' && '+ Over'}
                                                </span>
                                            </header>

                                            <div className="insert-specs">
                                                <span>Shell <strong>{insert.shell_size}</strong></span>
                                                <span>{insert.total_contacts} pos</span>
                                            </div>

                                            <div className="contact-chips">
                                                {Object.entries(insert.contact_breakdown).map(([size, qty]) => (
                                                    <span key={size} className="chip">
                                                        {qty}× {size}
                                                    </span>
                                                ))}
                                            </div>

                                            {Object.values(insert.extra_positions).some(v => v > 0) && (
                                                <div className="extra-note">
                                                    +{Object.values(insert.extra_positions).reduce((a, b) => a + b, 0)} extra positions
                                                </div>
                                            )}

                                            <footer className={`availability ${insert.is_standard ? 'in-stock' : 'special'}`}>
                                                {insert.is_standard ? '✓ In Stock' : unavailable ? '🚫 N/A' : '⏳ Special'}
                                            </footer>
                                        </div>
                                    </Tooltip>
                                );
                            })}
                        </div>
                    )}

                    <div className="step-nav">
                        <button className="btn btn-ghost" onClick={() => setCurrentStep(1)}>
                            ← Back
                        </button>
                    </div>
                </section>
            )}

            {/* ================================================================ */}
            {/* STEP 3: Connector Configuration */}
            {/* ================================================================ */}
            {currentStep === 3 && selectedInsert && (
                <section className="card step-card">
                    <h2>⚙️ Configure Connector</h2>
                    <p className="help-text">
                        Insert <strong>{selectedInsert.code}</strong> • Shell {selectedInsert.shell_size} • {selectedInsert.total_contacts} positions
                    </p>

                    <div className="config-grid">
                        {/* Connector Type */}
                        <div className="config-field">
                            <label>
                                Connector Type
                                <Tooltip content="Determines mounting style and mating interface">
                                    <span className="info-icon">ℹ️</span>
                                </Tooltip>
                            </label>
                            <select
                                value={config.connectorType}
                                onChange={(e) => setConfig({ ...config, connectorType: e.target.value })}
                                className="select"
                            >
                                {connectorTypes.map(t => (
                                    <option key={t.code} value={t.code}>
                                        {t.code} - {t.name}
                                    </option>
                                ))}
                            </select>
                            {(() => {
                                const ct = connectorTypes.find(t => t.code === config.connectorType);
                                return ct && <p className="field-hint">{ct.description}</p>;
                            })()}
                        </div>

                        {/* Shell Finish */}
                        <div className="config-field">
                            <label>
                                Shell Finish
                                <Tooltip content="Plating type affects corrosion resistance and RoHS compliance">
                                    <span className="info-icon">ℹ️</span>
                                </Tooltip>
                            </label>
                            <select
                                value={config.finish}
                                onChange={(e) => setConfig({ ...config, finish: e.target.value })}
                                className="select"
                            >
                                {finishes.map(f => (
                                    <option key={f.code} value={f.code}>
                                        {f.code} - {f.name} {f.rohs ? '✓' : ''}
                                    </option>
                                ))}
                            </select>
                            {(() => {
                                const fin = finishes.find(f => f.code === config.finish);
                                return fin && (
                                    <p className="field-hint">
                                        {fin.description}
                                        {!fin.rohs && <span className="warning"> ⚠️ Not RoHS</span>}
                                    </p>
                                );
                            })()}
                        </div>

                        {/* Contact Type */}
                        <div className="config-field">
                            <label>
                                Contact Type
                                <Tooltip content="Pin (male) or Socket (female) contacts">
                                    <span className="info-icon">ℹ️</span>
                                </Tooltip>
                            </label>
                            <div className="radio-group">
                                <label className={config.contactType === 'P' ? 'active' : ''}>
                                    <input
                                        type="radio"
                                        value="P"
                                        checked={config.contactType === 'P'}
                                        onChange={(e) => setConfig({ ...config, contactType: e.target.value })}
                                    />
                                    <span className="radio-label">📍 Pin (P)</span>
                                </label>
                                <label className={config.contactType === 'S' ? 'active' : ''}>
                                    <input
                                        type="radio"
                                        value="S"
                                        checked={config.contactType === 'S'}
                                        onChange={(e) => setConfig({ ...config, contactType: e.target.value })}
                                    />
                                    <span className="radio-label">⚪ Socket (S)</span>
                                </label>
                            </div>
                        </div>

                        {/* Key Position */}
                        <div className="config-field">
                            <label>
                                Key Position
                                <Tooltip content="Prevents mismating with connectors using different keys">
                                    <span className="info-icon">ℹ️</span>
                                </Tooltip>
                            </label>
                            <div className="key-grid">
                                {KEY_POSITIONS.map(k => (
                                    <Tooltip key={k.code} content={k.description}>
                                        <button
                                            className={`key-btn ${config.keyPosition === k.code ? 'active' : ''}`}
                                            onClick={() => setConfig({ ...config, keyPosition: k.code })}
                                        >
                                            {k.code}
                                        </button>
                                    </Tooltip>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Current Selection Summary */}
                    <SelectionSummary selections={getCurrentSelections()} />

                    <div className="step-nav">
                        <button className="btn btn-ghost" onClick={() => setCurrentStep(2)}>
                            ← Back
                        </button>
                        <button className="btn btn-primary" onClick={generatePartNumber}>
                            Generate PN →
                        </button>
                    </div>
                </section>
            )}

            {/* ================================================================ */}
            {/* STEP 4: Generated Part Number */}
            {/* ================================================================ */}
            {currentStep === 4 && generatedPN && (
                <section className="card step-card result-card">
                    <h2>✅ Your Part Number</h2>

                    <div className="pn-display" onClick={handleCopy}>
                        <code className="pn-text">{generatedPN.full_part_number}</code>
                        <button className="copy-btn">{copied ? '✓ Copied' : '📋 Copy'}</button>
                    </div>

                    <div className={`status-banner ${generatedPN.is_standard ? 'standard' : 'special'}`}>
                        {generatedPN.availability_note}
                    </div>

                    {/* Part Number Breakdown */}
                    <div className="pn-breakdown">
                        <h3>📐 Part Number Breakdown</h3>
                        <div className="breakdown-grid">
                            {Object.entries(generatedPN.breakdown).map(([key, value]) => (
                                <div key={key} className="breakdown-item">
                                    <span className="breakdown-label">{key.replace('_', ' ')}</span>
                                    <strong className="breakdown-value">{value}</strong>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Contact Ordering Info */}
                    <div className="contact-ordering">
                        <h3>📦 Contact Order Info</h3>
                        <table className="ordering-table">
                            <thead>
                                <tr>
                                    <th>Size</th>
                                    <th>AWG</th>
                                    <th>Type</th>
                                    <th>Qty</th>
                                    <th>Part Number</th>
                                </tr>
                            </thead>
                            <tbody>
                                {contactRequirements.map((req, idx) => {
                                    const info = getContactInfo(req.size);
                                    const pnPrefix = config.contactType === 'P' ? '58' : '56';
                                    const pnSuffix = req.size === '22D' ? '360' : req.size === '16' ? '364' : '348';
                                    return (
                                        <tr key={idx}>
                                            <td>{req.size}</td>
                                            <td><span className="awg-badge small">{info.awg}</span></td>
                                            <td>{config.contactType === 'P' ? 'Pin' : 'Socket'}</td>
                                            <td>{req.quantity}</td>
                                            <td className="mono">M39029/{pnPrefix}-{pnSuffix}</td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    <div className="step-nav">
                        <button className="btn btn-ghost" onClick={() => setCurrentStep(1)}>
                            ← Start Over
                        </button>
                        <button className="btn btn-secondary" onClick={() => setCurrentStep(3)}>
                            Modify Config
                        </button>
                    </div>
                </section>
            )}

            {/* Toast */}
            {copied && <div className="toast">✓ Copied to clipboard</div>}

            {/* ================================================================ */}
            {/* STYLES */}
            {/* ================================================================ */}
            <style>{`
                .part-builder {
                    max-width: 900px;
                    margin: 0 auto;
                    padding: var(--space-6);
                }

                /* Header */
                .page-header {
                    margin-bottom: var(--space-6);
                }
                .page-header h1 {
                    margin: var(--space-2) 0;
                    font-size: 1.75rem;
                }
                .subtitle {
                    color: var(--text-muted);
                    margin: 0;
                }
                .back-link {
                    color: var(--text-muted);
                    text-decoration: none;
                    font-size: 0.875rem;
                }
                .back-link:hover { color: var(--accent-primary); }

                /* Progress Steps */
                .step-progress {
                    display: flex;
                    gap: var(--space-2);
                    margin-bottom: var(--space-6);
                    padding: var(--space-3);
                    background: var(--bg-secondary);
                    border-radius: var(--radius-lg);
                }
                .step {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: var(--space-3);
                    background: transparent;
                    border: none;
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    opacity: 0.5;
                    transition: all 0.2s;
                }
                .step:disabled { cursor: not-allowed; }
                .step.active { opacity: 1; }
                .step.current {
                    background: var(--accent-primary);
                    color: white;
                }
                .step-icon { font-size: 1.25rem; }
                .step-label { font-size: 0.75rem; margin-top: var(--space-1); }

                /* Cards */
                .card {
                    background: var(--bg-secondary);
                    border-radius: var(--radius-lg);
                    padding: var(--space-6);
                    border: 1px solid var(--border-subtle);
                }
                .step-card h2 {
                    margin: 0 0 var(--space-2) 0;
                    font-size: 1.25rem;
                }
                .help-text {
                    color: var(--text-muted);
                    margin: 0 0 var(--space-4) 0;
                    font-size: 0.875rem;
                }

                /* Requirements Table */
                .requirements-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: var(--space-4);
                }
                .requirements-table th {
                    text-align: left;
                    padding: var(--space-2) var(--space-3);
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    border-bottom: 1px solid var(--border-subtle);
                }
                .requirements-table td {
                    padding: var(--space-2) var(--space-3);
                    vertical-align: middle;
                }
                .awg-cell, .amps-cell {
                    white-space: nowrap;
                }
                .awg-badge {
                    background: var(--bg-tertiary);
                    padding: 2px 8px;
                    border-radius: var(--radius-full);
                    font-size: 0.75rem;
                    font-family: monospace;
                }
                .awg-badge.small {
                    font-size: 0.65rem;
                    padding: 1px 6px;
                }
                .amps-badge {
                    background: var(--accent-primary);
                    color: white;
                    padding: 2px 8px;
                    border-radius: var(--radius-full);
                    font-size: 0.75rem;
                    font-weight: 600;
                }
                .qty-input {
                    width: 70px;
                    text-align: center;
                }
                .requirements-actions {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-4);
                }
                .total-badge {
                    background: var(--bg-tertiary);
                    padding: var(--space-2) var(--space-4);
                    border-radius: var(--radius-full);
                    font-size: 0.875rem;
                }

                /* Insert Grid */
                .insert-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: var(--space-3);
                    margin-bottom: var(--space-4);
                }
                .insert-card {
                    padding: var(--space-4);
                    background: var(--bg-primary);
                    border: 2px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .insert-card:hover:not(.unavailable) {
                    border-color: var(--accent-primary);
                    transform: translateY(-2px);
                }
                .insert-card.exact { border-color: var(--success); }
                .insert-card.close { border-color: var(--warning); }
                .insert-card.unavailable {
                    opacity: 0.4;
                    cursor: not-allowed;
                }
                .insert-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-2);
                }
                .insert-code {
                    font-size: 1.1rem;
                    font-weight: 700;
                    color: var(--accent-primary);
                }
                .badge {
                    padding: 2px 8px;
                    border-radius: var(--radius-full);
                    font-size: 0.65rem;
                    font-weight: 600;
                }
                .badge.exact { background: var(--success); color: white; }
                .badge.close { background: var(--warning); color: black; }
                .badge.over { background: var(--text-muted); color: white; }
                .insert-specs {
                    display: flex;
                    gap: var(--space-3);
                    font-size: 0.8rem;
                    color: var(--text-muted);
                    margin-bottom: var(--space-2);
                }
                .contact-chips {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 4px;
                    margin-bottom: var(--space-2);
                }
                .chip {
                    padding: 2px 6px;
                    background: var(--bg-tertiary);
                    border-radius: 4px;
                    font-size: 0.7rem;
                    font-family: monospace;
                }
                .extra-note {
                    font-size: 0.7rem;
                    color: var(--text-muted);
                    margin-bottom: var(--space-2);
                }
                .availability {
                    font-size: 0.75rem;
                    font-weight: 600;
                    padding: var(--space-1) 0;
                    border-top: 1px solid var(--border-subtle);
                }
                .availability.in-stock { color: var(--success); }
                .availability.special { color: var(--warning); }

                /* Config Grid */
                .config-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: var(--space-4);
                    margin-bottom: var(--space-4);
                }
                @media (max-width: 600px) {
                    .config-grid { grid-template-columns: 1fr; }
                }
                .config-field label {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    margin-bottom: var(--space-2);
                    font-weight: 600;
                    font-size: 0.875rem;
                }
                .info-icon {
                    font-size: 0.75rem;
                    opacity: 0.6;
                    cursor: help;
                }
                .field-hint {
                    margin: var(--space-1) 0 0 0;
                    font-size: 0.75rem;
                    color: var(--text-muted);
                }
                .field-hint .warning { color: var(--warning); }
                .radio-group {
                    display: flex;
                    gap: var(--space-2);
                }
                .radio-group label {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    padding: var(--space-3);
                    background: var(--bg-primary);
                    border: 2px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-weight: normal;
                }
                .radio-group label.active {
                    border-color: var(--accent-primary);
                    background: rgba(var(--accent-primary-rgb), 0.1);
                }
                .radio-group input { display: none; }
                .key-grid {
                    display: grid;
                    grid-template-columns: repeat(6, 1fr);
                    gap: var(--space-2);
                }
                .key-btn {
                    padding: var(--space-2);
                    background: var(--bg-primary);
                    border: 2px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.2s;
                }
                .key-btn:hover { border-color: var(--accent-primary); }
                .key-btn.active {
                    background: var(--accent-primary);
                    color: white;
                    border-color: var(--accent-primary);
                }

                /* Selection Summary */
                .selection-summary {
                    display: flex;
                    flex-wrap: wrap;
                    gap: var(--space-3);
                    padding: var(--space-3);
                    background: var(--bg-tertiary);
                    border-radius: var(--radius-md);
                    margin-bottom: var(--space-4);
                }
                .selection-item {
                    display: flex;
                    align-items: center;
                    gap: var(--space-1);
                    font-size: 0.8rem;
                }
                .selection-label { color: var(--text-muted); }
                .selection-info { cursor: help; opacity: 0.6; }

                /* Result Card */
                .result-card { text-align: center; }
                .pn-display {
                    display: inline-flex;
                    align-items: center;
                    gap: var(--space-3);
                    padding: var(--space-4) var(--space-6);
                    background: var(--bg-tertiary);
                    border-radius: var(--radius-lg);
                    cursor: pointer;
                    margin-bottom: var(--space-4);
                }
                .pn-text {
                    font-size: 1.5rem;
                    font-weight: 700;
                    font-family: monospace;
                    color: var(--accent-primary);
                }
                .copy-btn {
                    padding: var(--space-2) var(--space-3);
                    background: var(--accent-primary);
                    color: white;
                    border: none;
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-size: 0.875rem;
                }
                .status-banner {
                    padding: var(--space-3);
                    border-radius: var(--radius-md);
                    margin-bottom: var(--space-4);
                    font-weight: 600;
                }
                .status-banner.standard { background: rgba(34, 197, 94, 0.1); color: var(--success); }
                .status-banner.special { background: rgba(234, 179, 8, 0.1); color: var(--warning); }

                /* Breakdown */
                .pn-breakdown, .contact-ordering {
                    text-align: left;
                    margin-bottom: var(--space-4);
                }
                .pn-breakdown h3, .contact-ordering h3 {
                    margin: 0 0 var(--space-3) 0;
                    font-size: 1rem;
                }
                .breakdown-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                    gap: var(--space-2);
                }
                .breakdown-item {
                    padding: var(--space-2);
                    background: var(--bg-primary);
                    border-radius: var(--radius-sm);
                    text-align: center;
                }
                .breakdown-label {
                    display: block;
                    font-size: 0.65rem;
                    color: var(--text-muted);
                    text-transform: uppercase;
                }
                .breakdown-value { font-size: 1rem; }
                .ordering-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .ordering-table th, .ordering-table td {
                    padding: var(--space-2);
                    text-align: left;
                    border-bottom: 1px solid var(--border-subtle);
                }
                .ordering-table th {
                    font-size: 0.7rem;
                    color: var(--text-muted);
                }
                .mono { font-family: monospace; }

                /* Step Nav */
                .step-nav {
                    display: flex;
                    justify-content: space-between;
                    gap: var(--space-3);
                    margin-top: var(--space-4);
                    padding-top: var(--space-4);
                    border-top: 1px solid var(--border-subtle);
                }

                /* Tooltips */
                .tooltip-wrapper {
                    position: relative;
                    display: inline-block;
                }
                .tooltip-popup {
                    position: absolute;
                    z-index: 100;
                    padding: var(--space-2) var(--space-3);
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    font-size: 0.75rem;
                    white-space: nowrap;
                    max-width: 250px;
                    white-space: normal;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .tooltip-popup.top {
                    bottom: 100%;
                    left: 50%;
                    transform: translateX(-50%);
                    margin-bottom: var(--space-2);
                }

                /* Toast */
                .toast {
                    position: fixed;
                    bottom: var(--space-6);
                    left: 50%;
                    transform: translateX(-50%);
                    padding: var(--space-3) var(--space-6);
                    background: var(--success);
                    color: white;
                    border-radius: var(--radius-full);
                    font-weight: 600;
                    animation: fadeIn 0.3s;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateX(-50%) translateY(10px); }
                    to { opacity: 1; transform: translateX(-50%) translateY(0); }
                }

                /* Empty State */
                .empty-state {
                    text-align: center;
                    padding: var(--space-6);
                    color: var(--text-muted);
                }

                /* Buttons */
                .btn {
                    padding: var(--space-3) var(--space-4);
                    border-radius: var(--radius-md);
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: none;
                }
                .btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .btn-primary {
                    background: var(--accent-primary);
                    color: white;
                }
                .btn-primary:hover:not(:disabled) { filter: brightness(1.1); }
                .btn-secondary {
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                }
                .btn-ghost {
                    background: transparent;
                    color: var(--text-muted);
                }
                .btn-ghost:hover { color: var(--text-primary); }
                .btn-sm { padding: var(--space-1) var(--space-2); font-size: 0.875rem; }
                .select {
                    width: 100%;
                    padding: var(--space-3);
                    background: var(--bg-primary);
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    color: var(--text-primary);
                }
                .input {
                    padding: var(--space-3);
                    background: var(--bg-primary);
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    color: var(--text-primary);
                }
            `}</style>
        </div>
    );
}
