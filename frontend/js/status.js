/**
 * Claim Status Page Logic
 */
const user = requireAuth();

document.addEventListener('DOMContentLoaded', async () => {
    if (!user) return;
    document.getElementById('navbar-root').innerHTML = renderNavbar(user.name || 'Farmer');
    await loadClaims();
});

async function loadClaims() {
    const container = document.getElementById('claimsList');
    try {
        const res = await apiGet(`/api/claims/user/${user.id}`);
        if (res.success && res.data.length > 0) {
            container.innerHTML = res.data.map(c => renderClaimCard(c)).join('');
        } else {
            container.innerHTML = `<div class="col-12 text-center text-muted py-5">
                <i class="bi bi-inbox" style="font-size:3rem;opacity:.3;"></i>
                <p class="mt-2">No claims found. <a href="claim.html">Submit your first claim</a></p>
            </div>`;
        }
    } catch (e) {
        container.innerHTML = '<div class="col-12 text-center text-danger">Failed to load claims.</div>';
    }
}

function renderClaimCard(c) {
    const steps = getTimelineSteps(c.claim_status);
    return `
    <div class="col-lg-6">
        <div class="card-govt fade-in">
            <div class="card-header-govt justify-content-between">
                <span><i class="bi bi-file-earmark-text"></i> ${c.crop_type} — ${c.damage_type}</span>
                ${getStatusBadge(c.claim_status)}
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-6"><small class="text-muted">Claim ID</small><br><code>${(c.claim_id || '').substring(0, 8)}...</code></div>
                    <div class="col-6"><small class="text-muted">Date</small><br>${formatDate(c.submitted_at)}</div>
                </div>
                <div class="row mb-3">
                    <div class="col-4"><small class="text-muted">AI Score</small><br><strong>${c.ai_score}%</strong></div>
                    <div class="col-4"><small class="text-muted">Eligibility</small><br><strong>${c.eligibility_score}/100</strong></div>
                    <div class="col-4"><small class="text-muted">Damage</small><br><strong>${c.damage_percentage}%</strong></div>
                </div>
                ${c.estimated_loss ? `<div class="mb-3"><small class="text-muted">Estimated Loss</small><br><strong>${formatCurrency(c.estimated_loss)}</strong></div>` : ''}
                ${c.officer_remarks ? `<div class="mb-3 p-2 rounded" style="background:#f5f5f5;"><small class="text-muted">Officer Remarks</small><br>${c.officer_remarks}</div>` : ''}
                <hr>
                <h6 class="mb-3"><i class="bi bi-signpost-split"></i> Progress</h6>
                <div class="timeline">
                    ${steps.map(s => `
                        <div class="timeline-item ${s.class}">
                            <div class="timeline-dot"></div>
                            <div class="timeline-content">
                                <h6>${s.label}</h6>
                                <p>${s.desc}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    </div>`;
}

function getTimelineSteps(status) {
    const all = [
        { label: 'Submitted', desc: 'Claim submitted successfully' },
        { label: 'Under Review', desc: 'AI analysis and verification in progress' },
        { label: 'Officer Verification', desc: 'Assigned to agriculture officer' },
        { label: 'Final Decision', desc: 'Claim approved or rejected' },
    ];
    const statusIndex = { pending: 1, reinspection: 2, approved: 3, rejected: 3 };
    const idx = statusIndex[status] || 0;
    return all.map((s, i) => ({
        ...s,
        class: i < idx ? 'completed' : i === idx ? 'active' : '',
    }));
}
