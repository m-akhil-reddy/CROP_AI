/**
 * Bank Details Page Logic
 */
const user = requireAuth();
document.addEventListener('DOMContentLoaded', () => {
    if (user) document.getElementById('navbar-root').innerHTML = renderNavbar(user.name || 'Farmer');
    document.getElementById('ifscCode').addEventListener('input', function () { this.value = this.value.toUpperCase(); });
});

function detectBank() {
    const ifsc = document.getElementById('ifscCode').value.trim();
    const bank = detectBankFromIFSC(ifsc);
    const el = document.getElementById('bankDetected');
    if (bank) {
        el.innerHTML = `<span class="verify-badge"><i class="bi bi-bank"></i> ${bank}</span>`;
        document.getElementById('bankName').value = bank;
        showToast(`Bank detected: ${bank}`, 'success');
    } else {
        el.innerHTML = '<small class="text-muted">Enter IFSC to auto-detect bank</small>';
    }
}

async function saveBank() {
    const holderName = document.getElementById('holderName').value.trim();
    const bankName = document.getElementById('bankName').value.trim();
    const accountNumber = document.getElementById('accountNumber').value.trim();
    const confirmAccount = document.getElementById('confirmAccount').value.trim();
    const ifscCode = document.getElementById('ifscCode').value.trim().toUpperCase();
    const branchName = document.getElementById('branchName').value.trim();

    if (!holderName || !bankName || !accountNumber || !ifscCode) {
        showToast('Please fill all required fields.', 'error');
        return;
    }
    if (accountNumber !== confirmAccount) {
        document.getElementById('confirmAccount').classList.add('is-invalid');
        showToast('Account numbers do not match.', 'error');
        return;
    }
    document.getElementById('confirmAccount').classList.remove('is-invalid');

    showSpinner('Saving bank details...');
    try {
        const res = await apiPost('/api/bank', {
            user_id: user.id, account_holder_name: holderName, bank_name: bankName,
            account_number: accountNumber, ifsc_code: ifscCode, branch_name: branchName,
        });
        hideSpinner();
        if (res.success) {
            showToast('Bank details saved!', 'success');
            setTimeout(() => { window.location.href = 'land.html'; }, 800);
        } else {
            showToast(res.message || 'Failed to save.', 'error');
        }
    } catch (e) { hideSpinner(); showToast('Server error.', 'error'); }
}
