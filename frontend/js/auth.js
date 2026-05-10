/**
 * Authentication Logic — Login & OTP
 */

// Redirect if already logged in
(function () {
    const user = getSession();
    if (user) window.location.href = 'dashboard.html';
})();

async function sendOTP() {
    const phone = document.getElementById('phoneInput').value.trim();

    if (!validatePhone(phone)) {
        document.getElementById('phoneInput').classList.add('is-invalid');
        showToast('Please enter a valid 10-digit mobile number.', 'error');
        return;
    }

    document.getElementById('phoneInput').classList.remove('is-invalid');
    showSpinner('Sending OTP...');

    try {
        const res = await apiPost('/api/auth/send-otp', { phone });
        hideSpinner();

        if (res.success) {
            document.getElementById('otpPhone').textContent = `+91 ${phone}`;
            document.getElementById('phoneSection').style.display = 'none';
            document.getElementById('otpSection').classList.add('show');
            showToast('OTP sent successfully!', 'success');
            document.getElementById('otpInput').focus();
        } else {
            showToast(res.message || 'Failed to send OTP.', 'error');
        }
    } catch (e) {
        hideSpinner();
        showToast('Server error. Please try again.', 'error');
    }
}

async function verifyOTP() {
    const phone = document.getElementById('phoneInput').value.trim();
    const otp = document.getElementById('otpInput').value.trim();

    if (otp.length !== 6) {
        document.getElementById('otpInput').classList.add('is-invalid');
        showToast('Please enter the 6-digit OTP.', 'error');
        return;
    }

    document.getElementById('otpInput').classList.remove('is-invalid');
    showSpinner('Verifying OTP...');

    try {
        const res = await apiPost('/api/auth/verify-otp', { phone, otp });
        hideSpinner();

        if (res.success) {
            saveSession(res.user);
            showToast('Login successful! Welcome.', 'success');
            setTimeout(() => { window.location.href = 'aadhaar.html'; }, 800);
        } else {
            document.getElementById('otpInput').classList.add('is-invalid');
            showToast(res.message || 'Invalid OTP.', 'error');
        }
    } catch (e) {
        hideSpinner();
        showToast('Server error. Please try again.', 'error');
    }
}

function resetLogin() {
    document.getElementById('otpSection').classList.remove('show');
    document.getElementById('phoneSection').style.display = 'block';
    document.getElementById('otpInput').value = '';
    document.getElementById('otpInput').classList.remove('is-invalid');
}

// Enter key support
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('phoneInput')?.addEventListener('keypress', e => { if (e.key === 'Enter') sendOTP(); });
    document.getElementById('otpInput')?.addEventListener('keypress', e => { if (e.key === 'Enter') verifyOTP(); });
});
