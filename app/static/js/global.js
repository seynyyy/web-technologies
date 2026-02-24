// Global toast notification function
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('toast-notification');
    const toastBody = document.getElementById('toast-body');
    toastBody.textContent = message;
    
    toastEl.classList.remove('text-bg-success', 'text-bg-danger', 'text-bg-warning', 'text-bg-info');
    
    if (type === 'success') {
        toastEl.classList.add('text-bg-success');
    } else if (type === 'danger' || type === 'error') {
        toastEl.classList.add('text-bg-danger');
    } else if (type === 'warning') {
        toastEl.classList.add('text-bg-warning');
    } else {
        toastEl.classList.add('text-bg-info');
    }
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Global 401 handler - intercepts all fetch responses
const originalFetch = window.fetch;
window.fetch = function(...args) {
    return originalFetch.apply(this, args)
        .then(response => {
            if (response.status === 401 && !window.location.pathname.includes('/login')) {
                showToast('Сесія завершена. Увійдіть знову.', 'warning');
                setTimeout(() => {
                    localStorage.removeItem('access_token');
                    document.cookie = 'access_token=; path=/; max-age=0';
                    window.location.href = '/login';
                }, 1000);
            }
            return response;
        });
};

// Logout handler
const logoutLink = document.getElementById('logout-link');
if (logoutLink) {
    logoutLink.addEventListener('click', (event) => {
        event.preventDefault();
        localStorage.removeItem('access_token');
        document.cookie = 'access_token=; path=/; max-age=0';
        window.location.href = '/login';
    });
}
