/**
 * System notification manager for toasts and banners
 */

// Show toast notification
function showToast(type, title, message) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    // Map type to Bootstrap classes
    const typeClasses = {
        'success': 'bg-success',
        'warning': 'bg-warning',
        'error': 'bg-danger',
        'info': 'bg-info'
    };
    
    const bgClass = typeClasses[type] || 'bg-secondary';
    
    // Create toast element
    const toastId = `toast-${Date.now()}`;
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" 
             role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Add to container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast with Bootstrap
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: type === 'success',
        delay: type === 'success' ? 3000 : 5000
    });
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
    
    // Limit to 3 visible toasts
    const toasts = toastContainer.querySelectorAll('.toast');
    if (toasts.length > 3) {
        const oldestToast = bootstrap.Toast.getInstance(toasts[0]);
        if (oldestToast) oldestToast.hide();
    }
}

// Show banner alert
function showBanner(controllerHost, siteName) {
    const bannerContainer = document.getElementById('banner-container');
    if (!bannerContainer) return;
    
    // Check if banner already exists
    if (bannerContainer.querySelector('.system-banner')) return;
    
    // Check if recently dismissed (within 5 minutes)
    const dismissTime = localStorage.getItem('banner_dismiss_time');
    if (dismissTime && (Date.now() - parseInt(dismissTime)) < 300000) {
        return;
    }
    
    // Default values if not provided
    controllerHost = controllerHost || 'controller';
    siteName = siteName || 'current site';
    
    const bannerHtml = `
        <div class="alert alert-danger system-banner mb-0" role="alert">
            <div class="container-fluid">
                <h5 class="alert-heading">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    Warning: Cannot connect to controller '${controllerHost}' for site '${siteName}'
                </h5>
                <p class="mb-2">
                    System running in degraded mode. The following features are unavailable:
                </p>
                <ul class="mb-2">
                    <li>Unit control and monitoring</li>
                    <li>Scheduler operations</li>
                    <li>Real-time status updates</li>
                </ul>
                <p class="mb-0">
                    <small>Retrying connection every 15 seconds...</small>
                </p>
                <button type="button" class="btn-close" onclick="dismissBanner()"></button>
            </div>
        </div>
    `;
    
    bannerContainer.innerHTML = bannerHtml;
}

// Hide banner alert
function hideBanner() {
    const bannerContainer = document.getElementById('banner-container');
    if (bannerContainer) {
        bannerContainer.innerHTML = '';
    }
    localStorage.removeItem('banner_dismiss_time');
}

// Dismiss banner (user action)
function dismissBanner() {
    hideBanner();
    localStorage.setItem('banner_dismiss_time', Date.now().toString());
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Notification system initialized');
});
