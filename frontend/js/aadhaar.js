/**
 * Aadhaar & Ration Card Page Logic
 */
const user = requireAuth();

document.addEventListener('DOMContentLoaded', () => {
    if (user) {
        document.getElementById('navbar-root').innerHTML = renderNavbar(user.name || 'Farmer');
    }
    // Only allow digits in aadhaar field
    document.getElementById('aadhaarInput').addEventListener('input', function () {
        this.value = this.value.replace(/\D/g, '');
    });
});

function verifyAadhaar() {
    const aadhaar = document.getElementById('aadhaarInput').value.trim();
    const statusEl = document.getElementById('aadhaarStatus');

    if (!validateAadhaar(aadhaar)) {
        document.getElementById('aadhaarInput').classList.add('is-invalid');
        statusEl.innerHTML = '';
        showToast('Aadhaar must be exactly 12 digits.', 'error');
        document.getElementById('continueBtn').disabled = true;
        return;
    }

    document.getElementById('aadhaarInput').classList.remove('is-invalid');
    document.getElementById('aadhaarInput').classList.add('is-valid');
    statusEl.innerHTML = '<div class="verify-badge"><i class="bi bi-patch-check-fill"></i> Aadhaar Verified Successfully</div>';
    document.getElementById('continueBtn').disabled = false;
    showToast('Aadhaar verified successfully!', 'success');
}

async function saveIdentity() {
    const aadhaar = document.getElementById('aadhaarInput').value.trim();
    if (!validateAadhaar(aadhaar)) {
        showToast('Please verify your Aadhaar first.', 'error');
        return;
    }

    showSpinner('Saving identity details...');

    const data = {
        user_id: user.id,
        aadhaar_number: aadhaar,
        ration_card_type: document.getElementById('rationTypeSelect').value,
        ration_card_number: document.getElementById('rationNumberInput').value.trim(),
    };

    try {
        const res = await apiPost('/api/identity', data);
        hideSpinner();
        if (res.success) {
            showToast('Identity details saved!', 'success');
            setTimeout(() => { window.location.href = 'bank.html'; }, 800);
        } else {
            showToast(res.message || 'Failed to save.', 'error');
        }
    } catch (e) {
        hideSpinner();
        showToast('Server error.', 'error');
    }
}
