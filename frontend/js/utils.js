/**
 * Shared Utilities — Toasts, Spinners, Validation, Session
 */

/* ── Toast Notifications ─────────────────────────────────── */
function ensureToastContainer() {
    let c = document.getElementById('toast-container');
    if (!c) {
        c = document.createElement('div');
        c.id = 'toast-container';
        c.className = 'toast-container';
        document.body.appendChild(c);
    }
    return c;
}

function showToast(message, type = 'success', duration = 3500) {
    const container = ensureToastContainer();
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
    const toast = document.createElement('div');
    toast.className = `toast-item ${type}`;
    toast.innerHTML = `<i class="bi ${icons[type] || icons.info}"></i><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100px)'; setTimeout(() => toast.remove(), 400); }, duration);
}

/* ── Spinner Overlay ─────────────────────────────────────── */
function ensureSpinner() {
    let s = document.getElementById('spinner-overlay');
    if (!s) {
        s = document.createElement('div');
        s.id = 'spinner-overlay';
        s.className = 'spinner-overlay';
        s.innerHTML = '<div class="spinner-govt"></div><div class="spinner-text">Processing...</div>';
        document.body.appendChild(s);
    }
    return s;
}

function showSpinner(text = 'Processing...') {
    const s = ensureSpinner();
    s.querySelector('.spinner-text').textContent = text;
    s.classList.add('show');
}

function hideSpinner() {
    const s = document.getElementById('spinner-overlay');
    if (s) s.classList.remove('show');
}

/* ── Validation Helpers ──────────────────────────────────── */
function validatePhone(phone) {
    return /^\d{10}$/.test(phone);
}

function validateAadhaar(aadhaar) {
    return /^\d{12}$/.test(aadhaar);
}

function validateIFSC(ifsc) {
    return /^[A-Z]{4}0[A-Z0-9]{6}$/.test(ifsc.toUpperCase());
}

function detectBankFromIFSC(ifsc) {
    const prefix = ifsc.substring(0, 4).toUpperCase();
    const banks = {
        'SBIN': 'State Bank of India', 'HDFC': 'HDFC Bank', 'ICIC': 'ICICI Bank',
        'PUNB': 'Punjab National Bank', 'BARB': 'Bank of Baroda', 'CNRB': 'Canara Bank',
        'UBIN': 'Union Bank of India', 'IOBA': 'Indian Overseas Bank', 'BKID': 'Bank of India',
        'UTIB': 'Axis Bank', 'KKBK': 'Kotak Mahindra Bank', 'YESB': 'Yes Bank',
        'IDIB': 'Indian Bank', 'ALLA': 'Allahabad Bank', 'ANDB': 'Andhra Bank',
    };
    return banks[prefix] || '';
}

function setFieldValid(input, valid, message = '') {
    input.classList.remove('is-valid', 'is-invalid');
    input.classList.add(valid ? 'is-valid' : 'is-invalid');
    const fb = input.nextElementSibling;
    if (fb && (fb.classList.contains('invalid-feedback') || fb.classList.contains('valid-feedback'))) {
        fb.textContent = message;
    }
}

/* ── Session Management ──────────────────────────────────── */
function saveSession(user) {
    localStorage.setItem('crop_ai_user', JSON.stringify(user));
}

function getSession() {
    try { return JSON.parse(localStorage.getItem('crop_ai_user')); } catch { return null; }
}

function clearSession() {
    localStorage.removeItem('crop_ai_user');
}

function requireAuth() {
    const user = getSession();
    if (!user) { window.location.href = 'login.html'; return null; }
    return user;
}

function saveOfficerSession(officer) {
    localStorage.setItem('crop_ai_officer', JSON.stringify(officer));
}

function getOfficerSession() {
    try { return JSON.parse(localStorage.getItem('crop_ai_officer')); } catch { return null; }
}

function clearOfficerSession() {
    localStorage.removeItem('crop_ai_officer');
}

function requireOfficerAuth() {
    const officer = getOfficerSession();
    if (!officer) { window.location.href = 'officer-login.html'; return null; }
    return officer;
}

/* ── API Helpers ─────────────────────────────────────────── */
async function apiPost(endpoint, data) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
    return res.json();
}

async function apiGet(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`);
    return res.json();
}

async function apiPut(endpoint, data) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
    });
    return res.json();
}

/* ── Format Helpers ──────────────────────────────────────── */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function getStatusBadge(status) {
    const map = {
        pending: '<span class="badge-status badge-pending">⏳ Pending</span>',
        approved: '<span class="badge-status badge-approved">✅ Approved</span>',
        rejected: '<span class="badge-status badge-rejected">❌ Rejected</span>',
        reinspection: '<span class="badge-status badge-review">🔍 Re-inspection</span>',
    };
    return map[status] || map.pending;
}

/* ── Navbar Renderer ─────────────────────────────────────── */
function renderNavbar(userName, isOfficer = false) {
    return `
    <nav class="navbar navbar-expand-lg navbar-govt">
        <div class="container">
            <a class="navbar-brand" href="${isOfficer ? 'officer.html' : 'dashboard.html'}">
                <span class="logo-icon-sm">🌾</span>
                Crop Damage Assessment
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav">
                <span class="navbar-toggler-icon" style="filter:invert(1)"></span>
            </button>
            <div class="collapse navbar-collapse" id="mainNav">
                <ul class="navbar-nav ms-auto align-items-center gap-2">
                    ${isOfficer ? `
                        <li class="nav-item"><a class="nav-link" href="officer.html">Dashboard</a></li>
                    ` : `
                        <li class="nav-item"><a class="nav-link" href="dashboard.html">Dashboard</a></li>
                        <li class="nav-item"><a class="nav-link" href="claim.html">New Claim</a></li>
                        <li class="nav-item"><a class="nav-link" href="status.html">My Claims</a></li>
                    `}
                    <li class="nav-item"><span class="user-badge"><i class="bi bi-person-fill"></i> ${userName}</span></li>
                    <li class="nav-item">
                        <button class="btn btn-logout" onclick="${isOfficer ? 'clearOfficerSession' : 'clearSession'}(); window.location.href='${isOfficer ? 'officer-login' : 'login'}.html';">
                            <i class="bi bi-box-arrow-right"></i> Logout
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>`;
}
