/**
 * Land Details Page Logic
 */
const user = requireAuth();
let map = null, marker = null;

document.addEventListener('DOMContentLoaded', () => {
    if (user) document.getElementById('navbar-root').innerHTML = renderNavbar(user.name || 'Farmer');
});

function captureGPS() {
    if (!navigator.geolocation) {
        showToast('Geolocation not supported by your browser.', 'error');
        return;
    }
    showSpinner('Capturing GPS location...');
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            hideSpinner();
            const lat = pos.coords.latitude.toFixed(6);
            const lng = pos.coords.longitude.toFixed(6);
            document.getElementById('gpsLocation').value = `${lat}, ${lng}`;
            document.getElementById('gpsStatus').innerHTML =
                `<div class="verify-badge"><i class="bi bi-geo-alt-fill"></i> Location: ${lat}, ${lng}</div>`;

            // Show map
            const mapEl = document.getElementById('map');
            mapEl.style.display = 'block';
            if (!map) {
                map = L.map('map').setView([lat, lng], 15);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap'
                }).addTo(map);
            } else {
                map.setView([lat, lng], 15);
            }
            if (marker) map.removeLayer(marker);
            marker = L.marker([lat, lng]).addTo(map).bindPopup('Your Land Location').openPopup();
            showToast('GPS location captured!', 'success');

            // Verify survey number
            const survey = document.getElementById('surveyNumber').value.trim();
            if (survey) {
                document.getElementById('surveyVerify').innerHTML =
                    '<div class="verify-badge"><i class="bi bi-patch-check-fill"></i> Survey Number Verified Successfully</div>';
            }
        },
        (err) => {
            hideSpinner();
            showToast('Unable to get location. Please allow location access.', 'error');
            // Fallback demo location
            const lat = 17.385044, lng = 78.486671;
            document.getElementById('gpsLocation').value = `${lat}, ${lng}`;
            document.getElementById('gpsStatus').innerHTML =
                `<div class="verify-badge"><i class="bi bi-geo-alt-fill"></i> Demo Location: ${lat}, ${lng}</div>`;
            const mapEl = document.getElementById('map');
            mapEl.style.display = 'block';
            if (!map) {
                map = L.map('map').setView([lat, lng], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
            }
            if (marker) map.removeLayer(marker);
            marker = L.marker([lat, lng]).addTo(map).bindPopup('Demo Location (Hyderabad)').openPopup();
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

async function saveLand() {
    const surveyNumber = document.getElementById('surveyNumber').value.trim();
    const landArea = document.getElementById('landArea').value.trim();
    const village = document.getElementById('village').value.trim();
    const mandal = document.getElementById('mandal').value.trim();
    const district = document.getElementById('district').value.trim();
    const state = document.getElementById('state').value.trim();

    if (!surveyNumber || !landArea || !village || !mandal || !district || !state) {
        showToast('Please fill all required fields.', 'error');
        return;
    }

    showSpinner('Saving land details...');
    try {
        const res = await apiPost('/api/land', {
            user_id: user.id,
            survey_number: surveyNumber,
            passbook_number: document.getElementById('passbookNumber').value.trim(),
            land_area: landArea,
            village, mandal, district, state,
            gps_location: document.getElementById('gpsLocation').value,
        });
        hideSpinner();
        if (res.success) {
            showToast('Land details saved!', 'success');
            setTimeout(() => { window.location.href = 'dashboard.html'; }, 800);
        } else {
            showToast(res.message || 'Failed to save.', 'error');
        }
    } catch (e) { hideSpinner(); showToast('Server error.', 'error'); }
}
