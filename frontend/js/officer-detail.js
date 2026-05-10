/**
 * Officer Claim Detail Page Logic
 */
const officer = requireOfficerAuth();
const claimId = new URLSearchParams(window.location.search).get('id');

document.addEventListener('DOMContentLoaded', async () => {
    if (!officer) return;
    document.getElementById('navbar-root').innerHTML = renderNavbar(officer.name || 'Officer', true);
    if (!claimId) { document.getElementById('claimDetail').innerHTML = '<p class="text-danger">No claim ID provided.</p>'; return; }
    await loadClaimDetail();
});

async function loadClaimDetail() {
    try {
        const res = await apiGet(`/api/claims/${claimId}`);
        if (res.success) {
            renderDetail(res.data);
        } else {
            document.getElementById('claimDetail').innerHTML = '<p class="text-danger">Claim not found.</p>';
        }
    } catch (e) {
        document.getElementById('claimDetail').innerHTML = '<p class="text-danger">Failed to load claim.</p>';
    }
}

function renderDetail(data) {
    const c = data.claim, u = data.user || {}, id = data.identity || {}, b = data.bank || {}, l = data.land || {}, uploads = data.uploads || [];
    const scoreClass = (c.eligibility_score || 0) >= 80 ? 'high' : (c.eligibility_score || 0) >= 50 ? 'medium' : 'low';

    document.getElementById('claimDetail').innerHTML = `
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-4">
            <h4 class="section-title mb-0"><i class="bi bi-file-earmark-text"></i> Claim: ${(c.claim_id || '').substring(0, 8)}...</h4>
            ${getStatusBadge(c.claim_status)}
        </div>

        <div class="row g-4">
            <!-- Farmer Info -->
            <div class="col-md-6">
                <div class="card-govt h-100">
                    <div class="card-header-govt"><i class="bi bi-person"></i> Farmer Details</div>
                    <div class="card-body">
                        <p><strong>Name:</strong> ${u.name || '—'}</p>
                        <p><strong>Phone:</strong> ${u.phone || '—'}</p>
                        <p><strong>Aadhaar:</strong> ${id.aadhaar_number ? id.aadhaar_number.replace(/(\d{4})/g, '$1 ').trim() : '—'}</p>
                        <p><strong>Ration Card:</strong> ${id.ration_card_type || '—'} — ${id.ration_card_number || '—'}</p>
                    </div>
                </div>
            </div>

            <!-- Land Info -->
            <div class="col-md-6">
                <div class="card-govt h-100">
                    <div class="card-header-govt"><i class="bi bi-geo-alt"></i> Land Details</div>
                    <div class="card-body">
                        <p><strong>Survey No:</strong> ${l.survey_number || '—'}</p>
                        <p><strong>Area:</strong> ${l.land_area || '—'} acres</p>
                        <p><strong>Location:</strong> ${l.village || '—'}, ${l.mandal || '—'}, ${l.district || '—'}, ${l.state || '—'}</p>
                        <p><strong>GPS:</strong> ${l.gps_location || c.gps_location || '—'}</p>
                    </div>
                </div>
            </div>

            <!-- Crop & Damage -->
            <div class="col-md-6">
                <div class="card-govt h-100">
                    <div class="card-header-govt"><i class="bi bi-flower1"></i> Crop & Damage</div>
                    <div class="card-body">
                        <p><strong>Crop:</strong> ${c.crop_type}</p>
                        <p><strong>Damage Type:</strong> ${c.damage_type}</p>
                        <p><strong>Stage:</strong> ${c.crop_stage || '—'}</p>
                        <p><strong>Damage %:</strong> ${c.damage_percentage}%</p>
                        <p><strong>Est. Loss:</strong> ${formatCurrency(c.estimated_loss || 0)}</p>
                    </div>
                </div>
            </div>

            <!-- AI Analysis -->
            <div class="col-md-6">
                <div class="card-govt h-100">
                    <div class="card-header-govt"><i class="bi bi-cpu"></i> AI Analysis</div>
                    <div class="card-body">
                        <div class="d-flex align-items-center gap-3 mb-3">
                            <div class="ai-score-circle ${scoreClass}">${c.ai_score || 0}</div>
                            <div><strong>AI Confidence: ${c.ai_score || 0}%</strong><br>Eligibility: ${c.eligibility_score || 0}/100</div>
                        </div>
                        <p class="small">${c.ai_result || '—'}</p>
                        <hr>
                        <div class="row text-center">
                            <div class="col-4"><small class="text-muted">Fraud Risk</small><br><strong>${c.fraud_probability || '—'}%</strong></div>
                            <div class="col-4"><small class="text-muted">Weather</small><br><strong>${c.weather_match ? '✅ Match' : '—'}</strong></div>
                            <div class="col-4"><small class="text-muted">GPS</small><br><strong>${c.gps_match ? '✅ Match' : '—'}</strong></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Weather -->
            <div class="col-md-6">
                <div class="weather-card">
                    <h6><i class="bi bi-cloud-rain"></i> Weather / Calamity Report</h6>
                    <p>${c.weather_report || 'No report available.'}</p>
                </div>
            </div>

            <!-- Bank Details -->
            <div class="col-md-6">
                <div class="card-govt h-100">
                    <div class="card-header-govt"><i class="bi bi-bank2"></i> Bank Details</div>
                    <div class="card-body">
                        <p><strong>Holder:</strong> ${b.account_holder_name || '—'}</p>
                        <p><strong>Bank:</strong> ${b.bank_name || '—'}</p>
                        <p><strong>Account:</strong> ${b.account_number ? '****' + b.account_number.slice(-4) : '—'}</p>
                        <p><strong>IFSC:</strong> ${b.ifsc_code || '—'}</p>
                    </div>
                </div>
            </div>

            <!-- Uploaded Evidence -->
            ${uploads.length > 0 ? `
            <div class="col-12">
                <div class="card-govt">
                    <div class="card-header-govt"><i class="bi bi-images"></i> Uploaded Evidence</div>
                    <div class="card-body">
                        <div class="preview-grid">
                            ${uploads.filter(u => u.file_type === 'image').map(u => `<div class="preview-item"><img src="${u.file_url}" alt="${u.original_name}"></div>`).join('')}
                        </div>
                    </div>
                </div>
            </div>` : ''}

            <!-- Action Buttons -->
            <div class="col-12">
                <div class="card-govt">
                    <div class="card-header-govt"><i class="bi bi-check2-square"></i> Officer Decision</div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label-govt">Remarks</label>
                            <textarea id="officerRemarks" class="form-control form-control-govt" rows="3" placeholder="Enter your remarks...">${c.officer_remarks || ''}</textarea>
                        </div>
                        <div class="d-flex gap-3 flex-wrap">
                            <button class="btn btn-govt flex-fill" onclick="updateStatus('approved')">
                                <i class="bi bi-check-circle"></i> Approve Claim
                            </button>
                            <button class="btn btn-danger flex-fill" onclick="updateStatus('rejected')">
                                <i class="bi bi-x-circle"></i> Reject Claim
                            </button>
                            <button class="btn btn-warning-custom flex-fill" onclick="updateStatus('reinspection')">
                                <i class="bi bi-arrow-repeat"></i> Request Re-inspection
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function updateStatus(status) {
    const remarks = document.getElementById('officerRemarks').value.trim();
    showSpinner('Updating claim...');
    try {
        const res = await apiPut(`/api/claims/${claimId}/status`, { status, remarks });
        hideSpinner();
        if (res.success) {
            showToast(`Claim ${status} successfully!`, 'success');
            setTimeout(() => { window.location.href = 'officer.html'; }, 1000);
        } else { showToast('Failed to update.', 'error'); }
    } catch (e) { hideSpinner(); showToast('Server error.', 'error'); }
}
