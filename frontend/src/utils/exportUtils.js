/**
 * CSV/PDF Export Utility
 * 
 * Implements UX-007: Export configurator results to CSV/PDF
 */

/**
 * Export part configuration to CSV format
 */
export function exportToCSV(partNumber, config, breakdown) {
    const csvRows = [];

    // Header
    csvRows.push(['Field', 'Value', 'Description']);

    // Part Number
    csvRows.push(['Part Number', partNumber, 'Complete MIL-DTL-38999 part number']);
    csvRows.push(['', '', '']); // Empty row

    // Breakdown
    csvRows.push(['Component', 'Code', 'Description']);
    for (const [key, value] of Object.entries(breakdown)) {
        const label = formatFieldLabel(key);
        csvRows.push([label, value, getFieldDescription(key, value)]);
    }

    csvRows.push(['', '', '']); // Empty row

    // Configuration details
    if (config) {
        csvRows.push(['Configuration', 'Details', '']);
        for (const [key, value] of Object.entries(config)) {
            csvRows.push([formatFieldLabel(key), value, '']);
        }
    }

    // Convert to CSV string
    const csvContent = csvRows
        .map(row => row.map(cell => `"${cell}"`).join(','))
        .join('\n');

    // Download
    downloadFile(csvContent, `${partNumber}.csv`, 'text/csv');
}

/**
 * Export part configuration to JSON format
 */
export function exportToJSON(partNumber, config, breakdown) {
    const data = {
        partNumber,
        breakdown,
        configuration: config,
        generatedAt: new Date().toISOString(),
        standard: 'MIL-DTL-38999'
    };

    const jsonContent = JSON.stringify(data, null, 2);
    downloadFile(jsonContent, `${partNumber}.json`, 'application/json');
}

/**
 * Helper: Download file
 */
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

/**
 * Helper: Format field labels
 */
function formatFieldLabel(key) {
    const labels = {
        spec: 'Specification',
        connector_type: 'Connector Type',
        finish: 'Shell Finish',
        class: 'Shell Class',
        shell_size: 'Shell Size',
        insert_arrangement: 'Insert Arrangement',
        contact_type: 'Contact Type',
        key_position: 'Key Position'
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Helper: Get field descriptions
 */
function getFieldDescription(key, value) {
    const descriptions = {
        spec: 'Military specification number',
        connector_type: 'Type of connector mounting',
        finish: 'Shell plating/finish type',
        class: 'Environmental sealing class',
        shell_size: 'Shell diameter/size',
        insert_arrangement: 'Contact layout pattern',
        contact_type: 'Pin (P) or Socket (S) contacts',
        key_position: 'Polarization keyway position'
    };
    return descriptions[key] || '';
}
