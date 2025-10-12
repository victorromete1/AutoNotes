# THIS FILE IS NOT IN USE, JUST FOR DEBUGGING PURPOSES
import streamlit as st
import json
from datetime import datetime

class DataPersistence:
    def __init__(self):
        self.storage_keys = {
            'notes': 'study_platform_notes',
            'flashcards': 'study_platform_flashcards',
            'study_sessions': 'study_platform_sessions',
            'user_settings': 'study_platform_settings'
        }

    def save_all_data(self):
        try:
            data_to_save = {
                'notes': st.session_state.get('notes', []),
                'flashcards': st.session_state.get('flashcards', []),
                'study_sessions': st.session_state.get('study_sessions', []),
                'last_saved': datetime.now().isoformat(),
                'version': '1.0'
            }
            self._save_to_local_storage('study_platform_data', data_to_save)
            return True
        except Exception as e:
            st.error(f"Error saving data: {str(e)}")
            return False

    def auto_save_data(self):
        try:
            self.save_all_data()
        except Exception:
            pass

    def load_all_data(self):
        try:
            if hasattr(st.session_state, 'data_load_attempted'):
                return True
            st.session_state.data_load_attempted = True
            self._create_auto_load_component()
            return True
        except Exception as e:
            st.warning(f"Could not initialize data loading: {str(e)}")
            return False

    def _create_auto_load_component(self):
        html_code = """
        <script>
        function loadStudyData() {
            try {
                const savedData = localStorage.getItem('study_platform_data');
                if (savedData) {
                    const data = JSON.parse(savedData);
                    console.log('Auto-loaded study data:', data);
                }
            } catch(e) {
                console.error('Error auto-loading data:', e);
            }
        }
        loadStudyData();
        </script>
        <div style="display: none;">Auto-load component</div>
        """
        st.components.v1.html(html_code, height=0)

    def _save_to_local_storage(self, key, data):
        try:
            json_data = json.dumps(data, default=str)
            html_code = f"""
            <script>
            try {{
                localStorage.setItem('{key}', {json.dumps(json_data)});
                console.log('Auto-save completed');
            }} catch(e) {{
                console.warn('Auto-save failed:', e);
            }}
            </script>
            """
            st.components.v1.html(html_code, height=0)
        except Exception:
            pass

    def _load_from_local_storage(self, key, default_value):
        return default_value

    def export_user_data(self):
        data = {
            'notes': st.session_state.get('notes', []),
            'flashcards': st.session_state.get('flashcards', []),
            'study_sessions': st.session_state.get('study_sessions', []),
            'export_date': datetime.now().isoformat(),
            'version': '1.0'
        }
        return json.dumps(data, indent=2)

    def import_user_data(self, json_data):
        try:
            data = json.loads(json_data)
            if not isinstance(data, dict):
                raise ValueError("Invalid data format")
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
        try:
            st.session_state.notes = []
            st.session_state.flashcards = []
            st.session_state.study_sessions = []
            st.session_state.current_note = ""
            st.session_state.note_title = ""
            st.session_state.current_quiz = None
            st.session_state.quiz_answers = {}
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
