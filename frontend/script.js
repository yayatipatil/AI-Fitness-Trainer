const API_BASE_URL = 'http://127.0.0.1:8000';

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}

// Ensure user is logged in for protected pages
function checkAuth() {
    const publicPages = ['login.html', 'register.html', 'index.html', ''];
    const path = window.location.pathname.split('/').pop();
    
    if (!getToken() && !publicPages.includes(path)) {
        window.location.href = 'login.html';
    } else if (getToken() && (path === 'login.html' || path === 'register.html')) {
        window.location.href = 'dashboard.html';
    }
}

async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method: method,
        headers: headers,
    };

    if (body) {
        if (body instanceof URLSearchParams) {
            config.headers['Content-Type'] = 'application/x-www-form-urlencoded';
            config.body = body;
        } else {
            config.body = JSON.stringify(body);
        }
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    const data = await response.json().catch(() => ({})); // Handle cases where response isn't JSON

    if (!response.ok) {
        if (response.status === 401) {
            // Token is invalid or expired
            localStorage.removeItem('token');
            window.location.href = 'login.html';
            return;
        }
        throw new Error(data.detail || 'API Error');
    }

    return data;
}

// Chart instance
let progressChart = null;

function renderChart(dates, calories) {
    const ctx = document.getElementById('progressChart');
    if (!ctx) return;

    if (progressChart) {
        progressChart.destroy();
    }

    progressChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Calories Burned',
                data: calories,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { labels: { color: '#f8fafc', font: { family: 'Outfit', size: 14 } } },
                tooltip: { backgroundColor: 'rgba(15, 23, 42, 0.9)', titleFont: { family: 'Outfit' }, bodyFont: { family: 'Outfit' } }
            }
        }
    });
}

// Run auth check on load
// --- Global UX Utilities ---

function showToast(message, type = "success") {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.gap = '10px';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    
    // Set colors based on type
    const bgColor = type === "error" ? "rgba(239, 68, 68, 0.9)" : 
                   type === "warning" ? "rgba(245, 158, 11, 0.9)" : 
                   "rgba(16, 185, 129, 0.9)";
                   
    const iconName = type === "error" ? "x-circle" : 
                    type === "warning" ? "alert-triangle" : 
                    "check-circle";

    toast.style.background = bgColor;
    toast.style.color = "white";
    toast.style.padding = "12px 20px";
    toast.style.borderRadius = "8px";
    toast.style.boxShadow = "0 4px 15px rgba(0,0,0,0.3)";
    toast.style.display = "flex";
    toast.style.alignItems = "center";
    toast.style.gap = "10px";
    toast.style.minWidth = "250px";
    toast.style.transform = "translateX(120%)";
    toast.style.opacity = "0";
    toast.style.transition = "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
    
    toast.innerHTML = `
        <i data-lucide="${iconName}" style="width: 20px; height: 20px;"></i>
        <span style="font-weight: 600; font-size: 0.95rem;">${message}</span>
    `;

    container.appendChild(toast);
    if (window.lucide) {
        lucide.createIcons({ root: toast });
    }

    // Trigger animation in
    setTimeout(() => {
        toast.style.transform = "translateX(0)";
        toast.style.opacity = "1";
    }, 10);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.transform = "translateX(120%)";
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showLoadingSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Check if already loading
    if (container.querySelector('.loading-overlay')) return;
    
    // Make container relative if static
    const computedStyle = window.getComputedStyle(container);
    if (computedStyle.position === 'static') {
        container.style.position = 'relative';
    }
    
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.style.position = 'absolute';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.background = 'rgba(13, 22, 39, 0.7)';
    overlay.style.backdropFilter = 'blur(4px)';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.zIndex = '50';
    overlay.style.borderRadius = computedStyle.borderRadius || 'inherit';
    
    overlay.innerHTML = `<i data-lucide="loader-2" class="spin-icon" style="width: 32px; height: 32px; color: var(--primary);"></i>`;
    
    container.appendChild(overlay);
    if (window.lucide) {
        lucide.createIcons({ root: overlay });
    }
}

function hideLoadingSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const overlay = container.querySelector('.loading-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.3s';
        setTimeout(() => overlay.remove(), 300);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    highlightActiveNavLink();
    injectBackToTop();
});

// Auto-highlight the nav link that matches the current page
function highlightActiveNavLink() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('nav .links a').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '#' && currentPage === href) {
            link.classList.add('active-page');
        }
    });
}

// Inject a back-to-top button once and wire up scroll visibility
function injectBackToTop() {
    if (document.getElementById('back-to-top')) return;

    const btn = document.createElement('button');
    btn.id = 'back-to-top';
    btn.setAttribute('aria-label', 'Back to top');
    btn.setAttribute('data-tip', 'Back to top');
    btn.innerHTML = '<i data-lucide="chevron-up" style="width:20px;height:20px;"></i>';
    document.body.appendChild(btn);

    if (window.lucide) lucide.createIcons({ root: btn });

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}
