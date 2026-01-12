// Custom confirm dialog matching app style
window.confirm = function(message) {
    return new Promise((resolve) => {
        // Remove any existing modal
        const existing = document.getElementById('custom-confirm-modal');
        if (existing) existing.remove();

        // Modal HTML
        const modal = document.createElement('div');
        modal.id = 'custom-confirm-modal';
        modal.innerHTML = `
<div class="modal fade show" tabindex="-1" style="display:block; background:rgba(0,0,0,0.3); z-index:2000;">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content" style="border-radius:0.5rem;">
      <div class="modal-header" style="background:#e9ecef;">
        <h5 class="modal-title"><i class="bi bi-question-circle me-2"></i>Confirm</h5>
      </div>
      <div class="modal-body" style="font-size:1.1rem;">
        <div>${message ? String(message) : "Are you sure?"}</div>
      </div>
      <div class="modal-footer" style="background:#f8f9fa;">
        <button type="button" class="btn btn-primary btn-sm" id="custom-confirm-ok" style="min-width:80px;">OK</button>
        <button type="button" class="btn btn-secondary btn-sm" id="custom-confirm-cancel" style="min-width:80px;">Cancel</button>
      </div>
    </div>
  </div>
</div>
        `;
        document.body.appendChild(modal);

        // Focus OK by default
        setTimeout(() => {
            document.getElementById('custom-confirm-ok')?.focus();
        }, 10);

        // Handlers
        function cleanup(result) {
            modal.remove();
            resolve(result);
        }
        document.getElementById('custom-confirm-ok').onclick = () => cleanup(true);
        document.getElementById('custom-confirm-cancel').onclick = () => cleanup(false);

        // ESC closes as Cancel
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') cleanup(false);
        });

        // Prevent background scroll
        document.body.style.overflow = 'hidden';
        modal.addEventListener('transitionend', () => {
            document.body.style.overflow = '';
        });

        // Trap focus inside modal
        modal.tabIndex = -1;
        modal.focus();
    });
};
