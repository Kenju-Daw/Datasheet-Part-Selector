/**
 * API Client - Wrapper for backend API calls
 */
const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    // Don't set Content-Type for FormData
    if (options.body instanceof FormData) {
        delete config.headers['Content-Type'];
    }

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Request failed' }));
            throw new Error(error.detail || error.message || `HTTP ${response.status}`);
        }

        return response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ============ Datasheet API ============

export const datasheetAPI = {
    /**
     * Upload a PDF datasheet
     */
    upload: async (file, metadata = {}) => {
        const formData = new FormData();
        formData.append('file', file);
        if (metadata.name) formData.append('name', metadata.name);
        if (metadata.manufacturer) formData.append('manufacturer', metadata.manufacturer);
        if (metadata.part_family) formData.append('part_family', metadata.part_family);

        return fetchAPI('/datasheets/upload', {
            method: 'POST',
            body: formData,
        });
    },

    /**
     * List all datasheets
     */
    list: (page = 1, pageSize = 20, includeArchived = false) => {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
            include_archived: includeArchived.toString(),
        });
        return fetchAPI(`/datasheets/?${params}`);
    },

    /**
     * Get single datasheet
     */
    get: (id) => fetchAPI(`/datasheets/${id}`),

    /**
     * Trigger re-processing
     */
    reprocess: (id) => fetchAPI(`/datasheets/${id}/reprocess`, { method: 'POST' }),

    /**
     * Archive/restore/delete
     */
    archive: (id, action) => fetchAPI(`/datasheets/${id}/archive`, {
        method: 'POST',
        body: JSON.stringify({ action }),
    }),

    /**
     * List archived datasheets
     */
    listArchived: (page = 1, pageSize = 20) => {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
        });
        return fetchAPI(`/datasheets/archive/list?${params}`);
    },
};

// ============ Parts API ============

export const partsAPI = {
    /**
     * Get schema for a datasheet
     */
    getSchema: (datasheetId) => fetchAPI(`/parts/schema/${datasheetId}`),

    /**
     * Configure/generate part number
     */
    configure: (schemaId, fieldValues) => fetchAPI('/parts/configure', {
        method: 'POST',
        body: JSON.stringify({ schema_id: schemaId, field_values: fieldValues }),
    }),

    /**
     * Decode existing part number
     */
    decode: (partNumber) => fetchAPI('/parts/decode', {
        method: 'POST',
        body: JSON.stringify({ part_number: partNumber }),
    }),

    /**
     * Search parts
     */
    search: (query = '', filters = {}, page = 1, pageSize = 20) => fetchAPI('/parts/search', {
        method: 'POST',
        body: JSON.stringify({ query, filters, page, page_size: pageSize }),
    }),
};

// ============ Progress SSE ============

/**
 * Connect to progress stream for a datasheet
 * @param {string} datasheetId 
 * @param {function} onProgress - Callback for progress updates
 * @param {function} onComplete - Callback when complete
 * @param {function} onError - Callback on error
 * @returns {function} Cleanup function to close connection
 */
export function connectProgressStream(datasheetId, onProgress, onComplete, onError) {
    const eventSource = new EventSource(`${API_BASE}/progress/${datasheetId}`);

    eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        onProgress?.(data);
    });

    eventSource.addEventListener('complete', (event) => {
        const data = JSON.parse(event.data);
        onComplete?.(data);
        eventSource.close();
    });

    eventSource.addEventListener('timeout', () => {
        onError?.(new Error('Connection timed out'));
        eventSource.close();
    });

    eventSource.onerror = (error) => {
        onError?.(error);
        eventSource.close();
    };

    // Return cleanup function
    return () => eventSource.close();
}

export default {
    datasheets: datasheetAPI,
    parts: partsAPI,
    connectProgressStream,
};
