import streamlit as st
import json
from datetime import datetime

class DataPersistence:
    """Handle saving and loading user data to browser local storage"""
    
    def __init__(self):
        self.storage_keys = {
            'notes': 'study_platform_notes',
            'flashcards': 'study_platform_flashcards', 
            'study_sessions': 'study_platform_sessions',
            'user_settings': 'study_platform_settings'
        }
    
    def save_all_data(self):
        """Save all user data to browser local storage"""
        try:
            # Prepare data for saving
            data_to_save = {
                'notes': st.session_state.get('notes', []),
                'flashcards': st.session_state.get('flashcards', []),
                'study_sessions': st.session_state.get('study_sessions', []),
                'last_saved': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Use Streamlit's built-in local storage via JavaScript
            for key, storage_key in self.storage_keys.items():
                if key in data_to_save:
                    self._save_to_local_storage(storage_key, data_to_save[key])
            
            return True
        except Exception as e:
            st.error(f"Error saving data: {str(e)}")
            return False
    
    def load_all_data(self):
        """Load all user data from browser local storage"""
        try:
            # Load each data type
            notes = self._load_from_local_storage(self.storage_keys['notes'], [])
            flashcards = self._load_from_local_storage(self.storage_keys['flashcards'], [])
            sessions = self._load_from_local_storage(self.storage_keys['study_sessions'], [])
            
            # Update session state
            if notes:
                st.session_state.notes = notes
            if flashcards:
                st.session_state.flashcards = flashcards
            if sessions:
                st.session_state.study_sessions = sessions
            
            return True
        except Exception as e:
            st.warning(f"Could not load saved data: {str(e)}")
            return False
    
    def _save_to_local_storage(self, key, data):
        """Save data to browser local storage using JavaScript"""
        json_data = json.dumps(data)
        
        # Create JavaScript code to save to localStorage
        js_code = f"""
        <script>
        localStorage.setItem('{key}', {json.dumps(json_data)});
        </script>
        """
        
        # Execute JavaScript (this will be hidden from user)
        st.components.v1.html(js_code, height=0)
    
    def _load_from_local_storage(self, key, default_value):
        """Load data from browser local storage"""
        # For now, return default since we can't easily read from localStorage in Streamlit
        # This would require a custom component or different approach
        return default_value
    
    def export_user_data(self):
        """Export all user data as downloadable JSON file"""
        data = {
            'notes': st.session_state.get('notes', []),
            'flashcards': st.session_state.get('flashcards', []),
            'study_sessions': st.session_state.get('study_sessions', []),
            'export_date': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        return json.dumps(data, indent=2)
    
    def import_user_data(self, json_data):
        """Import user data from JSON file"""
        try:
            data = json.loads(json_data)
            
            # Validate data structure
            if not isinstance(data, dict):
                raise ValueError("Invalid data format")
            
            # Import each data type
            if 'notes' in data and isinstance(data['notes'], list):
                st.session_state.notes.extend(data['notes'])
            
            if 'flashcards' in data and isinstance(data['flashcards'], list):
                st.session_state.flashcards.extend(data['flashcards'])
            
            if 'study_sessions' in data and isinstance(data['study_sessions'], list):
                st.session_state.study_sessions.extend(data['study_sessions'])
            
            return True
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")
            return False
    
    def clear_all_data(self):
        """Clear all user data"""
        try:
            # Clear session state
            st.session_state.notes = []
            st.session_state.flashcards = []
            st.session_state.study_sessions = []
            st.session_state.current_note = ""
            st.session_state.note_title = ""
            st.session_state.current_quiz = None
            st.session_state.quiz_answers = {}
            
            # Clear local storage (JavaScript)
            for storage_key in self.storage_keys.values():
                js_code = f"""
                <script>
                localStorage.removeItem('{storage_key}');
                </script>
                """
                st.components.v1.html(js_code, height=0)
            
            return True
        except Exception as e:
            st.error(f"Error clearing data: {str(e)}")
            return False
    
    def get_data_summary(self):
        """Get summary of user's data"""
        return {
            'notes_count': len(st.session_state.get('notes', [])),
            'flashcards_count': len(st.session_state.get('flashcards', [])),
            'sessions_count': len(st.session_state.get('study_sessions', [])),
            'subjects': list(set([
                note.get('category', 'General') for note in st.session_state.get('notes', [])
            ] + [
                card.get('category', 'General') for card in st.session_state.get('flashcards', [])
            ]))
        }