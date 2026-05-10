/**
 * Supabase Client Configuration
 * Replace with your Supabase project credentials
 */
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// API base URL (Flask backend)
const API_BASE = window.location.origin;

// Initialize Supabase client (only if configured)
let supabaseClient = null;
if (typeof supabase !== 'undefined' && !SUPABASE_URL.startsWith('YOUR_')) {
    supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    console.log('✅ Supabase client initialized');
} else {
    console.log('ℹ️ Running in demo mode (Supabase not configured)');
}
