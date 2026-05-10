/**
 * Officer Dashboard Logic
 */
const officer = requireOfficerAuth();
let allClaims = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!officer) return;
    document.getElementById('navbar-root').innerHTML = renderNavbar(officer.name || 'Officer', true);
    await loadAllClaims();
});

async function loadAllClaims() {
    try {
        const res = await apiGet('/api/claims');
        if (res.success) {
            allClaims = res.data || [];
            renderStats();
            renderTable(allClaims);
        }
    } catch (e) {
        document.getElementById('claimsTableBody').innerHTML = '<tr><td colspan="9" class="text-center text-danger">Failed to load.</td></tr>';
    }
}

function renderStats() {
    const total = allClaims.length;
    const pending = allClaims.filter(c => c.claim_status === 'pending').length;
    const approved = allClaims.filter(c => c.claim_status === 'approved').length;
    const rejected = allClaims.filter(c => c.claim_status === 'rejected').length;

    document.getElementById('officerStats').innerHTML = `
        <div class="col-6 col-lg-3"><div class="stat-card"><div class="d-flex align-items-center gap-3">
            <div class="stat-icon blue"><i class="bi bi-file-earmark-text"></i></div>
            <div><div class="stat-value">${total}</div><div class="stat-label">Total</div></div>
        </div></div></div>
        <div class="col-6 col-lg-3"><div class="stat-card"><div class="d-flex align-items-center gap-3">
            <div class="stat-icon yellow"><i class="bi bi-hourglass-split"></i></div>
            <div><div class="stat-value">${pending}</div><div class="stat-label">Pending</div></div>
        </div></div></div>
        <div class="col-6 col-lg-3"><div class="stat-card"><div class="d-flex align-items-center gap-3">
            <div class="stat-icon green"><i class="bi bi-check-circle"></i></div>
            <div><div class="stat-value">${approved}</div><div class="stat-label">Approved</div></div>
        </div></div></div>
        <div class="col-6 col-lg-3"><div class="stat-card"><div class="d-flex align-items-center gap-3">
            <div class="stat-icon red"><i class="bi bi-x-circle"></i></div>
            <div><div class="stat-value">${rejected}</div><div class="stat-label">Rejected</div></div>
        </div></div></div>
    `;
}

function renderTable(claims) {
    const tbody = document.getElementById('claimsTableBody');
    if (claims.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center py-4 text-muted">No claims found.</td></tr>';
        return;
    }
    tbody.innerHTML = claims.map(c => `
        <tr>
            <td><code>${(c.claim_id || '').substring(0, 8)}</code></td>
            <td>${c.user_id ? c.user_id.substring(0, 8) + '...' : '—'}</td>
            <td>${c.crop_type}</td>
            <td>${c.damage_type}</td>
            <td><strong>${c.ai_score}%</strong></td>
            <td><strong>${c.eligibility_score}/100</strong></td>
            <td>${getStatusBadge(c.claim_status)}</td>
            <td>${formatDate(c.submitted_at)}</td>
            <td><a href="officer-detail.html?id=${c.claim_id}" class="btn btn-govt" style="padding:6px 14px;font-size:.8rem;"><i class="bi bi-eye"></i> View</a></td>
        </tr>
    `).join('');
}

function filterClaims() {
    const status = document.getElementById('filterStatus').value;
    const filtered = status === 'all' ? allClaims : allClaims.filter(c => c.claim_status === status);
    renderTable(filtered);
}
