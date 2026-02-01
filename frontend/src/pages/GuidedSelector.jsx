import React, { useState, useEffect, useRef } from 'react';
import { chatAPI, partsAPI } from '../api/client';
import ChatInterface from '../components/ChatInterface';
import PDFSnippet from '../components/PDFSnippet';

/**
 * Guided Part Selector Page (GPS-002, GPS-007, GPS-008, UI-003)
 * 
 * Implements the Split-View UI with datasheet context grounding:
 * - Left: Chat Interface with D38999 knowledge
 * - Right: Context Panel (Source Snippets, Part Results, or Context Summary)
 */
function GuidedSelector() {
    const [sessionId, setSessionId] = useState(null);
    const [selectedContext, setSelectedContext] = useState(null); // Generalized selection (source or part)
    const [loading, setLoading] = useState(true);
    const [showQuickGuide, setShowQuickGuide] = useState(true);

    // UI State for split view (UI-004)
    const [isChatVisible, setIsChatVisible] = useState(true);
    const [chatWidth, setChatWidth] = useState(400); // Default width in px
    const [isResizing, setIsResizing] = useState(false);
    const sidebarRef = useRef(null);

    // Auto-create session on mount (GPS-001)
    useEffect(() => {
        const initSession = async () => {
            try {
                // In a real app, we might check for an existing active session
                const session = await chatAPI.createSession();
                setSessionId(session.id);
            } catch (error) {
                console.error("Failed to init chat session:", error);
            } finally {
                setLoading(false);
            }
        };
        initSession();
    }, []);

    // Resizing Logic
    const startResizing = (e) => {
        setIsResizing(true);
    };

    const stopResizing = () => {
        setIsResizing(false);
    };

    const resize = (e) => {
        if (isResizing) {
            // Clamp width between 300px and 50% of screen
            const newWidth = Math.max(300, Math.min(e.clientX, window.innerWidth * 0.5));
            setChatWidth(newWidth);
        }
    };

    useEffect(() => {
        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);
        return () => {
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [isResizing]);

    const handleSourceClick = (source) => {
        console.log("Viewing source:", source);
        setSelectedContext({ type: 'source', ...source });
        setShowQuickGuide(false);
    };

    const handlePartClick = async (partNumber) => {
        // ... (existing code) ...
        console.log("Decoding part:", partNumber);
        setShowQuickGuide(false);
        try {
            const data = await partsAPI.decode(partNumber);
            setSelectedContext({ type: 'part', data });
        } catch (error) {
            console.error("Failed to decode part:", error);
            setSelectedContext({ type: 'part-error', partNumber, error: error.message });
        }
    };

    if (loading) return <div className="p-4">Initializing Guided Selector...</div>;

    return (
        <div className="guided-selector-layout">
            <div
                className={`chat-pane ${!isChatVisible ? 'collapsed' : ''}`}
                style={{ width: isChatVisible ? chatWidth : 0 }}
                ref={sidebarRef}
            >
                <div className="chat-pane-content">
                    <ChatInterface
                        sessionId={sessionId}
                        onSourceClick={handleSourceClick}
                        onPartClick={handlePartClick}
                    />
                </div>
            </div>

            {/* Resize Handle */}
            {isChatVisible && (
                <div
                    className={`resize-handle ${isResizing ? 'active' : ''}`}
                    onMouseDown={startResizing}
                />
            )}

            <div className="context-pane">
                {/* Context Header */}
                <div className="context-header">
                    <div className="header-left" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <button
                            className="icon-btn"
                            onClick={() => setIsChatVisible(!isChatVisible)}
                            title={isChatVisible ? "Hide Chat" : "Show Chat"}
                        >
                            {isChatVisible ? '◀' : '▶'}
                        </button>
                        <div className="context-badge">
                            <span className="badge-icon">📦</span>
                            <span className="badge-text">D38999 Connectors</span>
                        </div>
                    </div>

                    <button
                        className="guide-toggle"
                        onClick={() => {
                            setShowQuickGuide(!showQuickGuide);
                            if (!showQuickGuide) setSelectedContext(null);
                        }}
                    >
                        {showQuickGuide ? '📘 Hide Guide' : '📘 Quick Guide'}
                    </button>
                </div>

                {/* ... (Rest of content) ... */}
                {selectedContext?.type === 'source' ? (

                    <div className="snippet-view">
                        <div className="snippet-header">
                            <h4>Source Document</h4>
                            <button onClick={() => setSelectedContext(null)}>✕</button>
                        </div>
                        <div className="snippet-content">
                            <PDFSnippet
                                datasheetId={selectedContext.datasheet_id}
                                pageNumber={selectedContext.page}
                                bbox={selectedContext.bbox}
                                scale={1.5}
                            />
                        </div>
                    </div>
                ) : selectedContext?.type === 'part' ? (
                    <div className="part-view">
                        <div className="part-header">
                            <h4>Selected Part</h4>
                            <button onClick={() => setSelectedContext(null)}>✕</button>
                        </div>
                        <div className="part-card">
                            <input
                                className="part-number-input"
                                key={selectedContext.data.part_number}
                                defaultValue={selectedContext.data.part_number}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') e.target.blur();
                                }}
                                onBlur={(e) => {
                                    const val = e.target.value.trim();
                                    if (val && val !== selectedContext.data.part_number) {
                                        handlePartClick(val);
                                    }
                                }}
                                title="Click to edit part number"
                            />
                            {selectedContext.data.is_valid ? (
                                <div className="part-specs">
                                    <h5>Specifications</h5>
                                    <table className="specs-table">
                                        <tbody>
                                            {Object.entries(selectedContext.data.field_names).map(([code, desc]) => (
                                                <tr key={code}>
                                                    <td className="spec-label">{code}</td>
                                                    <td className="spec-val">{desc}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="part-error">
                                    ⚠️ Invalid Part Number Format
                                </div>
                            )}
                        </div>
                    </div>
                ) : showQuickGuide ? (
                    <div className="quick-guide">
                        <h3>🎯 D38999 Quick Reference</h3>

                        <div className="guide-section">
                            <h4>Part Number Format</h4>
                            <code className="part-format">D38999/XX-YY-ZZNP</code>
                            <ul>
                                <li><strong>XX</strong>: Series (20=Bayonet, 24=Threaded, 26=Breech)</li>
                                <li><strong>Y</strong>: Class (W=Olive Drab, F=Nickel, K=Stainless)</li>
                                <li><strong>Y</strong>: Shell Size (A-J for sizes 9-25)</li>
                                <li><strong>ZZ</strong>: Insert Arrangement (contact pattern)</li>
                                <li><strong>N</strong>: Contact Style (P=Pins, S=Sockets)</li>
                            </ul>
                        </div>

                        <div className="guide-section">
                            <h4>Contact Sizes</h4>
                            <table className="reference-table">
                                <thead>
                                    <tr><th>Size</th><th>AWG Range</th><th>Use</th></tr>
                                </thead>
                                <tbody>
                                    <tr><td>22D</td><td>22-26 AWG</td><td>Signal</td></tr>
                                    <tr><td>20</td><td>20 AWG</td><td>Light Power</td></tr>
                                    <tr><td>16</td><td>16-18 AWG</td><td>Power</td></tr>
                                    <tr><td>12</td><td>12 AWG</td><td>High Power</td></tr>
                                </tbody>
                            </table>
                        </div>

                        <div className="guide-section">
                            <h4>Shell Sizes</h4>
                            <table className="reference-table">
                                <thead>
                                    <tr><th>Code</th><th>Size</th><th>Max Contacts</th></tr>
                                </thead>
                                <tbody>
                                    <tr><td>A</td><td>9</td><td>5</td></tr>
                                    <tr><td>B</td><td>11</td><td>9</td></tr>
                                    <tr><td>C</td><td>13</td><td>14</td></tr>
                                    <tr><td>D</td><td>15</td><td>19</td></tr>
                                    <tr><td>E</td><td>17</td><td>26</td></tr>
                                    <tr><td>F</td><td>19</td><td>39</td></tr>
                                    <tr><td>G</td><td>21</td><td>55</td></tr>
                                </tbody>
                            </table>
                        </div>

                        <div className="guide-section tips">
                            <h4>💡 Tips</h4>
                            <ul>
                                <li><strong>"Jam nut"</strong> = Through-panel receptacle mount</li>
                                <li>Specify AWG + quantity for best recommendations</li>
                                <li>Mix power + signal? Consider multi-insert options</li>
                            </ul>
                        </div>
                    </div>
                ) : (
                    <div className="empty-context">
                        <div className="placeholder-icon">📑</div>
                        <h3>Context View</h3>
                        <p>Ask questions to see relevant part details and PDF source snippets here.</p>
                        <p className="hint">Try asking: "I need a connector with 20 signal wires and 2 power wires"</p>
                    </div>
                )}
            </div>

            <style>{`
                .guided-selector-layout {
                    display: flex;
                    height: 100vh;
                    overflow: hidden;
                    background: var(--bg-primary);
                }
                .chat-pane {
                    flex: none; /* Turn off flex grow/shrink */
                    display: flex;
                    flex-direction: column;
                    border-right: 1px solid var(--border-subtle);
                    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    overflow: hidden;
                }
                .chat-pane.collapsed {
                    width: 0 !important;
                    border-right: none;
                }
                .chat-pane-content {
                    width: 400px; /* Min width needed content */
                    min-width: 100%;
                    height: 100%;
                }
                
                /* Resize Handle */
                .resize-handle {
                    width: 4px;
                    cursor: col-resize;
                    background: transparent;
                    transition: background 0.2s;
                    position: relative;
                    z-index: 10;
                    flex: none;
                }
                .resize-handle:hover, .resize-handle.active {
                    background: var(--accent-primary);
                }
                /* Expand handle hit area */
                .resize-handle::after {
                    content: '';
                    position: absolute;
                    left: -4px;
                    right: -4px;
                    top: 0;
                    bottom: 0;
                }

                .context-pane {
                    flex: 1;
                    /* flex: 1.5; Removed fixed ratio */
                    background: var(--bg-secondary);
                    position: relative;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                
                /* Context Header - GPS-008 */
                .context-header {
                    padding: 0.75rem 1rem;
                    background: var(--bg-tertiary);
                    border-bottom: 1px solid var(--border-subtle);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .icon-btn {
                    background: transparent;
                    border: none;
                    color: var(--text-secondary);
                    cursor: pointer;
                    padding: 0.25rem 0.5rem;
                    border-radius: var(--radius-sm);
                    font-size: 1rem;
                }
                .icon-btn:hover {
                    background: rgba(0,0,0,0.05);
                    color: var(--text-primary);
                }
                .context-badge {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.25rem 0.75rem;
                    background: rgba(99, 102, 241, 0.1);
                    border: 1px solid var(--accent-primary);
                    border-radius: var(--radius-full);
                }
                .badge-icon {
                    font-size: 1rem;
                }
                .badge-text {
                    font-weight: 600;
                    color: var(--accent-primary);
                    font-size: 0.875rem;
                }
                .guide-toggle {
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-subtle);
                    padding: 0.375rem 0.75rem;
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    font-size: 0.75rem;
                    color: var(--text-secondary);
                    transition: all var(--transition-fast);
                }
                .guide-toggle:hover {
                    background: var(--bg-elevated);
                    border-color: var(--accent-primary);
                }
                
                /* Quick Guide */
                .quick-guide {
                    flex: 1;
                    overflow-y: auto;
                    padding: 1.5rem;
                }
                .quick-guide h3 {
                    margin-bottom: 1.25rem;
                    color: var(--text-primary);
                }
                .guide-section {
                    margin-bottom: 1.5rem;
                    background: var(--bg-tertiary);
                    border-radius: var(--radius-md);
                    padding: 1rem;
                }
                .guide-section h4 {
                    font-size: 0.875rem;
                    color: var(--accent-primary);
                    margin-bottom: 0.75rem;
                }
                .part-format {
                    display: block;
                    font-size: 1.125rem;
                    font-family: var(--font-mono);
                    color: var(--text-primary);
                    background: var(--bg-primary);
                    padding: 0.75rem 1rem;
                    border-radius: var(--radius-sm);
                    margin-bottom: 0.75rem;
                    text-align: center;
                }
                .guide-section ul {
                    padding-left: 1.25rem;
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                }
                .guide-section li {
                    margin-bottom: 0.25rem;
                }
                .reference-table {
                    width: 100%;
                    font-size: 0.75rem;
                    border-collapse: collapse;
                }
                .reference-table th,
                .reference-table td {
                    padding: 0.375rem 0.5rem;
                    text-align: left;
                    border-bottom: 1px solid var(--border-subtle);
                }
                .reference-table th {
                    color: var(--text-muted);
                    font-weight: 500;
                }
                .reference-table td {
                    font-family: var(--font-mono);
                    color: var(--text-secondary);
                }
                .guide-section.tips {
                    background: rgba(34, 197, 94, 0.05);
                    border: 1px solid rgba(34, 197, 94, 0.2);
                }
                .guide-section.tips h4 {
                    color: var(--success);
                }
                
                .empty-context {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: var(--text-secondary);
                    text-align: center;
                    padding: 2rem;
                }
                .placeholder-icon {
                    font-size: 3rem;
                    margin-bottom: 1rem;
                    opacity: 0.5;
                }
                .hint {
                    margin-top: 1rem;
                    font-size: 0.875rem;
                    color: var(--text-muted);
                    font-style: italic;
                }
                .snippet-view {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                }
                .snippet-header {
                    padding: 0.75rem 1rem;
                    background: var(--bg-primary);
                    border-bottom: 1px solid var(--border-subtle);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .snippet-content {
                    flex: 1;
                    overflow: auto;
                    padding: 1rem;
                    display: flex;
                    justify-content: center;
                }
                /* Part View */
                .part-view {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    overflow: hidden;
                }
                .part-header {
                    padding: 0.75rem 1rem;
                    background: var(--bg-primary);
                    border-bottom: 1px solid var(--border-subtle);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .part-header h4 {
                    font-size: 0.875rem;
                    font-weight: 600;
                    margin: 0;
                }
                .part-card {
                    padding: 1.5rem;
                    overflow-y: auto;
                }
                .part-number {
                    font-family: var(--font-mono);
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: var(--accent-primary);
                    margin-bottom: 1.5rem;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid var(--border-subtle);
                }
                .part-number-input {
                    font-family: var(--font-mono);
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: var(--accent-primary);
                    margin-bottom: 1.5rem;
                    padding: 0.5rem;
                    width: 100%;
                    background: transparent;
                    border: 1px solid transparent;
                    border-bottom: 1px solid var(--border-subtle);
                    border-radius: var(--radius-sm);
                    transition: all 0.2s;
                }
                .part-number-input:hover {
                    background: var(--bg-tertiary);
                    border-color: var(--border-subtle);
                }
                .part-number-input:focus {
                    background: var(--bg-tertiary);
                    border-color: var(--accent-primary);
                    outline: none;
                }
                .part-specs h5 {
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    margin-bottom: 0.75rem;
                }
                .specs-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .specs-table td {
                    padding: 0.5rem 0;
                    border-bottom: 1px solid var(--border-subtle);
                    font-size: 0.875rem;
                }
                .spec-label {
                    color: var(--text-secondary);
                    width: 40px;
                    font-family: var(--font-mono);
                }
                .spec-val {
                    color: var(--text-primary);
                    font-weight: 500;
                }
                .part-error {
                    color: var(--error);
                    padding: 1rem;
                    background: rgba(239, 68, 68, 0.1);
                    border-radius: var(--radius-md);
                }
            `}</style>
        </div>
    );
}

export default GuidedSelector;
