# 🌾 AI-Based Crop Damage Assessment & Compensation System

A professional, responsive web application designed for farmers to claim crop insurance using AI-based crop damage analysis. Government agriculture officers can review, verify, and approve/reject claims through a dedicated dashboard.

---

## ✨ Features

- **Farmer Portal** — Phone + OTP login, identity verification, bank details, land registration
- **AI Crop Analysis** — Simulated AI engine for damage detection, severity assessment, and eligibility scoring
- **Insurance Claims** — Multi-section claim form with image/video uploads and GPS verification
- **Officer Dashboard** — Review claims, view AI analysis, approve/reject/request re-inspection
- **Claim Tracking** — Timeline-based progress tracker for submitted claims
- **GPS & Maps** — Leaflet.js with OpenStreetMap for location verification
- **Weather Reports** — Simulated weather/calamity data for claim validation
- **Responsive Design** — Mobile-friendly UI with modern animations
- **Supabase Integration** — PostgreSQL database, authentication, and file storage

---

## 🛠 Technologies Used

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Backend | Python Flask |
| Database | Supabase (PostgreSQL) |
| Maps | Leaflet.js + OpenStreetMap |
| AI/ML | Simulated module (ready for TensorFlow/OpenCV) |
| Icons | Bootstrap Icons |
| Fonts | Google Fonts (Inter) |

---

## 📁 Project Structure

```
CROP_AI/
├── frontend/
│   ├── index.html              # Landing page
│   ├── login.html              # Farmer login (OTP)
│   ├── aadhaar.html            # Aadhaar verification
│   ├── bank.html               # Bank details
│   ├── land.html               # Land registration + GPS
│   ├── dashboard.html          # Farmer dashboard
│   ├── claim.html              # Submit insurance claim
│   ├── status.html             # Claim status tracker
│   ├── officer-login.html      # Officer login
│   ├── officer.html            # Officer dashboard
│   ├── officer-detail.html     # Claim review detail
│   ├── css/style.css           # Master stylesheet
│   ├── js/                     # Page-specific JavaScript
│   └── assets/                 # Images and media
├── backend/
│   ├── app.py                  # Flask API server
│   ├── ml_model.py             # Simulated AI module
│   └── requirements.txt        # Python dependencies
├── database/
│   └── schema.sql              # Supabase table schema
├── uploads/                    # Uploaded files
├── .env                        # Environment variables
├── setup.bat                   # Windows setup script
├── setup.sh                    # Linux/Mac setup script
└── README.md                   # This file
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8 or higher
- A Supabase account (free tier works) — [supabase.com](https://supabase.com)

### Quick Start (Windows)

```bash
# Double-click setup.bat or run:
setup.bat
```

### Quick Start (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

```bash
# 1. Create virtual environment
cd backend
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python app.py
```

### Environment Configuration

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run the SQL from `database/schema.sql` in the Supabase SQL Editor
3. Update `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

> **Note:** The application works in demo mode without Supabase configuration, using in-memory storage.

---

## 🖥 Running the Application

After setup, the application runs at:

```
http://localhost:5000
```

### Demo Credentials

| Role | Credential | Value |
|------|-----------|-------|
| Farmer | Phone | Any 10-digit number |
| Farmer | OTP | `123456` |
| Officer | Username | `officer` |
| Officer | Password | `officer123` |

---

## 📱 Pages Overview

1. **Login** — Phone number + OTP authentication
2. **Aadhaar** — Identity verification (12-digit Aadhaar + ration card)
3. **Bank Details** — Bank account with IFSC auto-detection
4. **Land Details** — Survey number, GPS location, map view
5. **Dashboard** — Statistics cards, quick actions, recent claims
6. **Submit Claim** — Crop details, uploads, GPS, AI analysis, eligibility
7. **Claim Status** — Timeline tracker with progress visualization
8. **Officer Dashboard** — Claims table with filters and status management
9. **Officer Detail** — Full claim review with approve/reject actions

---

## 🔮 Future Enhancements

- [ ] Real TensorFlow/OpenCV crop damage detection model
- [ ] SMS OTP via Twilio or Firebase
- [ ] Multi-language support (Hindi, Telugu, etc.)
- [ ] Payment gateway for compensation disbursement
- [ ] Satellite imagery integration
- [ ] Mobile app (React Native / Flutter)
- [ ] Blockchain-based claim verification
- [ ] Advanced analytics and reporting dashboard
- [ ] Email notifications for claim updates
- [ ] Role-based access control with multiple officer levels

---

## 📜 License

This project is built for educational and demonstration purposes.

---

<p align="center">Built with ❤️ for Indian Agriculture</p>
