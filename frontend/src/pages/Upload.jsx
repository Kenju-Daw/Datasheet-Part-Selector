import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { datasheetAPI, connectProgressStream } from '../api/client';

/**
 * Upload Page
 * 
 * Implements:
 * - PDF-001: PDF upload
 * - PDF-009: Processing status
 * - PDF-012: Detailed progress bar
 * - PDF-014: Real-time updates
 * - PDF-015: Estimated remaining time
 */
function Upload() {
    const navigate = useNavigate();
    const fileInputRef = useRef(null);

    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(null);
    const [error, setError] = useState(null);

    // Metadata form
    const [name, setName] = useState('');
    const [manufacturer, setManufacturer] = useState('');

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const droppedFile = e.dataTransfer?.files?.[0];
        if (droppedFile?.type === 'application/pdf') {
            setFile(droppedFile);
            setName(droppedFile.name.replace('.pdf', ''));
            setError(null);
        } else {
            setError('Please upload a PDF file');
        }
    }, []);

    const handleFileSelect = useCallback((e) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            setName(selectedFile.name.replace('.pdf', ''));
            setError(null);
        }
    }, []);

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);
        setProgress({ stage: 'upload', percent: 0, message: 'Uploading file...' });

        try {
            // Upload the file
            const datasheet = await datasheetAPI.upload(file, { name, manufacturer });

            setProgress({ stage: 'upload', percent: 5, message: 'Upload complete, starting processing...' });

            // Connect to progress stream
            const cleanup = connectProgressStream(
                datasheet.id,
                // On progress
                (data) => setProgress(data),
                // On complete
                (data) => {
                    setProgress({ ...data, percent: 100, message: 'Complete!' });
                    setTimeout(() => navigate(`/configure/${datasheet.id}`), 1500);
                },
                // On error
                (err) => {
                    setError('Processing failed. Please try again.');
                    setUploading(false);
                }
            );

            // Cleanup on unmount would go here

        } catch (err) {
            setError(err.message || 'Upload failed');
            setUploading(false);
            setProgress(null);
        }
    };

    const formatTime = (seconds) => {
        if (!seconds || seconds < 0) return '';
        if (seconds < 60) return `~${seconds}s remaining`;
        return `~${Math.ceil(seconds / 60)} min remaining`;
    };

    const getStageLabel = (stage) => {
        const stages = {
            upload: 'Uploading',
            docling_init: 'Initializing Parser',
            docling_pages: 'Parsing Pages',
            docling_tables: 'Extracting Tables',
            llm_analyze: 'Analyzing Structure',
            llm_extract: 'Extracting Fields',
            llm_schema: 'Building Schema',
            saving: 'Saving Data',
            complete: 'Complete'
        };
        return stages[stage] || stage;
    };

    return (
        <div className="upload-page">
            <header className="page-header">
                <h1>Upload Datasheet</h1>
                <p className="text-muted">Upload a PDF datasheet to create an interactive part configurator</p>
            </header>

            {!uploading ? (
                <>
                    {/* Drop Zone */}
                    <div
                        className={`drop-zone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf"
                            onChange={handleFileSelect}
                            style={{ display: 'none' }}
                        />

                        {file ? (
                            <div className="file-preview">
                                <div className="file-icon">📄</div>
                                <div className="file-info">
                                    <div className="file-name">{file.name}</div>
                                    <div className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                                </div>
                                <button className="btn btn-ghost" onClick={(e) => { e.stopPropagation(); setFile(null); }}>
                                    ✕
                                </button>
                            </div>
                        ) : (
                            <>
                                <div className="drop-zone-icon">📤</div>
                                <div className="drop-zone-text">Drag and drop your PDF here</div>
                                <div className="drop-zone-hint">or click to browse (max 50MB)</div>
                            </>
                        )}
                    </div>

                    {error && (
                        <div className="error-message">{error}</div>
                    )}

                    {/* Metadata Form */}
                    {file && (
                        <div className="card mt-6">
                            <h3 className="card-title mb-4">Datasheet Details</h3>

                            <div className="form-grid">
                                <div className="input-group">
                                    <label className="input-label">Name</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        placeholder="e.g., D38999 Series III"
                                    />
                                </div>

                                <div className="input-group">
                                    <label className="input-label">Manufacturer</label>
                                    <input
                                        type="text"
                                        className="input"
                                        value={manufacturer}
                                        onChange={(e) => setManufacturer(e.target.value)}
                                        placeholder="e.g., Amphenol"
                                    />
                                </div>
                            </div>

                            <button
                                className="btn btn-primary mt-6"
                                onClick={handleUpload}
                                disabled={!file}
                            >
                                Start Processing
                            </button>
                        </div>
                    )}
                </>
            ) : (
                /* Progress View */
                <div className="card processing-card">
                    <div className="processing-header">
                        <div className="file-icon large">📄</div>
                        <div>
                            <h3>{name}</h3>
                            <p className="text-muted">{file?.name}</p>
                        </div>
                    </div>

                    {/* Detailed Progress Bar (PDF-012) */}
                    <div className="progress-container mt-6">
                        <div className="progress-header">
                            <span className="progress-stage">{getStageLabel(progress?.stage)}</span>
                            <span className="progress-percent">{Math.round(progress?.percent || 0)}%</span>
                        </div>

                        <div className="progress-bar">
                            <div
                                className="progress-fill"
                                style={{ width: `${progress?.percent || 0}%` }}
                            ></div>
                        </div>

                        <div className="progress-message">{progress?.message}</div>

                        {/* Detailed Info (PDF-012) */}
                        {(progress?.pages_total || progress?.tables_found) && (
                            <div className="progress-details">
                                {progress?.pages_processed !== undefined && (
                                    <div className="progress-detail">
                                        📄 {progress.pages_processed}/{progress.pages_total || '?'} pages
                                    </div>
                                )}
                                {progress?.tables_found !== undefined && (
                                    <div className="progress-detail">
                                        📊 {progress.tables_found} tables found
                                    </div>
                                )}
                                {progress?.estimated_seconds_remaining && (
                                    <div className="progress-detail">
                                        ⏱️ {formatTime(progress.estimated_seconds_remaining)}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Stage Indicators (PDF-013) */}
                    <div className="stage-list mt-6">
                        {['docling_init', 'docling_pages', 'docling_tables', 'llm_analyze', 'llm_extract', 'llm_schema', 'complete'].map((stage, i) => {
                            const current = ['docling_init', 'docling_pages', 'docling_tables', 'llm_analyze', 'llm_extract', 'llm_schema', 'saving', 'complete'].indexOf(progress?.stage || '');
                            const stageIndex = i;
                            const status = stageIndex < current ? 'done' : stageIndex === current ? 'active' : 'pending';

                            return (
                                <div key={stage} className={`stage-item ${status}`}>
                                    <div className="stage-dot"></div>
                                    <span>{getStageLabel(stage)}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <style>{`
        .upload-page {
          max-width: 700px;
        }

        .page-header {
          margin-bottom: var(--space-6);
        }

        .drop-zone.has-file {
          padding: var(--space-5);
        }

        .file-preview {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          width: 100%;
        }

        .file-icon {
          font-size: 2.5rem;
        }

        .file-icon.large {
          font-size: 3rem;
        }

        .file-info {
          flex: 1;
          text-align: left;
        }

        .file-name {
          font-weight: 600;
          color: var(--text-primary);
        }

        .file-size {
          font-size: 0.875rem;
          color: var(--text-muted);
        }

        .error-message {
          margin-top: var(--space-4);
          padding: var(--space-3) var(--space-4);
          background: rgba(248, 113, 113, 0.1);
          border: 1px solid var(--error);
          border-radius: var(--radius-sm);
          color: var(--error);
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: var(--space-4);
        }

        .processing-card {
          text-align: center;
        }

        .processing-header {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          justify-content: center;
        }

        .progress-message {
          margin-top: var(--space-2);
          font-size: 0.875rem;
          color: var(--text-secondary);
        }

        .stage-list {
          display: flex;
          flex-wrap: wrap;
          justify-content: center;
          gap: var(--space-4);
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-subtle);
        }

        .stage-item {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .stage-item.active {
          color: var(--accent-primary);
        }

        .stage-item.done {
          color: var(--success);
        }

        .stage-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--text-muted);
        }

        .stage-item.active .stage-dot {
          background: var(--accent-primary);
          animation: pulse 1s infinite;
        }

        .stage-item.done .stage-dot {
          background: var(--success);
        }
      `}</style>
        </div>
    );
}

export default Upload;
