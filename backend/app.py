"""
AI-Based Crop Damage Assessment & Compensation System
=====================================================
Flask Backend — REST API Server
"""

import os
import uuid
import json
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import simulated ML module
from ml_model import (
    analyze_crop_damage,
    calculate_eligibility_score,
    generate_weather_report,
    estimate_loss,
)

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'crop-ai-dev-secret')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# Supabase client (lazy init — gracefully degrade if not configured)
# ---------------------------------------------------------------------------
supabase = None

def get_supabase():
    global supabase
    if supabase is not None:
        return supabase
    url = os.getenv('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_SERVICE_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '')
    if url and key and not url.startswith('your_'):
        try:
            from supabase import create_client
            supabase = create_client(url, key)
            print("[OK] Supabase connected successfully")
        except Exception as e:
            print(f"[WARN] Supabase connection failed: {e}")
            supabase = None
    else:
        print("[INFO] Supabase not configured -- running in demo mode (in-memory storage)")
    return supabase

# ---------------------------------------------------------------------------
# In‑memory fallback storage (used when Supabase is not configured)
# ---------------------------------------------------------------------------
demo_store = {
    "users": {},
    "identity_details": {},
    "bank_details": {},
    "land_details": {},
    "claims": {},
    "uploads": {},
    "otp_sessions": {},
}

# Default officer account
OFFICER_CREDENTIALS = {"username": "officer", "password": "officer123"}
FIXED_OTP = "123456"


# ═══════════════════════════════════════════════════════════════════════════
#  SERVE FRONTEND
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ═══════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    """Simulate sending OTP to a phone number."""
    data = request.get_json() or {}
    phone = data.get('phone', '').strip()

    if not phone or len(phone) != 10 or not phone.isdigit():
        return jsonify({"success": False, "message": "Invalid phone number. Must be 10 digits."}), 400

    # Store OTP session
    demo_store["otp_sessions"][phone] = FIXED_OTP
    return jsonify({"success": True, "message": f"OTP sent to +91{phone} successfully."})


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and create / fetch user."""
    data = request.get_json() or {}
    phone = data.get('phone', '').strip()
    otp = data.get('otp', '').strip()

    if otp != FIXED_OTP:
        return jsonify({"success": False, "message": "Invalid OTP. Please try again."}), 401

    sb = get_supabase()
    user_id = None

    if sb:
        try:
            # Check if user exists
            res = sb.table('users').select('*').eq('phone', phone).execute()
            if res.data and len(res.data) > 0:
                user_id = res.data[0]['id']
                user_data = res.data[0]
            else:
                # Create new user
                user_id = str(uuid.uuid4())
                new_user = {"id": user_id, "phone": phone, "name": f"Farmer_{phone[-4:]}"}
                sb.table('users').insert(new_user).execute()
                user_data = new_user
        except Exception as e:
            print(f"Supabase error: {e}")
            user_id = None

    # Fallback to in‑memory
    if user_id is None:
        if phone in demo_store["users"]:
            user_data = demo_store["users"][phone]
            user_id = user_data["id"]
        else:
            user_id = str(uuid.uuid4())
            user_data = {"id": user_id, "phone": phone, "name": f"Farmer_{phone[-4:]}"}
            demo_store["users"][phone] = user_data

    return jsonify({
        "success": True,
        "message": "OTP verified successfully.",
        "user": user_data,
    })


# ═══════════════════════════════════════════════════════════════════════════
#  OFFICER LOGIN
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/officer/login', methods=['POST'])
def officer_login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    if username == OFFICER_CREDENTIALS["username"] and password == OFFICER_CREDENTIALS["password"]:
        return jsonify({
            "success": True,
            "message": "Officer login successful.",
            "officer": {
                "id": "officer-001",
                "username": username,
                "name": "District Agriculture Officer",
                "designation": "Senior Agriculture Officer",
            },
        })
    return jsonify({"success": False, "message": "Invalid credentials."}), 401


# ═══════════════════════════════════════════════════════════════════════════
#  IDENTITY DETAILS (Aadhaar & Ration Card)
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/identity', methods=['POST'])
def save_identity():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    aadhaar = data.get('aadhaar_number', '').strip()

    if not aadhaar or len(aadhaar) != 12 or not aadhaar.isdigit():
        return jsonify({"success": False, "message": "Aadhaar must be 12 digits."}), 400

    record = {
        "user_id": user_id,
        "aadhaar_number": aadhaar,
        "ration_card_type": data.get('ration_card_type', ''),
        "ration_card_number": data.get('ration_card_number', ''),
        "verified": True,
    }

    sb = get_supabase()
    if sb:
        try:
            existing = sb.table('identity_details').select('*').eq('user_id', user_id).execute()
            if existing.data and len(existing.data) > 0:
                sb.table('identity_details').update(record).eq('user_id', user_id).execute()
            else:
                record['id'] = str(uuid.uuid4())
                sb.table('identity_details').insert(record).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

    demo_store["identity_details"][user_id] = record
    return jsonify({"success": True, "message": "Identity details saved successfully.", "data": record})


@app.route('/api/identity/<user_id>', methods=['GET'])
def get_identity(user_id):
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('identity_details').select('*').eq('user_id', user_id).execute()
            if res.data and len(res.data) > 0:
                return jsonify({"success": True, "data": res.data[0]})
        except Exception as e:
            print(f"Supabase error: {e}")

    data = demo_store["identity_details"].get(user_id)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "No identity details found."}), 404


# ═══════════════════════════════════════════════════════════════════════════
#  BANK DETAILS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/bank', methods=['POST'])
def save_bank():
    data = request.get_json() or {}
    user_id = data.get('user_id')

    record = {
        "user_id": user_id,
        "account_holder_name": data.get('account_holder_name', ''),
        "bank_name": data.get('bank_name', ''),
        "account_number": data.get('account_number', ''),
        "ifsc_code": data.get('ifsc_code', '').upper(),
        "branch_name": data.get('branch_name', ''),
        "verified": True,
    }

    sb = get_supabase()
    if sb:
        try:
            existing = sb.table('bank_details').select('*').eq('user_id', user_id).execute()
            if existing.data and len(existing.data) > 0:
                sb.table('bank_details').update(record).eq('user_id', user_id).execute()
            else:
                record['id'] = str(uuid.uuid4())
                sb.table('bank_details').insert(record).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

    demo_store["bank_details"][user_id] = record
    return jsonify({"success": True, "message": "Bank details saved successfully.", "data": record})


@app.route('/api/bank/<user_id>', methods=['GET'])
def get_bank(user_id):
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('bank_details').select('*').eq('user_id', user_id).execute()
            if res.data and len(res.data) > 0:
                return jsonify({"success": True, "data": res.data[0]})
        except Exception as e:
            print(f"Supabase error: {e}")

    data = demo_store["bank_details"].get(user_id)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "No bank details found."}), 404


# ═══════════════════════════════════════════════════════════════════════════
#  LAND DETAILS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/land', methods=['POST'])
def save_land():
    data = request.get_json() or {}
    user_id = data.get('user_id')

    record = {
        "user_id": user_id,
        "survey_number": data.get('survey_number', ''),
        "passbook_number": data.get('passbook_number', ''),
        "land_area": data.get('land_area', ''),
        "village": data.get('village', ''),
        "mandal": data.get('mandal', ''),
        "district": data.get('district', ''),
        "state": data.get('state', ''),
        "gps_location": data.get('gps_location', ''),
        "verified": True,
    }

    sb = get_supabase()
    if sb:
        try:
            existing = sb.table('land_details').select('*').eq('user_id', user_id).execute()
            if existing.data and len(existing.data) > 0:
                sb.table('land_details').update(record).eq('user_id', user_id).execute()
            else:
                record['id'] = str(uuid.uuid4())
                sb.table('land_details').insert(record).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

    demo_store["land_details"][user_id] = record
    return jsonify({"success": True, "message": "Land details saved successfully.", "data": record})


@app.route('/api/land/<user_id>', methods=['GET'])
def get_land(user_id):
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('land_details').select('*').eq('user_id', user_id).execute()
            if res.data and len(res.data) > 0:
                return jsonify({"success": True, "data": res.data[0]})
        except Exception as e:
            print(f"Supabase error: {e}")

    data = demo_store["land_details"].get(user_id)
    if data:
        return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "message": "No land details found."}), 404


# ═══════════════════════════════════════════════════════════════════════════
#  CLAIMS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/claims', methods=['POST'])
def submit_claim():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    claim_id = str(uuid.uuid4())

    record = {
        "claim_id": claim_id,
        "user_id": user_id,
        "crop_type": data.get('crop_type', ''),
        "damage_type": data.get('damage_type', ''),
        "crop_stage": data.get('crop_stage', ''),
        "damage_percentage": int(data.get('damage_percentage', 0)),
        "estimated_loss": float(data.get('estimated_loss', 0)),
        "ai_result": data.get('ai_result', ''),
        "ai_score": int(data.get('ai_score', 0)),
        "eligibility_score": int(data.get('eligibility_score', 0)),
        "weather_report": data.get('weather_report', ''),
        "claim_status": "pending",
        "gps_location": data.get('gps_location', ''),
        "submitted_at": datetime.utcnow().isoformat(),
    }

    sb = get_supabase()
    if sb:
        try:
            sb.table('claims').insert(record).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

    demo_store["claims"][claim_id] = record
    return jsonify({"success": True, "message": "Claim submitted successfully.", "claim_id": claim_id, "data": record})


@app.route('/api/claims', methods=['GET'])
def get_all_claims():
    """Get all claims (officer endpoint)."""
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('claims').select('*').order('submitted_at', desc=True).execute()
            if res.data:
                return jsonify({"success": True, "data": res.data})
        except Exception as e:
            print(f"Supabase error: {e}")

    claims = list(demo_store["claims"].values())
    claims.sort(key=lambda c: c.get('submitted_at', ''), reverse=True)
    return jsonify({"success": True, "data": claims})


@app.route('/api/claims/user/<user_id>', methods=['GET'])
def get_user_claims(user_id):
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('claims').select('*').eq('user_id', user_id).order('submitted_at', desc=True).execute()
            if res.data:
                return jsonify({"success": True, "data": res.data})
        except Exception as e:
            print(f"Supabase error: {e}")

    claims = [c for c in demo_store["claims"].values() if c.get('user_id') == user_id]
    claims.sort(key=lambda c: c.get('submitted_at', ''), reverse=True)
    return jsonify({"success": True, "data": claims})


@app.route('/api/claims/<claim_id>', methods=['GET'])
def get_claim_detail(claim_id):
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('claims').select('*').eq('claim_id', claim_id).execute()
            if res.data and len(res.data) > 0:
                claim = res.data[0]
                # Fetch related user info
                user_id = claim.get('user_id')
                user_res = sb.table('users').select('*').eq('id', user_id).execute()
                identity_res = sb.table('identity_details').select('*').eq('user_id', user_id).execute()
                bank_res = sb.table('bank_details').select('*').eq('user_id', user_id).execute()
                land_res = sb.table('land_details').select('*').eq('user_id', user_id).execute()
                uploads_res = sb.table('uploads').select('*').eq('claim_id', claim_id).execute()

                return jsonify({
                    "success": True,
                    "data": {
                        "claim": claim,
                        "user": user_res.data[0] if user_res.data else {},
                        "identity": identity_res.data[0] if identity_res.data else {},
                        "bank": bank_res.data[0] if bank_res.data else {},
                        "land": land_res.data[0] if land_res.data else {},
                        "uploads": uploads_res.data if uploads_res.data else [],
                    },
                })
        except Exception as e:
            print(f"Supabase error: {e}")

    claim = demo_store["claims"].get(claim_id)
    if claim:
        user_id = claim.get('user_id')
        return jsonify({
            "success": True,
            "data": {
                "claim": claim,
                "user": demo_store["users"].get(user_id, next((u for u in demo_store["users"].values() if u.get('id') == user_id), {})),
                "identity": demo_store["identity_details"].get(user_id, {}),
                "bank": demo_store["bank_details"].get(user_id, {}),
                "land": demo_store["land_details"].get(user_id, {}),
                "uploads": [u for u in demo_store["uploads"].values() if u.get('claim_id') == claim_id] if demo_store["uploads"] else [],
            },
        })
    return jsonify({"success": False, "message": "Claim not found."}), 404


@app.route('/api/claims/<claim_id>/status', methods=['PUT'])
def update_claim_status(claim_id):
    data = request.get_json() or {}
    new_status = data.get('status', 'pending')
    remarks = data.get('remarks', '')

    sb = get_supabase()
    if sb:
        try:
            sb.table('claims').update({
                "claim_status": new_status,
                "officer_remarks": remarks,
                "reviewed_at": datetime.utcnow().isoformat(),
            }).eq('claim_id', claim_id).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

    if claim_id in demo_store["claims"]:
        demo_store["claims"][claim_id]["claim_status"] = new_status
        demo_store["claims"][claim_id]["officer_remarks"] = remarks
        demo_store["claims"][claim_id]["reviewed_at"] = datetime.utcnow().isoformat()

    return jsonify({"success": True, "message": f"Claim status updated to '{new_status}'."})


# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD STATISTICS
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/dashboard/<user_id>', methods=['GET'])
def dashboard_stats(user_id):
    claims = []
    sb = get_supabase()
    if sb:
        try:
            res = sb.table('claims').select('*').eq('user_id', user_id).execute()
            claims = res.data if res.data else []
        except Exception:
            pass

    if not claims:
        claims = [c for c in demo_store["claims"].values() if c.get('user_id') == user_id]

    total = len(claims)
    pending = sum(1 for c in claims if c.get('claim_status') == 'pending')
    approved = sum(1 for c in claims if c.get('claim_status') == 'approved')
    rejected = sum(1 for c in claims if c.get('claim_status') == 'rejected')

    return jsonify({
        "success": True,
        "data": {
            "total_claims": total,
            "pending_claims": pending,
            "approved_claims": approved,
            "rejected_claims": rejected,
        },
    })


# ═══════════════════════════════════════════════════════════════════════════
#  AI ANALYSIS ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/analyze', methods=['POST'])
def ai_analyze():
    data = request.get_json() or {}
    crop_type = data.get('crop_type', 'Rice')
    damage_type = data.get('damage_type', 'Flood')
    damage_percentage = int(data.get('damage_percentage', 50))
    crop_stage = data.get('crop_stage', 'Growing stage')
    district = data.get('district', '')
    land_area = float(data.get('land_area', 1.0))

    # Run simulated analysis
    analysis = analyze_crop_damage(crop_type, damage_type, damage_percentage)
    eligibility = calculate_eligibility_score(damage_percentage, crop_stage)
    weather = generate_weather_report(district if district else None)
    loss = estimate_loss(crop_type, damage_percentage, land_area)

    return jsonify({
        "success": True,
        "data": {
            "analysis": analysis,
            "eligibility": eligibility,
            "weather": weather,
            "loss_estimate": loss,
        },
    })


# ═══════════════════════════════════════════════════════════════════════════
#  FILE UPLOAD
# ═══════════════════════════════════════════════════════════════════════════

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file provided."}), 400

    file = request.files['file']
    user_id = request.form.get('user_id', 'unknown')
    claim_id = request.form.get('claim_id', 'unknown')
    file_type = request.form.get('file_type', 'image')

    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected."}), 400

    # Save locally
    ext = os.path.splitext(file.filename)[1]
    safe_name = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(filepath)

    file_url = f"/uploads/{safe_name}"

    upload_record = {
        "id": str(uuid.uuid4()),
        "claim_id": claim_id,
        "user_id": user_id,
        "file_url": file_url,
        "file_type": file_type,
        "original_name": file.filename,
        "uploaded_at": datetime.utcnow().isoformat(),
    }

    sb = get_supabase()
    if sb:
        try:
            sb.table('uploads').insert(upload_record).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

    demo_store["uploads"][upload_record["id"]] = upload_record

    return jsonify({"success": True, "message": "File uploaded successfully.", "data": upload_record})


@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    print(f"\n[SERVER] Crop Damage Assessment Server starting on http://localhost:{port}")
    print(f"[STATIC] Serving frontend from: {os.path.abspath(app.static_folder)}")
    print(f"[UPLOAD] Uploads directory: {os.path.abspath(UPLOAD_FOLDER)}\n")
    get_supabase()  # Attempt connection on startup
    app.run(host='0.0.0.0', port=port, debug=debug)
