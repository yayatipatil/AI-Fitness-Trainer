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
document.addEventListener('DOMContentLoaded', checkAuth);
