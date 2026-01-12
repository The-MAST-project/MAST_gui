const mast_control_api_base = "/mast/api/v1/control";
const mast_proxy_dash_base = "/mast-dash";
const mast_proxy_backend_base = "/mast-backend";

// getApiBaseUrl: determines the base URL for the Control API based on the current window location.
// If running on port 8000, it assumes a proxy setup and uses /mast-backend/mast/api/v1/control.
// Otherwise, it defaults to http://<controlHost>:8002/mast/api/v1/control.

function getApiBaseUrl() {
    if (window.location.pathname.includes(mast_proxy_dash_base)) {
        return `${window.location.protocol}//${window.location.host}${mast_proxy_backend_base}${mast_control_api_base}`;
    }
    // Fallback to direct
    const controlHost = window.site_control_machine || location.hostname;
    return `http://${controlHost}:8002${mast_control_api_base}`;
}

// ControlApi: fetches from the controller host for the selected site, port 8002, prepending /mast/api/v1/control to the url.
// Usage: const result = await ControlApi('/data/autofocus/unit01');  // result = data.value (or null / raw JSON per api_version)
//        const result = await ControlApi('/some/path', { method: 'POST', body: ... });
async function ControlApi(url, options = {}) {
    let path = String(url || '');
    const fullUrl = getApiBaseUrl() + normalizeUrlPath(path);

    // Default to GET if not specified
    const fetchOptions = {
        method: options.method || 'GET',
        headers: options.headers || {},
        body: options.body || undefined,
        // ...you may add credentials, mode, etc if needed
    };
    console.log(`ControlApi fetching: ${fullUrl}`, options);

    try {
        const resp = await fetch(fullUrl, fetchOptions);
        const data = await resp.json();
        // If the response is not a JSON object, return it directly
        if (!data || typeof data !== 'object') return data;

        const apiVersion = data.api_version || data.version || null;
        // If not 1.0, return the raw payload for backward/other versions
        if (apiVersion !== '1.0') return data;

        // 1.0: expect { api_version: '1.0', errors: [...], value: ... }
        if (Array.isArray(data.errors) && data.errors.length > 0) {
            console.error('ControlApi reported errors for', fullUrl, data.errors);
            return null;
        }

        // success path: return the value field
        return data.value;
    } catch (err) {
        console.error('ControlApi fetch/parsing error for', fullUrl, err);
        return null;
    }
}

/**
 * Normalize a URL path by collapsing multiple slashes into a single slash,
 * except after the protocol (e.g., http://).
 * Example: normalizeUrlPath('///foo//bar') => '/foo/bar'
 */
function normalizeUrlPath(path) {
    // Only normalize the path part, not protocol/domain
    return path.replace(/([^:]\/)\/+/g, '$1');
}
