-- ============================================================
-- AI-Based Crop Damage Assessment & Compensation System
-- Supabase PostgreSQL Schema
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 2. IDENTITY DETAILS TABLE (Aadhaar & Ration Card)
-- ============================================================
CREATE TABLE IF NOT EXISTS identity_details (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    aadhaar_number VARCHAR(12) NOT NULL,
    ration_card_type VARCHAR(50),
    ration_card_number VARCHAR(50),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- 3. BANK DETAILS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS bank_details (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    account_holder_name VARCHAR(100) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    ifsc_code VARCHAR(11) NOT NULL,
    branch_name VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- 4. LAND DETAILS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS land_details (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    survey_number VARCHAR(50) NOT NULL,
    passbook_number VARCHAR(50),
    land_area VARCHAR(50) NOT NULL,
    village VARCHAR(100),
    mandal VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100),
    gps_location VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- 5. CLAIMS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS claims (
    claim_id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    crop_type VARCHAR(50) NOT NULL,
    damage_type VARCHAR(50) NOT NULL,
    crop_stage VARCHAR(50),
    damage_percentage INTEGER DEFAULT 0,
    estimated_loss DECIMAL(12, 2) DEFAULT 0,
    ai_result TEXT,
    ai_score INTEGER DEFAULT 0,
    eligibility_score INTEGER DEFAULT 0,
    weather_report TEXT,
    claim_status VARCHAR(20) DEFAULT 'pending',
    officer_remarks TEXT,
    gps_location VARCHAR(100),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 6. UPLOADS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS uploads (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    claim_id UUID REFERENCES claims(claim_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    file_type VARCHAR(20) DEFAULT 'image',
    original_name VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- 7. OFFICERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS officers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    designation VARCHAR(100) DEFAULT 'Agriculture Officer',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- Insert default officer account
-- Password: officer123 (stored as plain text for demo; hash in production)
-- ============================================================
INSERT INTO officers (username, password_hash, name, designation)
VALUES ('officer', 'officer123', 'District Agriculture Officer', 'Senior Agriculture Officer')
ON CONFLICT (username) DO NOTHING;

-- ============================================================
-- Row Level Security Policies (Optional - enable as needed)
-- ============================================================
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE identity_details ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE bank_details ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE land_details ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_claims_user_id ON claims(user_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(claim_status);
CREATE INDEX IF NOT EXISTS idx_uploads_claim_id ON uploads(claim_id);
CREATE INDEX IF NOT EXISTS idx_identity_user_id ON identity_details(user_id);
CREATE INDEX IF NOT EXISTS idx_bank_user_id ON bank_details(user_id);
CREATE INDEX IF NOT EXISTS idx_land_user_id ON land_details(user_id);
