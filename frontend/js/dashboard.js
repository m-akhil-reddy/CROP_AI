/**
 * Dashboard Page Logic
 */
const user = requireAuth();

document.addEventListener('DOMContentLoaded', async () => {
    if (!user) return;
    document.getElementById('navbar-root').innerHTML = renderNavbar(user.name || 'Farmer');
    document.getElementById('farmerName').textContent = user.name || 'Farmer';
    await loadStats();
    await loadRecentClaims();
});

async function loadStats() {
    try {
        const res = await apiGet(`/api/dashboard/${user.id}`);
        if (res.success) {
            animateCounter('totalClaims', res.data.total_claims);
            animateCounter('pendingClaims', res.data.pending_claims);
            animateCounter('approvedClaims', res.data.approved_claims);
            animateCounter('rejectedClaims', res.data.rejected_claims);
        }
    } catch (e) { console.log('Stats load error', e); }
}

function animateCounter(id, target) {
    const el = document.getElementById(id);
    let current = 0;
    if (target === 0) { el.textContent = '0'; return; }
    const step = Math.max(1, Math.floor(target / 20));
    const interval = setInterval(() => {
        current += step;
        if (current >= target) { current = target; clearInterval(interval); }
        el.textContent = current;
    }, 50);
}

async function loadRecentClaims() {
    try {
        const res = await apiGet(`/api/claims/user/${user.id}`);
        if (res.success && res.data.length > 0) {
            const section = document.getElementById('recentClaimsSection');
            const recent = res.data.slice(0, 5);
            let html = '<div class="table-responsive"><table class="table table-govt"><thead><tr><th>Claim ID</th><th>Crop</th><th>Damage</th><th>Score</th><th>Status</th><th>Date</th></tr></thead><tbody>';
            recent.forEach(c => {
                html += `<tr>
                    <td><code>${(c.claim_id || '').substring(0, 8)}...</code></td>
                    <td>${c.crop_type}</td>
                    <td>${c.damage_type}</td>
                    <td>${c.ai_score}%</td>
                    <td>${getStatusBadge(c.claim_status)}</td>
                    <td>${formatDate(c.submitted_at)}</td>
                </tr>`;
            });
            html += '</tbody></table></div>';
            section.innerHTML = html;
        }
    } catch (e) { console.log('Recent claims error', e); }
}
