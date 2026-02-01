import { useState, useEffect } from 'react';
import { settingsAPI } from '../api/client';

/**
 * Settings Page
 * 
 * Allows users to configure API keys and select models for Google Gemini or OpenRouter
 */
function Settings() {
    const [settings, setSettings] = useState({
        active_provider: 'google',
        selected_model: null,
        gemini_api_key_configured: false,
        openrouter_api_key_configured: false,
        gemini_api_key_masked: null,
        openrouter_api_key_masked: null,
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState(null);

    // Models state
    const [loadingModels, setLoadingModels] = useState(false);
    const [models, setModels] = useState([]);
    const [modelsMessage, setModelsMessage] = useState('');
    const [showModels, setShowModels] = useState(false);
    const [selectedModelId, setSelectedModelId] = useState('');

    // Form state
    const [provider, setProvider] = useState('google');
    const [apiKey, setApiKey] = useState('');
    const [showKey, setShowKey] = useState(false);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const data = await settingsAPI.get();
            setSettings(data);
            setProvider(data.active_provider || 'google');
            setSelectedModelId(data.selected_model || '');
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setTestResult(null);

        try {
            const update = {
                active_provider: provider,
            };

            // Only include API key if user entered a new one
            if (apiKey) {
                if (provider === 'google') {
                    update.gemini_api_key = apiKey;
                } else {
                    update.openrouter_api_key = apiKey;
                }
            }

            // Include selected model if set
            if (selectedModelId) {
                update.selected_model = selectedModelId;
            }

            const data = await settingsAPI.save(update);
            setSettings(data);
            setApiKey(''); // Clear the input
            setTestResult({ valid: true, message: 'Settings saved successfully!' });
        } catch (error) {
            setTestResult({ valid: false, message: `Failed to save: ${error.message}` });
        } finally {
            setSaving(false);
        }
    };

    const handleTest = async () => {
        if (!apiKey && !getCurrentKeyConfigured()) {
            setTestResult({ valid: false, message: 'Please enter an API key first' });
            return;
        }

        setTesting(true);
        setTestResult(null);

        try {
            const result = await settingsAPI.testKey(provider, apiKey || '');
            setTestResult(result);
        } catch (error) {
            setTestResult({ valid: false, message: `Test failed: ${error.message}` });
        } finally {
            setTesting(false);
        }
    };

    const handleListModels = async () => {
        setLoadingModels(true);
        setModels([]);
        setModelsMessage('');
        setShowModels(true);

        try {
            const result = await settingsAPI.listModels(provider, apiKey || null);
            if (result.success) {
                setModels(result.models);
                setModelsMessage(result.message);
            } else {
                setModelsMessage(result.message);
            }
        } catch (error) {
            setModelsMessage(`Error: ${error.message}`);
        } finally {
            setLoadingModels(false);
        }
    };

    const handleSelectModel = async (modelId) => {
        setSelectedModelId(modelId);
        setSaving(true);

        try {
            const update = {
                active_provider: provider,
                selected_model: modelId,
            };
            const data = await settingsAPI.save(update);
            setSettings(data);
            setTestResult({ valid: true, message: `Model selected: ${modelId}` });
        } catch (error) {
            setTestResult({ valid: false, message: `Failed to select model: ${error.message}` });
        } finally {
            setSaving(false);
        }
    };

    const handleClear = async () => {
        setSaving(true);
        setTestResult(null);

        try {
            const update = {
                active_provider: provider,
                clear_gemini_key: provider === 'google',
                clear_openrouter_key: provider === 'openrouter',
            };

            const data = await settingsAPI.save(update);
            setSettings(data);
            setApiKey('');
            setTestResult({ valid: true, message: 'API key cleared' });
        } catch (error) {
            setTestResult({ valid: false, message: `Failed to clear: ${error.message}` });
        } finally {
            setSaving(false);
        }
    };

    const getCurrentKeyConfigured = () => {
        return provider === 'google'
            ? settings.gemini_api_key_configured
            : settings.openrouter_api_key_configured;
    };

    const getCurrentKeyMasked = () => {
        return provider === 'google'
            ? settings.gemini_api_key_masked
            : settings.openrouter_api_key_masked;
    };

    if (loading) {
        return (
            <div className="settings-page">
                <div className="skeleton" style={{ height: '200px' }}></div>
            </div>
        );
    }

    return (
        <div className="settings-page">
            <div className="page-header">
                <h1>⚙️ Settings</h1>
                <p className="text-muted">Configure your API keys and select AI models</p>
            </div>

            <div className="settings-card">
                <h2>LLM Provider</h2>
                <p className="text-muted">Choose which AI provider to use for chat and datasheet analysis.</p>

                <div className="provider-toggle">
                    <button
                        className={`provider-btn ${provider === 'google' ? 'active' : ''}`}
                        onClick={() => { setProvider('google'); setShowModels(false); setModels([]); }}
                    >
                        <span className="provider-icon">🔷</span>
                        <span className="provider-name">Google Gemini</span>
                        {settings.gemini_api_key_configured && (
                            <span className="configured-badge">✓ Configured</span>
                        )}
                    </button>
                    <button
                        className={`provider-btn ${provider === 'openrouter' ? 'active' : ''}`}
                        onClick={() => { setProvider('openrouter'); setShowModels(false); setModels([]); }}
                    >
                        <span className="provider-icon">🌐</span>
                        <span className="provider-name">OpenRouter</span>
                        {settings.openrouter_api_key_configured && (
                            <span className="configured-badge">✓ Configured</span>
                        )}
                    </button>
                </div>
            </div>

            <div className="settings-card">
                <h2>
                    {provider === 'google' ? 'Google Gemini' : 'OpenRouter'} API Key
                </h2>
                <p className="text-muted">
                    {provider === 'google'
                        ? 'Get your API key from Google AI Studio (aistudio.google.com)'
                        : 'Get your API key from OpenRouter (openrouter.ai/keys)'}
                </p>

                <div className="key-status">
                    {getCurrentKeyConfigured() ? (
                        <div className="status configured">
                            <span className="status-icon">✓</span>
                            <span>Configured: {getCurrentKeyMasked()}</span>
                        </div>
                    ) : (
                        <div className="status not-configured">
                            <span className="status-icon">○</span>
                            <span>Not configured</span>
                        </div>
                    )}
                </div>

                {/* Show selected model */}
                {settings.selected_model && (
                    <div className="selected-model-display">
                        <span className="label">Active Model:</span>
                        <span className="model-badge">{settings.selected_model}</span>
                    </div>
                )}

                <div className="api-key-input-group">
                    <div className="input-wrapper">
                        <input
                            type={showKey ? 'text' : 'password'}
                            className="api-key-input"
                            placeholder={getCurrentKeyConfigured() ? 'Enter new key to replace...' : 'Enter your API key...'}
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                        />
                        <button
                            className="toggle-visibility"
                            onClick={() => setShowKey(!showKey)}
                            type="button"
                        >
                            {showKey ? '🙈' : '👁️'}
                        </button>
                    </div>
                </div>

                <div className="button-group">
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={saving || (!apiKey && provider === settings.active_provider && !selectedModelId)}
                    >
                        {saving ? 'Saving...' : '💾 Save'}
                    </button>
                    <button
                        className="btn btn-secondary"
                        onClick={handleTest}
                        disabled={testing || (!apiKey && !getCurrentKeyConfigured())}
                    >
                        {testing ? 'Testing...' : '🧪 Test Key'}
                    </button>
                    <button
                        className="btn btn-accent"
                        onClick={handleListModels}
                        disabled={loadingModels || (!apiKey && !getCurrentKeyConfigured())}
                    >
                        {loadingModels ? 'Loading...' : '📋 Select Model'}
                    </button>
                    {getCurrentKeyConfigured() && (
                        <button
                            className="btn btn-danger"
                            onClick={handleClear}
                            disabled={saving}
                        >
                            🗑️ Clear Key
                        </button>
                    )}
                </div>

                {testResult && (
                    <div className={`test-result ${testResult.valid ? 'success' : 'error'}`}>
                        <span className="result-icon">{testResult.valid ? '✅' : '❌'}</span>
                        <span>{testResult.message}</span>
                    </div>
                )}
            </div>

            {/* Models List Section */}
            {showModels && (
                <div className="settings-card models-card">
                    <div className="models-header">
                        <h2>📋 Select a Model</h2>
                        <button className="btn-close" onClick={() => setShowModels(false)}>✕</button>
                    </div>
                    <p className="text-muted">{modelsMessage}</p>
                    <p className="text-muted text-sm">Click on a model to select it for use. Free models are highlighted in green.</p>

                    {loadingModels ? (
                        <div className="models-loading">
                            <div className="spinner"></div>
                            <span>Loading models...</span>
                        </div>
                    ) : models.length > 0 ? (
                        <div className="models-list">
                            <table className="models-table">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Context</th>
                                        <th>Input</th>
                                        <th>Output</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {models.map((model, idx) => (
                                        <tr
                                            key={idx}
                                            className={`${model.is_free ? 'free-model' : ''} ${selectedModelId === model.id ? 'selected-model' : ''}`}
                                        >
                                            <td>
                                                <div className="model-name">
                                                    {model.is_free && <span className="free-badge">FREE</span>}
                                                    <span>{model.name}</span>
                                                </div>
                                                <div className="model-id">{model.id}</div>
                                            </td>
                                            <td className="context-col">
                                                {model.context_length ? `${(model.context_length / 1000).toFixed(0)}K` : '-'}
                                            </td>
                                            <td className="cost-col">{model.input_cost || '-'}</td>
                                            <td className="cost-col">{model.output_cost || '-'}</td>
                                            <td>
                                                <button
                                                    className={`btn btn-sm ${selectedModelId === model.id ? 'btn-selected' : 'btn-select'}`}
                                                    onClick={() => handleSelectModel(model.id)}
                                                    disabled={saving}
                                                >
                                                    {selectedModelId === model.id ? '✓ Selected' : 'Select'}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : modelsMessage && !loadingModels ? (
                        <div className="no-models">No models found</div>
                    ) : null}
                </div>
            )}

            <style>{`
                .settings-page {
                    padding: var(--space-6);
                    max-width: 1100px;
                    margin: 0 auto;
                }

                .page-header {
                    margin-bottom: var(--space-6);
                }

                .page-header h1 {
                    margin-bottom: var(--space-2);
                }

                .settings-card {
                    background: var(--bg-secondary);
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-lg);
                    padding: var(--space-5);
                    margin-bottom: var(--space-5);
                }

                .settings-card h2 {
                    font-size: 1.125rem;
                    margin-bottom: var(--space-2);
                }

                .provider-toggle {
                    display: flex;
                    gap: var(--space-3);
                    margin-top: var(--space-4);
                }

                .provider-btn {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: var(--space-2);
                    padding: var(--space-4);
                    background: var(--bg-tertiary);
                    border: 2px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    cursor: pointer;
                    transition: all var(--transition-fast);
                }

                .provider-btn:hover {
                    border-color: var(--border-default);
                }

                .provider-btn.active {
                    border-color: var(--accent-primary);
                    background: rgba(99, 102, 241, 0.1);
                }

                .provider-icon {
                    font-size: 2rem;
                }

                .provider-name {
                    font-weight: 600;
                    color: var(--text-primary);
                }

                .configured-badge {
                    font-size: 0.75rem;
                    color: var(--success);
                    background: rgba(34, 197, 94, 0.1);
                    padding: 2px 8px;
                    border-radius: var(--radius-full);
                }

                .key-status {
                    margin: var(--space-4) 0;
                }

                .status {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    padding: var(--space-3);
                    border-radius: var(--radius-md);
                }

                .status.configured {
                    background: rgba(34, 197, 94, 0.1);
                    color: var(--success);
                }

                .status.not-configured {
                    background: rgba(251, 191, 36, 0.1);
                    color: var(--warning);
                }

                .selected-model-display {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    padding: var(--space-3);
                    background: rgba(99, 102, 241, 0.1);
                    border-radius: var(--radius-md);
                    margin-bottom: var(--space-4);
                }

                .selected-model-display .label {
                    color: var(--text-muted);
                }

                .model-badge {
                    font-family: var(--font-mono);
                    font-size: 0.875rem;
                    color: var(--accent-primary);
                    font-weight: 500;
                }

                .api-key-input-group {
                    margin-bottom: var(--space-4);
                }

                .input-wrapper {
                    position: relative;
                    display: flex;
                }

                .api-key-input {
                    flex: 1;
                    padding: var(--space-3) var(--space-4);
                    padding-right: 50px;
                    background: var(--bg-tertiary);
                    border: 1px solid var(--border-subtle);
                    border-radius: var(--radius-md);
                    color: var(--text-primary);
                    font-family: var(--font-mono);
                    font-size: 0.875rem;
                }

                .api-key-input:focus {
                    outline: none;
                    border-color: var(--accent-primary);
                }

                .toggle-visibility {
                    position: absolute;
                    right: var(--space-2);
                    top: 50%;
                    transform: translateY(-50%);
                    background: none;
                    border: none;
                    cursor: pointer;
                    font-size: 1rem;
                    padding: var(--space-2);
                }

                .button-group {
                    display: flex;
                    gap: var(--space-3);
                    flex-wrap: wrap;
                }

                .btn {
                    padding: var(--space-3) var(--space-4);
                    border-radius: var(--radius-md);
                    font-weight: 500;
                    cursor: pointer;
                    transition: all var(--transition-fast);
                    border: none;
                }

                .btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .btn-primary {
                    background: var(--accent-gradient);
                    color: white;
                }

                .btn-primary:hover:not(:disabled) {
                    filter: brightness(1.1);
                }

                .btn-secondary {
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                    border: 1px solid var(--border-subtle);
                }

                .btn-secondary:hover:not(:disabled) {
                    background: var(--bg-elevated);
                }

                .btn-accent {
                    background: rgba(99, 102, 241, 0.2);
                    color: var(--accent-primary);
                    border: 1px solid var(--accent-primary);
                }

                .btn-accent:hover:not(:disabled) {
                    background: rgba(99, 102, 241, 0.3);
                }

                .btn-danger {
                    background: rgba(239, 68, 68, 0.1);
                    color: var(--error);
                    border: 1px solid var(--error);
                }

                .btn-danger:hover:not(:disabled) {
                    background: rgba(239, 68, 68, 0.2);
                }

                .btn-sm {
                    padding: var(--space-1) var(--space-3);
                    font-size: 0.75rem;
                }

                .btn-select {
                    background: var(--bg-tertiary);
                    color: var(--text-primary);
                    border: 1px solid var(--border-subtle);
                }

                .btn-select:hover:not(:disabled) {
                    background: var(--accent-primary);
                    color: white;
                    border-color: var(--accent-primary);
                }

                .btn-selected {
                    background: var(--success);
                    color: white;
                    border: 1px solid var(--success);
                }

                .test-result {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    margin-top: var(--space-4);
                    padding: var(--space-3);
                    border-radius: var(--radius-md);
                }

                .test-result.success {
                    background: rgba(34, 197, 94, 0.1);
                    color: var(--success);
                }

                .test-result.error {
                    background: rgba(239, 68, 68, 0.1);
                    color: var(--error);
                }

                .text-muted {
                    color: var(--text-muted);
                }

                .text-sm {
                    font-size: 0.75rem;
                }

                /* Models Section */
                .models-card {
                    max-height: 70vh;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }

                .models-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .btn-close {
                    background: none;
                    border: none;
                    font-size: 1.25rem;
                    cursor: pointer;
                    color: var(--text-muted);
                    padding: var(--space-2);
                }

                .btn-close:hover {
                    color: var(--text-primary);
                }

                .models-loading {
                    display: flex;
                    align-items: center;
                    gap: var(--space-3);
                    padding: var(--space-4);
                    color: var(--text-muted);
                }

                .spinner {
                    width: 20px;
                    height: 20px;
                    border: 2px solid var(--border-subtle);
                    border-top-color: var(--accent-primary);
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                .models-list {
                    margin-top: var(--space-4);
                    flex: 1;
                    overflow-y: auto;
                }

                .models-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.875rem;
                }

                .models-table th {
                    text-align: left;
                    padding: var(--space-2) var(--space-3);
                    background: var(--bg-tertiary);
                    color: var(--text-muted);
                    font-weight: 500;
                    position: sticky;
                    top: 0;
                }

                .models-table td {
                    padding: var(--space-2) var(--space-3);
                    border-bottom: 1px solid var(--border-subtle);
                    vertical-align: top;
                }

                .models-table tr:hover {
                    background: var(--bg-tertiary);
                }

                .models-table tr.free-model {
                    background: rgba(34, 197, 94, 0.05);
                }

                .models-table tr.selected-model {
                    background: rgba(99, 102, 241, 0.1);
                    border-left: 3px solid var(--accent-primary);
                }

                .model-name {
                    display: flex;
                    align-items: center;
                    gap: var(--space-2);
                    font-weight: 500;
                    color: var(--text-primary);
                }

                .model-id {
                    font-size: 0.75rem;
                    color: var(--text-muted);
                    font-family: var(--font-mono);
                    margin-top: 2px;
                }

                .free-badge {
                    font-size: 0.625rem;
                    font-weight: 700;
                    background: var(--success);
                    color: white;
                    padding: 2px 6px;
                    border-radius: var(--radius-sm);
                }

                .context-col, .cost-col {
                    white-space: nowrap;
                    font-family: var(--font-mono);
                    font-size: 0.75rem;
                }

                .no-models {
                    padding: var(--space-4);
                    text-align: center;
                    color: var(--text-muted);
                }
            `}</style>
        </div>
    );
}

export default Settings;
