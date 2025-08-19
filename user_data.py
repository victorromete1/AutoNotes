# user_data.py - Case-insensitive usernames (stores lowercase)
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import streamlit as st
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
ADMIN_KEY = st.secrets.get("ADMIN_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Utilities ----------
def _now_iso():
    return datetime.utcnow().isoformat()

def hash_password(password: str) -> str:
    """Simple sha256 hashing"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def normalize_username(username: str) -> str:
    """Convert username to lowercase for storage and comparison"""
    return username.strip().lower()

# ---------- Auth / user management ----------
def register_user(username: str, password: str) -> Tuple[bool, str]:
    """Create a user row with lowercase username"""
    if not username or not password:
        return False, "Username & password required"
    
    normalized = normalize_username(username)
    
    try:
        # Check if username exists (case-insensitive)
        q = supabase.table("users").select("username").eq("username", normalized).execute()
        if q.data and len(q.data) > 0:
            return False, "Username already exists"
            
        hashed = hash_password(password)
        supabase.table("users").insert({
            "username": normalized,  # Store lowercase version
            "original_username": username.strip(),  # Store original for display
            "password": hashed,
            "created_at": _now_iso()
        }).execute()
        return True, "User created"
    except Exception as e:
        return False, f"Register error: {e}"

def authenticate(username: str, password: str) -> Tuple[bool, str, Optional[str]]:
    """Login with case-insensitive username, returns (success, message, original_username)"""
    normalized = normalize_username(username)
    hashed = hash_password(password)
    
    try:
        r = supabase.table("users").select("*").eq("username", normalized).execute()
        if not r.data or len(r.data) == 0:
            return False, "Invalid username/password", None
            
        user = r.data[0]
        if user["password"] == hashed:
            # Return the original username casing for display
            original_username = user.get("original_username", normalized)
            return True, "Authenticated", original_username
        return False, "Invalid username/password", None
    except Exception as e:
        return False, f"Auth error: {e}", None

def admin_reset_password(target_username: str, new_password: str) -> Tuple[bool, str]:
    """Admin password reset with case-insensitive lookup"""
    normalized = normalize_username(target_username)
    hashed = hash_password(new_password)
    
    try:
        supabase.table("users").update({"password": hashed}).eq("username", normalized).execute()
        return True, "Password reset"
    except Exception as e:
        return False, f"Admin reset error: {e}"

def delete_account_db(username: str) -> Tuple[bool, str]:
    """Delete account with case-insensitive lookup"""
    normalized = normalize_username(username)
    
    try:
        # First delete all user data
        tables = ["notes", "flashcards", "study_sessions", "events"]
        for table in tables:
            supabase.table(table).delete().eq("username", normalized).execute()
            
        # Then delete user
        supabase.table("users").delete().eq("username", normalized).execute()
        return True, "Account deleted"
    except Exception as e:
        return False, f"Delete error: {e}"

# ---------- Save / load user data ----------
def save_current_user(session_state: dict) -> Tuple[bool, str]:
    """Save all user data using lowercase username"""
    username = session_state.get("username")
    if not username:
        return False, "No username in session"
    
    normalized = normalize_username(username)
    
    try:
        # Notes
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

        # Flashcards
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

        # Study sessions
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

        # Events
        supabase.table("events").delete().eq("username", normalized).execute()
        events = []
        for e in session_state.get("events", []):
            events.append({
                "username": normalized,
                "name": e.get("name"),
                "date": e.get("date"),
                "notes": e.get("notes"),
                "color": e.get("color"),
                "created_at": e.get("created") or _now_iso()
            })
        if events:
            supabase.table("events").insert(events).execute()

        return True, "Data saved"
    except Exception as e:
        return False, f"Save error: {e}"

def load_user_data(username: str, merge_local: bool = False, local_state: Optional[dict] = None) -> Tuple[bool, dict]:
    """Load user data using lowercase username"""
    normalized = normalize_username(username)
    
    try:
        # notes
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

        # flashcards
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

        # study_sessions
        r = supabase.table("study_sessions").select("*").eq("username", normalized).execute()
        study_sessions = []
        if r.data:
            for row in r.data:
                study_sessions.append(row.get("data") or {"timestamp": row.get("timestamp"), "activity_type": row.get("activity_type")})

        # events
        r = supabase.table("events").select("*").eq("username", normalized).execute()
        events = []
        if r.data:
            for row in r.data:
                events.append({
                    "name": row.get("name"),
                    "date": row.get("date"),
                    "notes": row.get("notes"),
                    "color": row.get("color"),
                    "created": row.get("created_at")
                })

        payload = {
            "notes": notes,
            "flashcards": flashcards,
            "study_sessions": study_sessions,
            "events": events
        }

        if merge_local and local_state:
            merged = {
                "notes": local_state.get("notes", []) + payload["notes"],
                "flashcards": local_state.get("flashcards", []) + payload["flashcards"],
                "study_sessions": local_state.get("study_sessions", []) + payload["study_sessions"],
                "events": local_state.get("events", []) + payload["events"]
            }
            return True, merged

        return True, payload
    except Exception as e:
        return False, {"error": str(e)}
