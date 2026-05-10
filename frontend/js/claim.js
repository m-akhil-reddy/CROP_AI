/**
 * Claim Submission Page Logic
 */
const user = requireAuth();
let claimMap = null, claimMarker = null, aiData = null;

document.addEventListener('DOMContentLoaded', () => {
    if (user) document.getElementById('navbar-root').innerHTML = renderNavbar(user.name || 'Farmer');
});

/* ── File Preview ───────────────────────────────────────── */
function previewFiles(inputId, previewId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(previewId);
    container.innerHTML = '';
    Array.from(input.files).forEach((file, i) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.className = 'preview-item';
            div.innerHTML = `<img src="${e.target.result}" alt="preview"><button class="remove-btn" onclick="this.parentElement.remove()">×</button>`;
            container.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

function previewVideo() {
    const input = document.getElementById('videoUpload');
    const container = document.getElementById('videoPreview');
    container.innerHTML = '';
    if (input.files[0]) {
        const url = URL.createObjectURL(input.files[0]);
        container.innerHTML = `<video controls width="100%" style="border-radius:var(--radius-sm);max-height:240px;"><source src="${url}"></video>`;
    }
}

/* ── GPS ─────────────────────────────────────────────────── */
function captureClaimGPS() {
    if (!navigator.geolocation) { showToast('Geolocation not supported.', 'error'); return; }
    showSpinner('Capturing GPS...');
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            hideSpinner();
            const lat = pos.coords.latitude.toFixed(6), lng = pos.coords.longitude.toFixed(6);
            document.getElementById('claimGps').value = `${lat}, ${lng}`;
            document.getElementById('claimGpsStatus').innerHTML = `<div class="verify-badge"><i class="bi bi-geo-alt-fill"></i> ${lat}, ${lng}</div>`;
            const mapEl = document.getElementById('claimMap');
            mapEl.style.display = 'block';
            if (!claimMap) {
                claimMap = L.map('claimMap').setView([lat, lng], 15);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(claimMap);
            } else { claimMap.setView([lat, lng], 15); }
            if (claimMarker) claimMap.removeLayer(claimMarker);
            claimMarker = L.marker([lat, lng]).addTo(claimMap).bindPopup('Claim Location').openPopup();
            showToast('GPS captured!', 'success');
        },
        () => {
            hideSpinner();
            const lat = 17.385044, lng = 78.486671;
            document.getElementById('claimGps').value = `${lat}, ${lng}`;
            document.getElementById('claimGpsStatus').innerHTML = `<div class="verify-badge"><i class="bi bi-geo-alt-fill"></i> Demo: ${lat}, ${lng}</div>`;
            const mapEl = document.getElementById('claimMap');
            mapEl.style.display = 'block';
            if (!claimMap) {
                claimMap = L.map('claimMap').setView([lat, lng], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(claimMap);
            }
            if (claimMarker) claimMap.removeLayer(claimMarker);
            claimMarker = L.marker([lat, lng]).addTo(claimMap).bindPopup('Demo Location').openPopup();
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

/* ── AI Analysis (upgraded with real ML pipeline) ───────── */
async function runAIAnalysis() {
    const cropType = document.getElementById('cropType').value;
    const damageType = document.getElementById('damageType').value;
    if (!cropType || !damageType) { showToast('Please select crop type and damage type first.', 'error'); return; }

    showSpinner('Running AI Analysis...');
    try {
        // Build FormData to send images + metadata together
        const fd = new FormData();
        fd.append('crop_type', cropType);
        fd.append('damage_type', damageType);
        fd.append('damage_percentage', document.getElementById('damagePercentage').value);
        fd.append('crop_stage', document.getElementById('cropStage').value);
        fd.append('district', '');
        fd.append('land_area', '1');
        fd.append('gps_location', document.getElementById('claimGps').value || '');
        fd.append('user_id', user ? user.id : '');

        // Attach uploaded images for real AI analysis
        const imageInput = document.getElementById('imageUpload');
        if (imageInput && imageInput.files.length > 0) {
            for (const file of imageInput.files) {
                fd.append('images', file);
            }
        }

        const res = await fetch(`${API_BASE}/api/analyze`, { method: 'POST', body: fd }).then(r => r.json());
        hideSpinner();

        if (res.success) {
            aiData = res.data;
            renderAIResults(res.data);
            document.getElementById('submitClaimBtn').disabled = false;
            showToast('AI analysis complete!', 'success');
        }
    } catch (e) { hideSpinner(); showToast('Analysis failed.', 'error'); }
}

function renderAIResults(data) {
    const a = data.analysis, e = data.eligibility, w = data.weather, l = data.loss_estimate;
    const fraud = data.fraud || {};
    const weatherVal = data.weather_validation || {};
    const gpsVal = data.gps_validation || {};
    const modelMode = data.model_mode || 'simulation';
    const scoreClass = e.eligibility_score >= 80 ? 'high' : e.eligibility_score >= 50 ? 'medium' : 'low';
    const barClass = e.eligibility_score >= 80 ? 'green' : e.eligibility_score >= 50 ? 'yellow' : 'red';
    const fraudPct = fraud.fraud_probability || 0;
    const fraudClass = fraudPct <= 20 ? 'green' : fraudPct <= 50 ? 'yellow' : 'red';

    document.getElementById('aiResultSection').style.display = 'block';
    document.getElementById('aiResultSection').innerHTML = `
        <div class="ai-result-card mb-3">
            <h6><i class="bi bi-cpu"></i> AI Damage Analysis
                <span class="badge-status" style="float:right;font-size:.7rem;background:${modelMode==='real_cnn'?'#e8f5e9':'#e3f2fd'};color:${modelMode==='real_cnn'?'#2e7d32':'#1565c0'}">
                    ${modelMode === 'real_cnn' ? '🧠 Real CNN' : '⚡ Simulation'}
                </span>
            </h6>
            <p class="mb-2"><strong>Damage Type:</strong> ${a.damage_type || a.damage_type_raw} | <strong>Severity:</strong> ${a.severity}</p>
            <p class="mb-2"><strong>Confidence:</strong> ${a.ai_score || a.confidence}%</p>
            <ul class="mb-2">${(a.indicators||[]).map(i => `<li>${i}</li>`).join('')}</ul>
            <p class="mb-0"><strong>Recommendation:</strong> ${a.recommendation}</p>
        </div>
        <div class="ai-result-card mb-3">
            <h6><i class="bi bi-speedometer2"></i> Claim Eligibility Score</h6>
            <div class="d-flex align-items-center gap-3 mb-2">
                <div class="ai-score-circle ${scoreClass}">${e.eligibility_score}</div>
                <div><strong>${e.status}</strong><br><small class="text-muted">Score: ${e.eligibility_score}/100 — ${e.risk_level || ''}</small></div>
            </div>
            <div class="eligibility-bar"><div class="eligibility-fill ${barClass}" style="width:${e.eligibility_score}%"></div></div>
        </div>
        <div class="row g-3 mb-3">
            <div class="col-md-4">
                <div class="ai-result-card text-center h-100">
                    <h6><i class="bi bi-shield-exclamation"></i> Fraud Check</h6>
                    <div class="ai-score-circle ${fraudClass}" style="width:60px;height:60px;font-size:1.1rem;margin:8px auto;">${fraudPct}%</div>
                    <small class="text-muted">${fraudPct <= 20 ? 'Low Risk' : fraudPct <= 50 ? 'Medium Risk' : 'High Risk'}</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="ai-result-card text-center h-100">
                    <h6><i class="bi bi-cloud-rain"></i> Weather</h6>
                    <div style="font-size:2rem;">${weatherVal.weather_match ? '✅' : '⚠️'}</div>
                    <small class="text-muted">Score: ${weatherVal.weather_score || '—'}/100</small>
                </div>
            </div>
            <div class="col-md-4">
                <div class="ai-result-card text-center h-100">
                    <h6><i class="bi bi-geo-alt"></i> GPS</h6>
                    <div style="font-size:2rem;">${gpsVal.gps_match !== false ? '✅' : '❌'}</div>
                    <small class="text-muted">${gpsVal.distance_km != null ? gpsVal.distance_km + ' km' : 'N/A'}</small>
                </div>
            </div>
        </div>
        <div class="weather-card mb-3">
            <h6><i class="bi bi-cloud-rain"></i> Weather / Calamity Report</h6>
            <p class="mb-1"><strong>${w.event || 'N/A'}</strong> — Severity: ${w.severity || 'N/A'}</p>
            <p class="mb-0">${w.description || ''}</p>
        </div>
    `;

    // Update sidebar summary
    const loss = parseFloat(document.getElementById('estimatedLoss').value) || l.estimated_loss;
    document.getElementById('claimSummary').innerHTML = `
        <div class="mb-2"><strong>Crop:</strong> ${a.crop_type || ''}</div>
        <div class="mb-2"><strong>Damage:</strong> ${a.damage_type || ''} (${a.severity})</div>
        <div class="mb-2"><strong>AI Score:</strong> ${a.ai_score || a.confidence}%</div>
        <div class="mb-2"><strong>Eligibility:</strong> <span style="color:${e.color === 'green' ? 'var(--success)' : e.color === 'yellow' ? 'var(--warning)' : 'var(--danger)'};font-weight:700;">${e.eligibility_score}/100</span></div>
        <div class="mb-2"><strong>Fraud Risk:</strong> ${fraudPct}%</div>
        <div class="mb-2"><strong>Weather:</strong> ${w.event || '—'}</div>
        <hr>
        <div class="mb-1"><strong>Est. Loss:</strong> ${formatCurrency(loss)}</div>
        <div><strong>Compensation:</strong> ${formatCurrency(l.compensation_amount)}</div>
    `;
}

/* ── Submit Claim ────────────────────────────────────────── */
async function submitClaim() {
    if (!aiData) { showToast('Please run AI analysis first.', 'error'); return; }

    showSpinner('Submitting claim...');
    try {
        const res = await apiPost('/api/claims', {
            user_id: user.id,
            crop_type: document.getElementById('cropType').value,
            damage_type: document.getElementById('damageType').value,
            crop_stage: document.getElementById('cropStage').value,
            damage_percentage: parseInt(document.getElementById('damagePercentage').value),
            estimated_loss: parseFloat(document.getElementById('estimatedLoss').value) || aiData.loss_estimate.estimated_loss,
            ai_result: aiData.analysis.ai_result,
            ai_score: aiData.analysis.ai_score,
            eligibility_score: aiData.eligibility.eligibility_score,
            weather_report: `${aiData.weather.event}: ${aiData.weather.description}`,
            gps_location: document.getElementById('claimGps').value,
        });
        hideSpinner();

        if (res.success) {
            // Upload images
            const imageInput = document.getElementById('imageUpload');
            if (imageInput.files.length > 0) {
                for (const file of imageInput.files) {
                    const fd = new FormData();
                    fd.append('file', file);
                    fd.append('user_id', user.id);
                    fd.append('claim_id', res.claim_id);
                    fd.append('file_type', 'image');
                    await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: fd });
                }
            }
            showToast('Claim submitted successfully!', 'success');
            setTimeout(() => { window.location.href = 'status.html'; }, 1200);
        } else {
            showToast(res.message || 'Failed to submit.', 'error');
        }
    } catch (e) { hideSpinner(); showToast('Server error.', 'error'); }
}
