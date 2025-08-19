# user_data.py - Case-insensitive username handling (lowercase-only) - FIXED VERSION
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import streamlit as st
from supabase import create_client

# Initialize Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_KEY = st.secrets.get("ADMIN_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---- Core Functions ----
def _now_iso() -> str:
    """Get current UTC timestamp"""
    return datetime.utcnow().isoformat()

def hash_password(password: str) -> str:
    """Secure password hashing"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def normalize_username(username: str) -> str:
    """Convert username to lowercase and strip whitespace"""
    return username.strip().lower()

# ---- Authentication ----
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Register new user (auto-lowercase)"""
    normalized = normalize_username(username)
    if not normalized or not password:
        return False, "Username and password required"
    
    try:
        # Check for existing username (case-insensitive)
        existing = supabase.table("users") \
                         .select("username") \
                         .eq("username", normalized) \
                         .execute()
        
        if existing.data:
            return False, "Username already exists"
            
        # Insert new user
        supabase.table("users").insert({
            "username": normalized,
            "password": hash_password(password),
            "created_at": _now_iso()
        }).execute()
        
        return True, "Registration successful"
    except Exception as e:
        return False, f"Registration failed: {str(e)}"

def authenticate(username: str, password: str) -> Tuple[bool, str]:
    """Login with case-insensitive username"""
    normalized = normalize_username(username)
    try:
        # Find user
        user = supabase.table("users") \
                     .select("*") \
                     .eq("username", normalized) \
                     .execute()
        
        if not user.data:
            return False, "User not found"
            
        # Verify password
        if user.data[0]["password"] == hash_password(password):
            return True, "Login successful"
        return False, "Incorrect password"
    except Exception as e:
        return False, f"Login error: {str(e)}"

# ---- User Management ----
def admin_reset_password(target_username: str, new_password: str) -> Tuple[bool, str]:
    """Admin password reset (case-insensitive)"""
    normalized = normalize_username(target_username)
    try:
        supabase.table("users") \
              .update({"password": hash_password(new_password)}) \
              .eq("username", normalized) \
              .execute()
        return True, "Password updated"
    except Exception as e:
        return False, f"Reset failed: {str(e)}"

def delete_account(username: str) -> Tuple[bool, str]:
    """Delete account (case-insensitive)"""
    normalized = normalize_username(username)
    try:
        # Delete user data first
        tables = ["notes", "flashcards", "study_sessions", "events"]
        for table in tables:
            supabase.table(table) \
                  .delete() \
                  .eq("username", normalized) \
                  .execute()
        
        # Delete user
        supabase.table("users") \
              .delete() \
              .eq("username", normalized) \
              .execute()
        
        return True, "Account deleted"
    except Exception as e:
        return False, f"Deletion failed: {str(e)}"

# ---- Data Handling ----
def save_current_user(session_state: dict) -> Tuple[bool, str]:
    """Save all user data using lowercase username"""
    if not session_state.get("logged_in"):
        return False, "Not logged in"
    
    normalized = normalize_username(session_state["username"])
    
    try:
        # ----- NOTES -----
        supabase.table("notes").delete().eq("username", normalized).execute()
        notes_to_insert = []
        for n in session_state.get("notes", []):
            notes_to_insert.append({
                "username": normalized,
                "title": n.get("title"),
                "content": n.get("content"),
                "category": n.get("category", "General"),
                "created_at": n.get("timestamp") or _now_iso(),
                "updated_at": n.get("timestamp") or _now_iso()
            })
        if notes_to_insert:
            supabase.table("notes").insert(notes_to_insert).execute()

        # ----- FLASHCARDS -----
        supabase.table("flashcards").delete().eq("username", normalized).execute()
        fcs = []
        for c in session_state.get("flashcards", []):
            fcs.append({
                "username": normalized,
                "front": c.get("front"),
                "back": c.get("back"),
                "category": c.get("category", "General"),
                "created_at": c.get("created") or _now_iso()
            })
        if fcs:
            supabase.table("flashcards").insert(fcs).execute()

        # ----- STUDY SESSIONS -----
        supabase.table("study_sessions").delete().eq("username", normalized).execute()
        ss = []
        for s in session_state.get("study_sessions", []):
            ss.append({
                "username": normalized,
                "timestamp": s.get("timestamp") or _now_iso(),
                "activity_type": s.get("activity_type"),
                "data": s
            })
        if ss:
            supabase.table("study_sessions").insert(ss).execute()

        # ----- EVENTS (CALENDAR) - THE MISSING PART -----
        supabase.table("events").delete().eq("username", normalized).execute()
        events = []
        for e in session_state.get("events", []):
            events.append({
                "username": normalized,
                "name": e.get("name"),      # Check if your app uses 'name' or 'title'
                "date": e.get("date"),       # Check if your app uses 'date' or 'start'/'end'
                "notes": e.get("notes"),
                "color": e.get("color"),
                "created_at": e.get("created") or _now_iso()
            })
        if events:
            supabase.table("events").insert(events).execute()

        return True, "Data saved successfully"
    except Exception as e:
        return False, f"Save error: {str(e)}"

def load_user_data(username: str, merge_local: bool = False, 
                 local_state: Optional[dict] = None) -> Tuple[bool, dict]:
    """Load user data with case-insensitive lookup"""
    normalized = normalize_username(username)
    try:
        # ----- NOTES -----
        r = supabase.table("notes").select("*").eq("username", normalized).execute()
        notes = []
        if r.data:
            for row in r.data:
                notes.append({
                    "title": row.get("title"),
                    "content": row.get("content"),
                    "category": row.get("category"),
                    "timestamp": row.get("created_at")
                })

        # ----- FLASHCARDS -----
        r = supabase.table("flashcards").select("*").eq("username", normalized).execute()
        flashcards = []
        if r.data:
            for row in r.data:
                flashcards.append({
                    "front": row.get("front"),
                    "back": row.get("back"),
                    "category": row.get("category"),
                    "created": row.get("created_at")
                })

        # ----- STUDY SESSIONS -----
        r = supabase.table("study_sessions").select("*").eq("username", normalized).execute()
        study_sessions = []
        if r.data:
            for row in r.data:
                study_sessions.append(row.get("data") or {"timestamp": row.get("timestamp"), "activity_type": row.get("activity_type")})

        # ----- EVENTS (CALENDAR) - THE MISSING PART -----
        r = supabase.table("events").select("*").eq("username", normalized).execute()
        events = []
        if r.data:
            for row in r.data:
                events.append({
                    "name": row.get("name"),      # Check if your app uses 'name' or 'title'
                    "date": row.get("date"),       # Check if your app uses 'date' or 'start'/'end'
                    "notes": row.get("notes"),
                    "color": row.get("color"),
                    "created": row.get("created_at")
                })

        payload = {
            "notes": notes,
            "flashcards": flashcards,
            "study_sessions": study_sessions,
            "events": events  # <-- NOW INCLUDES EVENTS!
        }

        if merge_local and local_state:
            merged = {
                "notes": local_state.get("notes", []) + payload["notes"],
                "flashcards": local_state.get("flashcards", []) + payload["flashcards"],
                "study_sessions": local_state.get("study_sessions", []) + payload["study_sessions"],
                "events": local_state.get("events", []) + payload["events"] # <-- NOW MERGES EVENTS!
            }
            return True, merged
            
        return True, payload
    except Exception as e:
        return False, {"error": str(e)}
