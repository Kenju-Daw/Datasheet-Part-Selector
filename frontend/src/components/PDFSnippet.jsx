import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    'pdfjs-dist/build/pdf.worker.min.mjs',
    import.meta.url,
).toString();

const PDFSnippet = ({ datasheetId, pageNumber, bbox, scale = 1.0 }) => {
    const [numPages, setNumPages] = useState(null);
    const [pageWidth, setPageWidth] = useState(0);
    const containerRef = useRef(null);

    const onDocumentLoadSuccess = ({ numPages }) => {
        setNumPages(numPages);
    };

    const onPageLoadSuccess = (page) => {
        setPageWidth(page.width);
    };

    // Construct PDF URL (using existing backend endpoint)
    const pdfUrl = `/api/datasheets/${datasheetId}/download`;

    // Convert BBox to style (assuming Docling coordinate system: usually bottom-left origin in points?)
    // Docling v2 usually returns [l, b, r, t] or [x, y, w, h] relative to bottom-left. 
    // PDF.js uses top-left. We need to flip Y.
    // For MVP, we'll try to just render the box and adjust.
    // Let's assume bbox is { l, t, r, b } or similar from the parent. 
    // If bbox is missing, we just show the page.

    // Note: Docling export_to_dict 'bbox' is usually [x, y, width, height]?
    // We will inspect the JSON later. For now, we prepare the Highlight div.

    return (
        <div className="pdf-snippet-container" ref={containerRef} style={{ position: 'relative', overflow: 'hidden', border: '1px solid #ccc' }}>
            <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={<div className="loading-spinner">Loading PDF...</div>}
                error={<div className="error">Failed to load PDF source.</div>}
            >
                <Page
                    pageNumber={pageNumber || 1}
                    scale={scale}
                    onLoadSuccess={onPageLoadSuccess}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                />
            </Document>

            {/* Highlight Overlay */}
            {bbox && (
                <div
                    className="pdf-highlight"
                    style={{
                        position: 'absolute',
                        left: bbox.l * scale + 'px',
                        top: bbox.t * scale + 'px', // Needs coordinate mapping verification
                        width: (bbox.r - bbox.l) * scale + 'px',
                        height: (bbox.b - bbox.t) * scale + 'px',
                        backgroundColor: 'rgba(255, 255, 0, 0.3)',
                        border: '2px solid rgba(255, 200, 0, 0.8)',
                        pointerEvents: 'none'
                    }}
                />
            )}
        </div>
    );
};

export default PDFSnippet;
