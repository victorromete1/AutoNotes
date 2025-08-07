import streamlit as st
import json
from datetime import datetime, timedelta
from note_generator import NoteGenerator
from flashcard_generator import FlashcardGenerator
from quiz_generator import QuizGenerator
from progress_tracker import ProgressTracker
from pdf_report_generator import PDFReportGenerator
from data_persistence import DataPersistence
from advanced_quiz_system import AdvancedQuizSystem
from utils import export_notes_as_text, sanitize_filename
import base64

# Configure page
st.set_page_config(
    page_title="Advanced AI Study Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize generators
@st.cache_resource
def get_generators():
    return {
        'notes': NoteGenerator(),
        'flashcards': FlashcardGenerator(),
        'quiz': QuizGenerator(),
        'progress': ProgressTracker(),
        'pdf': PDFReportGenerator()
    }

generators = get_generators()
persistence = DataPersistence()
advanced_quiz = AdvancedQuizSystem(generators['quiz'])

# Initialize comprehensive session state
def init_session_state():
    defaults = {
        'notes': [],
        'flashcards': [],
        'quizzes': [],
        'study_sessions': [],
        'current_note': "",
        'note_title': "",
        'note_category': "General",
        'current_flashcards': [],
        'current_quiz': None,
        'quiz_answers': {},
        'page': 'Home'
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# Auto-load saved data on app start
persistence.load_all_data()

# Simple auto-save function
def auto_save():
    """Auto-save data when changes occur"""
    try:
        persistence.auto_save_data()
    except:
        pass  # Silent fail to avoid disrupting user experience

# Enhanced Navigation Sidebar
with st.sidebar:
    st.title("🎓 Study Platform")
    
    # Show AI provider
    try:
        if hasattr(generators['notes'], 'provider'):
            if "Free" in generators['notes'].provider:
                st.success(f"🆓 {generators['notes'].provider}")
            else:
                st.info(f"🤖 {generators['notes'].provider}")
    except:
        st.info("🤖 AI Service Ready")
    
    st.divider()
    
    # Navigation
    page = st.selectbox(
        "📱 Navigate to:",
        ["🏠 Home", "📝 Notes", "📚 Flashcards", "🧠 Quizzes", "📊 Progress", "📄 Reports"],
        index=["🏠 Home", "📝 Notes", "📚 Flashcards", "🧠 Quizzes", "📊 Progress", "📄 Reports"].index(st.session_state.page) if st.session_state.page in ["🏠 Home", "📝 Notes", "📚 Flashcards", "🧠 Quizzes", "📊 Progress", "📄 Reports"] else 0
    )
    st.session_state.page = page
    
    st.divider()
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    st.metric("Notes", len(st.session_state.notes))
    st.metric("Flashcards", len(st.session_state.flashcards))
    st.metric("Quizzes Taken", len(st.session_state.study_sessions))
    
    st.divider()
    
    # Data Management
    st.subheader("💾 Data Management")
    st.success("🔄 Auto-save: Active")
    
    # Export all data
    if st.button("📥 Download All Data", use_container_width=True, help="Save all your notes, flashcards, and progress"):
        exported_data = persistence.export_user_data()
        st.download_button(
            label="📁 Download Study Data",
            data=exported_data,
            file_name=f"study_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Import data
    uploaded_data = st.file_uploader(
        "📤 Upload Study Data",
        type=['json'],
        help="Restore your saved progress",
        key="data_upload"
    )
    
    if uploaded_data:
        try:
            file_content = uploaded_data.read().decode('utf-8')
            if persistence.import_user_data(file_content):
                st.success("✅ Data imported successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to import data")
        except Exception as e:
            st.error(f"Error importing data: {str(e)}")
    
    # Clear all data option
    with st.expander("⚠️ Reset All Data"):
        st.warning("This will delete all your notes, flashcards, and progress!")
        if st.button("🗑️ Clear Everything", type="secondary"):
            if st.button("⚠️ Confirm Delete All", type="primary"):
                persistence.clear_all_data()
                st.success("All data cleared!")
                st.rerun()

# Page functions
def show_home_page():
    st.title("🎓 Advanced AI Study Platform")
    st.markdown("### Your complete study companion with AI-powered learning tools")
    
    # Feature overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📝 Smart Notes
        - AI-generated study notes
        - Multiple note types
        - Upload & summarize content
        - Category organization
        """)
    
    with col2:
        st.markdown("""
        #### 📚 Flashcards
        - Auto-generate from notes
        - Import/export flashcard files
        - Spaced repetition
        - Progress tracking
        """)
    
    with col3:
        st.markdown("""
        #### 🧠 Quizzes
        - Multiple choice, T/F, short answer
        - AI-powered grading
        - Detailed feedback
        - Performance analytics
        """)
    
    st.divider()
    
    # Recent activity
    if st.session_state.study_sessions:
        st.subheader("🕐 Recent Activity")
        recent_sessions = sorted(st.session_state.study_sessions, 
                               key=lambda x: x.get('timestamp', ''), reverse=True)[:5]
        
        for session in recent_sessions:
            activity_type = session.get('activity_type', 'study').title()
            subject = session.get('subject', 'General')
            timestamp = datetime.fromisoformat(session.get('timestamp', '')).strftime("%m/%d %H:%M")
            
            score_text = ""
            if session.get('score') is not None:
                score_text = f" - Score: {session.get('score', 0)}%"
            
            st.text(f"🔹 {timestamp} | {activity_type} in {subject}{score_text}")
    
    # Important notice about data persistence
    st.info("💡 **Auto-Save Active:** Your progress is automatically saved to your browser! Use 'Download All Data' in the sidebar to create backup files you can share between devices.")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    quick_col1, quick_col2, quick_col3 = st.columns(3)
    
    with quick_col1:
        if st.button("📝 Create Notes", use_container_width=True):
            st.session_state.page = "📝 Notes"
            st.rerun()
    
    with quick_col2:
        if st.button("📚 Study Flashcards", use_container_width=True):
            st.session_state.page = "📚 Flashcards"
            st.rerun()
    
    with quick_col3:
        if st.button("🧠 Take Quiz", use_container_width=True):
            st.session_state.page = "🧠 Quizzes"
            st.rerun()

def show_notes_page():
    st.title("📝 AI Note Generation")
    
    # Input methods
    input_method = st.radio(
        "Choose input method:",
        ["📖 Topic/Subject", "📄 Upload/Text Content", "❓ Questions/Prompts"],
        horizontal=True
    )
    
    user_input = ""
    
    if input_method == "📖 Topic/Subject":
        col1, col2 = st.columns([2, 1])
        with col1:
            user_input = st.text_input(
                "Enter a topic or subject:",
                placeholder="e.g., Photosynthesis, World War II, Machine Learning..."
            )
        
        with col2:
            note_type = st.selectbox(
                "Note type:",
                ["Summary", "Detailed Explanation", "Key Points", "Study Guide", "Definitions"]
            )
        
        detail_level = st.select_slider(
            "Detail level:",
            options=["Basic", "Intermediate", "Advanced"],
            value="Intermediate"
        )
        
    elif input_method == "📄 Upload/Text Content":
        uploaded_file = st.file_uploader(
            "Upload a file or paste text:",
            type=['txt', 'pdf', 'docx'],
            help="Upload text files, PDFs, or Word documents"
        )
        
        if uploaded_file:
            try:
                if uploaded_file.type == "text/plain":
                    file_content = str(uploaded_file.read(), "utf-8")
                    user_input = file_content
                    st.success(f"✅ File uploaded: {uploaded_file.name}")
                else:
                    st.warning("Currently supporting text files. PDF and DOCX support coming soon!")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        
        user_input = st.text_area(
            "Or paste text content:",
            value=user_input,
            placeholder="Paste your lecture notes, textbook content, or any text...",
            height=150
        )
        
        note_type = st.selectbox(
            "Processing type:",
            ["Summarize", "Extract Key Points", "Create Study Questions", "Organize Content"]
        )
        
    else:  # Questions/Prompts
        user_input = st.text_area(
            "Enter your questions or prompts:",
            placeholder="e.g., Explain quantum mechanics, What are the causes of climate change?",
            height=100
        )
        note_type = "Answer Questions"
    
    # Category and title
    col1, col2 = st.columns(2)
    with col1:
        note_title = st.text_input(
            "Note Title (optional):",
            placeholder="Auto-generated if left blank"
        )
    
    with col2:
        categories_list = ["General", "Math", "Science", "History", "Literature", "Languages", "Arts", "Technology", "Other"]
        current_categories = list(set([note.get('category', 'General') for note in st.session_state.notes]))
        all_categories = sorted(list(set(categories_list + current_categories)))
        
        category = st.selectbox("Category:", all_categories)
    
    # Generate button
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Generate Notes", type="primary", use_container_width=True):
            if user_input.strip():
                with st.spinner("Generating notes... This may take a moment."):
                    try:
                        generated_notes = generators['notes'].generate_notes(
                            user_input, 
                            note_type=note_type,
                            detail_level=locals().get('detail_level', 'Intermediate')
                        )
                        
                        # Auto-generate title if not provided
                        if not note_title.strip():
                            note_title = f"{note_type}: {user_input[:50]}..." if len(user_input) > 50 else f"{note_type}: {user_input}"
                        
                        # Save note
                        new_note = {
                            'title': note_title,
                            'content': generated_notes,
                            'category': category,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.notes.append(new_note)
                        
                        # Add study session
                        session = {
                            'timestamp': datetime.now().isoformat(),
                            'activity_type': 'study',
                            'subject': category,
                            'duration_minutes': 5,  # Estimated time for note generation
                            'notes_created': 1
                        }
                        st.session_state.study_sessions.append(session)
                        
                        # Auto-save progress
                        persistence.auto_save_data()
                        
                        st.success("✅ Notes generated and saved successfully!")
                        st.markdown("### Generated Notes:")
                        st.markdown(generated_notes)
                        
                    except Exception as e:
                        st.error(f"Error generating notes: {str(e)}")
            else:
                st.warning("Please enter some content to generate notes from.")
    
    with col2:
        if st.button("📚 Generate Flashcards from Notes", use_container_width=True):
            if user_input.strip():
                with st.spinner("Creating flashcards..."):
                    try:
                        flashcards = generators['flashcards'].generate_flashcards(
                            user_input, num_cards=8, difficulty="Medium"
                        )
                        
                        if flashcards:
                            # Add to flashcards collection
                            for card in flashcards:
                                card['category'] = category
                            
                            st.session_state.flashcards.extend(flashcards)
                            st.success(f"✅ Generated {len(flashcards)} flashcards!")
                            
                            # Show preview
                            st.markdown("### Flashcard Preview:")
                            for i, card in enumerate(flashcards[:3], 1):
                                with st.expander(f"Card {i}: {card['front'][:50]}..."):
                                    st.write(f"**Front:** {card['front']}")
                                    st.write(f"**Back:** {card['back']}")
                        
                    except Exception as e:
                        st.error(f"Error generating flashcards: {str(e)}")
    
    # Display existing notes
    if st.session_state.notes:
        st.divider()
        st.subheader("📚 Saved Notes")
        
        # Filter options
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            categories = ["All"] + sorted(list(set([note.get('category', 'General') for note in st.session_state.notes])))
            selected_category = st.selectbox("Filter by category:", categories)
        
        with filter_col2:
            search_term = st.text_input("🔍 Search notes:", placeholder="Search titles or content...")
        
        # Filter notes
        filtered_notes = st.session_state.notes
        if selected_category != "All":
            filtered_notes = [note for note in filtered_notes if note.get('category', 'General') == selected_category]
        
        if search_term:
            filtered_notes = [note for note in filtered_notes if 
                            search_term.lower() in note.get('title', '').lower() or 
                            search_term.lower() in note.get('content', '').lower()]
        
        # Display notes
        for i, note in enumerate(filtered_notes):
            with st.expander(f"📄 {note['title']} ({note.get('category', 'General')})"):
                st.write(f"**Created:** {note['timestamp']}")
                st.markdown(note['content'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🗑️ Delete", key=f"del_note_{i}"):
                        st.session_state.notes.remove(note)
                        st.rerun()
                
                with col2:
                    st.download_button(
                        "📥 Export",
                        data=note['content'],
                        file_name=f"{sanitize_filename(note['title'])}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        key=f"export_note_{i}"
                    )
                
                with col3:
                    if st.button("📚 Create Flashcards", key=f"flashcard_note_{i}"):
                        with st.spinner("Creating flashcards from note..."):
                            try:
                                flashcards = generators['flashcards'].generate_flashcards(
                                    note['content'], num_cards=6, difficulty="Medium"
                                )
                                
                                for card in flashcards:
                                    card['category'] = note.get('category', 'General')
                                
                                st.session_state.flashcards.extend(flashcards)
                                auto_save()
                                st.success(f"✅ Created {len(flashcards)} flashcards from this note!")
                                
                                # Add to study sessions
                                session = {
                                    'timestamp': datetime.now().isoformat(),
                                    'activity_type': 'flashcards_created',
                                    'subject': note.get('category', 'General'),
                                    'flashcards_created': len(flashcards),
                                    'duration_minutes': 2
                                }
                                st.session_state.study_sessions.append(session)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

def next_card(study_cards, correct=False):
    """Move to next card and track progress"""
    if 'cards_studied' not in st.session_state:
        st.session_state.cards_studied = 0
    if 'cards_correct' not in st.session_state:
        st.session_state.cards_correct = 0
    
    st.session_state.cards_studied += 1
    if correct:
        st.session_state.cards_correct += 1
    
    st.session_state.current_card_index += 1
    st.session_state.show_answer = False
    
    if st.session_state.current_card_index >= len(study_cards):
        # Session complete
        session = {
            'timestamp': datetime.now().isoformat(),
            'activity_type': 'flashcards',
            'subject': 'Mixed' if len(set([card.get('category', 'General') for card in study_cards])) > 1 else study_cards[0].get('category', 'General'),
            'duration_minutes': 10,
            'flashcards_studied': st.session_state.cards_studied,
            'correct_answers': st.session_state.cards_correct,
            'questions_answered': st.session_state.cards_studied
        }
        st.session_state.study_sessions.append(session)
        auto_save()
        
        st.success(f"Session complete! You studied {st.session_state.cards_studied} cards with {(st.session_state.cards_correct/st.session_state.cards_studied)*100:.1f}% accuracy!")
        
        # Reset for next session
        for key in ['current_card_index', 'show_answer', 'cards_studied', 'cards_correct']:
            if key in st.session_state:
                del st.session_state[key]
    
    st.rerun()

def show_flashcards_page():
    st.title("📚 Flashcards")
    
    # Tabs for different flashcard functions
    tab1, tab2, tab3 = st.tabs(["📖 Study", "➕ Create", "📂 Manage"])
    
    with tab1:
        st.subheader("📖 Study Session")
        
        if not st.session_state.flashcards:
            st.info("No flashcards available. Create some first!")
            return
        
        # Filter flashcards for study
        categories = list(set([card.get('category', 'General') for card in st.session_state.flashcards]))
        selected_category = st.selectbox("Study category:", ["All"] + categories)
        
        study_cards = st.session_state.flashcards
        if selected_category != "All":
            study_cards = [card for card in study_cards if card.get('category', 'General') == selected_category]
        
        if study_cards:
            if 'current_card_index' not in st.session_state:
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False
                st.session_state.cards_studied = 0
                st.session_state.cards_correct = 0
            
            current_card = study_cards[st.session_state.current_card_index]
            
            # Progress bar
            progress = (st.session_state.current_card_index + 1) / len(study_cards)
            st.progress(progress, text=f"Card {st.session_state.current_card_index + 1} of {len(study_cards)}")
            
            # Card display
            st.markdown("### 🎴 Flashcard")
            
            # Front of card
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 2px solid #ddd; 
                    border-radius: 10px; 
                    padding: 20px; 
                    margin: 10px 0; 
                    background-color: #f9f9f9;
                    min-height: 150px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                ">
                    <h4>{current_card['front']}</h4>
                </div>
                """, unsafe_allow_html=True)
            
            # Answer section
            if st.session_state.show_answer:
                st.markdown("### 💡 Answer")
                with st.container():
                    st.markdown(f"""
                    <div style="
                        border: 2px solid #4CAF50; 
                        border-radius: 10px; 
                        padding: 20px; 
                        margin: 10px 0; 
                        background-color: #e8f5e8;
                        min-height: 100px;
                    ">
                        {current_card['back']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Self-assessment buttons
                st.markdown("### How well did you know this?")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("❌ Incorrect", use_container_width=True):
                        next_card(study_cards, correct=False)
                
                with col2:
                    if st.button("🤔 Partial", use_container_width=True):
                        next_card(study_cards, correct=True)
                
                with col3:
                    if st.button("✅ Correct", use_container_width=True):
                        next_card(study_cards, correct=True)
            
            else:
                if st.button("🔍 Show Answer", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            
            # Study session stats
            if st.session_state.cards_studied > 0:
                accuracy = (st.session_state.cards_correct / st.session_state.cards_studied) * 100
                st.metric("Session Accuracy", f"{accuracy:.1f}%")

    with tab2:
        st.subheader("➕ Create Flashcards")
        
        # Method selection
        creation_method = st.radio(
            "How do you want to create flashcards?",
            ["📝 From Text/Notes", "📂 Upload .flashcard File", "✋ Manual Entry"],
            horizontal=True
        )
        
        if creation_method == "📝 From Text/Notes":
            content = st.text_area(
                "Paste content to generate flashcards from:",
                placeholder="Paste your notes, textbook content, or any study material...",
                height=150
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                num_cards = st.slider("Number of cards:", 3, 20, 8)
            with col2:
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            with col3:
                category = st.text_input("Category:", value="General")
            
            if st.button("🚀 Generate Flashcards", type="primary"):
                if content.strip():
                    with st.spinner("Creating flashcards..."):
                        try:
                            flashcards = generators['flashcards'].generate_flashcards(
                                content, num_cards=num_cards, difficulty=difficulty
                            )
                            
                            for card in flashcards:
                                card['category'] = category
                            
                            st.session_state.flashcards.extend(flashcards)
                            auto_save()
                            st.success(f"✅ Generated {len(flashcards)} flashcards!")
                            
                            # Preview
                            st.markdown("### 📖 Preview Created Cards:")
                            for i, card in enumerate(flashcards[:3], 1):
                                with st.expander(f"Preview Card {i}"):
                                    st.write(f"**Front:** {card['front']}")
                                    st.write(f"**Back:** {card['back']}")
                                    st.write(f"**Category:** {card['category']}")
                                    st.write(f"**Difficulty:** {card.get('difficulty', 'Medium')}")
                            
                            if len(flashcards) > 3:
                                st.info(f"+ {len(flashcards) - 3} more cards created!")
                            
                            # Add to study sessions
                            session = {
                                'timestamp': datetime.now().isoformat(),
                                'activity_type': 'flashcards_created',
                                'subject': category,
                                'flashcards_created': len(flashcards),
                                'duration_minutes': 2
                            }
                            st.session_state.study_sessions.append(session)
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please enter content to generate flashcards from.")
        
        elif creation_method == "📂 Upload .flashcard File":
            uploaded_file = st.file_uploader(
                "Upload a .flashcard file:",
                type=['flashcard', 'json'],
                help="Upload previously exported flashcard files"
            )
            
            if uploaded_file:
                try:
                    file_content = uploaded_file.read().decode('utf-8')
                    loaded_flashcards = generators['flashcards'].load_flashcards_file(file_content)
                    
                    if loaded_flashcards:
                        st.session_state.flashcards.extend(loaded_flashcards)
                        auto_save()
                        st.success(f"✅ Loaded {len(loaded_flashcards)} flashcards!")
                        
                        # Preview
                        st.markdown("### 📖 Loaded Cards Preview:")
                        for i, card in enumerate(loaded_flashcards[:3], 1):
                            with st.expander(f"Loaded Card {i}"):
                                st.write(f"**Front:** {card['front']}")
                                st.write(f"**Back:** {card['back']}")
                                st.write(f"**Category:** {card.get('category', 'General')}")
                        
                        if len(loaded_flashcards) > 3:
                            st.info(f"+ {len(loaded_flashcards) - 3} more cards loaded!")
                    else:
                        st.error("No valid flashcards found in file.")
                
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        
        else:  # Manual Entry
            st.markdown("#### Add Individual Flashcard")
            
            with st.form("manual_flashcard"):
                front = st.text_area("Front (Question/Term):", height=100)
                back = st.text_area("Back (Answer/Definition):", height=100)
                category = st.text_input("Category:", value="General")
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
                
                if st.form_submit_button("➕ Add Flashcard"):
                    if front.strip() and back.strip():
                        new_card = {
                            'front': front,
                            'back': back,
                            'category': category,
                            'difficulty': difficulty,
                            'created': datetime.now().isoformat(),
                            'id': f"manual_{datetime.now().timestamp()}"
                        }
                        st.session_state.flashcards.append(new_card)
                        auto_save()
                        st.success("✅ Flashcard added successfully!")
                    else:
                        st.warning("Please fill in both front and back of the flashcard.")
    
    with tab3:
        st.subheader("📂 Manage Flashcards")
        
        if not st.session_state.flashcards:
            st.info("No flashcards to manage. Create some first!")
        else:
            # Export all flashcards
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export All Flashcards"):
                    flashcard_data = generators['flashcards'].save_flashcards_file(
                        st.session_state.flashcards, 
                        f"flashcards_{datetime.now().strftime('%Y%m%d')}"
                    )
                    
                    st.download_button(
                        label="Download .flashcard file",
                        data=flashcard_data,
                        file_name=f"flashcards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.flashcard",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("🗑️ Clear All Flashcards", type="secondary"):
                    if st.button("⚠️ Confirm Delete All", type="primary"):
                        st.session_state.flashcards = []
                        auto_save()
                        st.success("All flashcards deleted.")
                        st.rerun()
            
            # Category management
            st.divider()
            categories = list(set([card.get('category', 'General') for card in st.session_state.flashcards]))
            selected_category = st.selectbox("View/Edit category:", ["All"] + categories)
            
            filtered_cards = st.session_state.flashcards
            if selected_category != "All":
                filtered_cards = [card for card in filtered_cards if card.get('category', 'General') == selected_category]
            
            st.write(f"**Showing {len(filtered_cards)} flashcards**")
            
            # Display flashcards
            for i, card in enumerate(filtered_cards):
                with st.expander(f"🎴 {card['front'][:50]}..." if len(card['front']) > 50 else f"🎴 {card['front']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Category:** {card.get('category', 'General')}")
                        st.write(f"**Front:** {card['front']}")
                        st.write(f"**Back:** {card['back']}")
                        st.write(f"**Difficulty:** {card.get('difficulty', 'Medium')}")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_card_{i}"):
                            st.session_state.flashcards.remove(card)
                            auto_save()
                            st.rerun()

def show_quizzes_page():
    st.title("🧠 Advanced Quiz System")
    
    tab1, tab2 = st.tabs(["📝 Take Quiz", "📊 Quiz History"])
    
    with tab1:
        st.subheader("📝 Create & Take Quiz")
        
        # Check if quiz is in progress
        if st.session_state.get('quiz_started', False) and not st.session_state.get('quiz_completed', False):
            # Display ongoing quiz
            if 'active_quiz_data' in st.session_state:
                advanced_quiz.display_quiz_interface(st.session_state.active_quiz_data)
            else:
                st.error("Quiz data lost. Please start a new quiz.")
                if st.button("🔄 Reset Quiz"):
                    advanced_quiz._reset_quiz_state()
                    st.rerun()
        else:
            # Quiz creation interface
            col1, col2 = st.columns(2)
            
            with col1:
                quiz_source = st.radio(
                    "Create quiz from:",
                    ["📚 Existing Notes", "📝 New Content", "📤 Upload File"],
                    horizontal=False
                )
            
            with col2:
                num_questions = st.slider("Number of questions:", 3, 15, 8)
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            
            content = ""
            
            # Handle different content sources
            if quiz_source == "📚 Existing Notes":
                if st.session_state.notes:
                    note_titles = [f"{note['title']} ({note.get('category', 'General')})" for note in st.session_state.notes]
                    selected_note_title = st.selectbox("Select note:", note_titles)
                    
                    if selected_note_title:
                        # Extract the actual title (remove category)
                        actual_title = selected_note_title.split(' (')[0]
                        selected_note_obj = next((note for note in st.session_state.notes if note['title'] == actual_title), None)
                        if selected_note_obj:
                            content = selected_note_obj['content']
                            st.text_area("Content preview:", value=content[:300] + "..." if len(content) > 300 else content, height=100, disabled=True)
                else:
                    st.info("No notes available. Create some notes first!")
                    return
            
            elif quiz_source == "📝 New Content":
                content = st.text_area(
                    "Enter content for quiz:",
                    placeholder="Paste study material, notes, or any content to create a quiz from...",
                    height=200
                )
            
            elif quiz_source == "📤 Upload File":
                content = advanced_quiz.upload_content_for_quiz()
            
            # Create quiz button
            if st.button("🚀 Create & Start Quiz", type="primary", use_container_width=True):
                if content and content.strip():
                    with st.spinner("Creating your personalized quiz... This may take a moment."):
                        try:
                            quiz_data = advanced_quiz.create_quiz_from_content(
                                content=content,
                                num_questions=num_questions,
                                difficulty=difficulty
                            )
                            
                            if quiz_data and quiz_data.get('questions'):
                                st.session_state.active_quiz_data = quiz_data
                                st.session_state.quiz_started = True
                                st.session_state.quiz_completed = False
                                st.session_state.current_question = 0
                                st.session_state.quiz_answers = {}
                                st.success("✅ Quiz created successfully! Starting now...")
                                st.rerun()
                            else:
                                st.error("Failed to create quiz. Please check your content and try again.")
                        
                        except Exception as e:
                            st.error(f"Error creating quiz: {str(e)}")
                            st.info("Please try with different content or contact support if the issue persists.")
                else:
                    st.warning("Please provide content for the quiz.")
    
    with tab2:
        st.subheader("📊 Quiz History & Progress")
        
        # Get quiz sessions
        quiz_sessions = [s for s in st.session_state.get('study_sessions', []) if s.get('activity_type') == 'quiz']
        
        if quiz_sessions:
            # Overall stats
            col1, col2, col3, col4 = st.columns(4)
            
            total_quizzes = len(quiz_sessions)
            avg_score = sum(s.get('score', 0) for s in quiz_sessions) / total_quizzes
            highest_score = max(s.get('score', 0) for s in quiz_sessions)
            recent_trend = "📈" if len(quiz_sessions) >= 2 and quiz_sessions[-1].get('score', 0) > quiz_sessions[-2].get('score', 0) else "📊"
            
            with col1:
                st.metric("Total Quizzes", total_quizzes)
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                st.metric("Best Score", f"{highest_score:.1f}%")
            with col4:
                st.metric("Trend", recent_trend)
            
            # Recent quiz history
            st.subheader("Recent Quiz Results")
            
            for i, session in enumerate(reversed(quiz_sessions[-10:])):  # Show last 10
                timestamp = datetime.fromisoformat(session['timestamp']).strftime("%Y-%m-%d %H:%M")
                score = session.get('score', 0)
                correct = session.get('correct_answers', 0)
                total = session.get('questions_answered', session.get('total_questions', 0))
                
                # Color code based on performance
                if score >= 90:
                    score_color = "🟢"
                elif score >= 80:
                    score_color = "🟡" 
                elif score >= 70:
                    score_color = "🟠"
                else:
                    score_color = "🔴"
                
                with st.expander(f"{score_color} {timestamp} - {score:.1f}% ({correct}/{total})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Score:** {score:.1f}%")
                        st.write(f"**Questions:** {correct}/{total}")
                    with col2:
                        st.write(f"**Difficulty:** {session.get('difficulty', 'N/A')}")
                        st.write(f"**Type:** {session.get('quiz_type', 'N/A')}")
        else:
            st.info("No quiz history yet. Take your first quiz to see your progress here!")

# Quiz functions now handled by AdvancedQuizSystem

def show_progress_page():
    st.title("📊 Progress Analytics")
    
    if not st.session_state.study_sessions:
        st.info("No study data yet. Start studying to see your progress!")
        return
    
    # Calculate progress statistics
    progress_stats = {}
    
    # Overall stats
    overall_stats = generators['progress'].calculate_subject_stats(st.session_state.study_sessions)
    progress_stats['overall'] = overall_stats
    
    # Subject-specific stats
    subjects = list(set(s.get('subject', 'General') for s in st.session_state.study_sessions))
    subject_stats = {}
    for subject in subjects:
        subject_stats[subject] = generators['progress'].calculate_subject_stats(
            st.session_state.study_sessions, subject
        )
    progress_stats['subjects'] = subject_stats
    
    # Display overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Sessions", 
            overall_stats['total_sessions'],
            help="Total number of study sessions completed"
        )
    
    with col2:
        hours = overall_stats['total_study_time'] / 60
        st.metric(
            "Study Time", 
            f"{hours:.1f}h",
            help="Total time spent studying"
        )
    
    with col3:
        st.metric(
            "Average Score", 
            f"{overall_stats['average_score']}%",
            help="Average quiz score across all subjects"
        )
    
    with col4:
        trend = overall_stats['improvement_trend']
        trend_emoji = "📈" if trend == "Improving" else "📉" if trend == "Declining" else "➡️"
        st.metric(
            "Trend", 
            f"{trend_emoji} {trend}",
            help="Performance trend based on recent quiz scores"
        )
    
    # Charts
    st.divider()
    
    # Create charts
    chart_tabs = st.tabs(["📈 Score Trends", "📊 Subject Breakdown", "📅 Activity Pattern"])
    
    with chart_tabs[0]:
        st.subheader("📈 Quiz Score Trends")
        chart_data = generators['progress'].create_progress_chart(
            st.session_state.study_sessions, "score_over_time"
        )
        if chart_data:
            st.image(f"data:image/png;base64,{chart_data}")
        else:
            st.info("Take more quizzes to see score trends!")
    
    with chart_tabs[1]:
        st.subheader("📊 Study Time by Subject")
        chart_data = generators['progress'].create_progress_chart(
            st.session_state.study_sessions, "subject_breakdown"
        )
        if chart_data:
            st.image(f"data:image/png;base64,{chart_data}")
        else:
            st.info("Study multiple subjects to see breakdown!")
    
    with chart_tabs[2]:
        st.subheader("📅 Activity Frequency by Day")
        chart_data = generators['progress'].create_progress_chart(
            st.session_state.study_sessions, "activity_frequency"
        )
        if chart_data:
            st.image(f"data:image/png;base64,{chart_data}")
        else:
            st.info("More study sessions needed for activity pattern analysis!")
    
    # Subject performance details
    st.divider()
    st.subheader("📚 Subject Performance Details")
    
    if subject_stats:
        # Create a table of subject performance
        performance_data = []
        for subject, stats in subject_stats.items():
            performance_data.append({
                'Subject': subject,
                'Sessions': stats['total_sessions'],
                'Avg Score': f"{stats['average_score']}%",
                'Accuracy': f"{stats['accuracy']}%",
                'Trend': stats['improvement_trend'],
                'Quiz Count': stats['quiz_sessions']
            })
        
        import pandas as pd
        df = pd.DataFrame(performance_data)
        st.dataframe(df, use_container_width=True)
    
    # Strengths and weaknesses analysis
    st.divider()
    analysis = generators['progress'].get_strengths_and_weaknesses(st.session_state.study_sessions)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💪 Your Strengths")
        if analysis['strengths']:
            for strength in analysis['strengths']:
                st.success(f"✅ {strength}")
        else:
            st.info("Take more quizzes to identify your strengths!")
    
    with col2:
        st.subheader("📈 Areas for Improvement")
        if analysis['needs_improvement']:
            for weakness in analysis['needs_improvement']:
                st.warning(f"⚠️ {weakness}")
        else:
            st.success("🎉 Great job! No clear weaknesses identified.")
    
    # Recommendations
    st.divider()
    st.subheader("🎯 Personalized Recommendations")
    
    recommendations = generators['progress'].generate_study_recommendations(st.session_state.study_sessions)
    for i, rec in enumerate(recommendations, 1):
        st.info(f"{i}. {rec}")
    
    # Weekly summary
    st.divider()
    st.subheader("📅 This Week's Summary")
    
    weekly_summary = generators['progress'].get_weekly_summary(st.session_state.study_sessions)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sessions This Week", weekly_summary['total_sessions'])
        st.metric("Study Time This Week", f"{weekly_summary['total_study_time']} min")
    
    with col2:
        st.write("**Subjects Studied:**")
        for subject, stats in weekly_summary['subjects'].items():
            st.write(f"• {subject}: {stats['total_sessions']} sessions")

def show_reports_page():
    st.title("📄 Study Reports")
    
    if not st.session_state.study_sessions:
        st.info("No study data yet. Complete some study sessions to generate reports!")
        return
    
    st.markdown("Generate comprehensive PDF reports of your study progress and performance.")
    
    # Report options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Progress Report")
        st.markdown("""
        **Includes:**
        - Overall performance summary
        - Subject-by-subject breakdown
        - Strengths and improvement areas
        - Study habits analysis
        - Personalized recommendations
        - Recent activity log
        """)
        
        if st.button("📥 Generate Progress Report", type="primary", use_container_width=True):
            generate_progress_report()
    
    with col2:
        st.subheader("📚 Flashcard Report")
        st.markdown("""
        **Includes:**
        - All your flashcards organized by category
        - Study statistics
        - Flashcard performance metrics
        - Ready for printing
        """)
        
        if st.button("📥 Generate Flashcard Report", type="primary", use_container_width=True):
            generate_flashcard_report()
    
    # Report history (if we want to store previous reports)
    st.divider()
    st.subheader("📋 Quick Stats for Reports")
    
    # Calculate stats for report preview
    total_sessions = len(st.session_state.study_sessions)
    quiz_sessions = [s for s in st.session_state.study_sessions if s.get('activity_type') == 'quiz']
    avg_score = sum(s.get('score', 0) for s in quiz_sessions) / len(quiz_sessions) if quiz_sessions else 0
    subjects = len(set(s.get('subject', 'General') for s in st.session_state.study_sessions))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", total_sessions)
    with col2:
        st.metric("Quizzes Taken", len(quiz_sessions))
    with col3:
        st.metric("Average Score", f"{avg_score:.1f}%" if quiz_sessions else "N/A")
    with col4:
        st.metric("Subjects Studied", subjects)

def generate_progress_report():
    """Generate and download progress report PDF"""
    with st.spinner("Generating your progress report..."):
        try:
            # Calculate comprehensive progress stats
            progress_stats = {}
            
            # Overall stats
            overall_stats = generators['progress'].calculate_subject_stats(st.session_state.study_sessions)
            progress_stats['overall'] = overall_stats
            
            # Subject-specific stats
            subjects = list(set(s.get('subject', 'General') for s in st.session_state.study_sessions))
            subject_stats = {}
            for subject in subjects:
                subject_stats[subject] = generators['progress'].calculate_subject_stats(
                    st.session_state.study_sessions, subject
                )
            progress_stats['subjects'] = subject_stats
            
            # Generate PDF
            pdf_data = generators['pdf'].generate_progress_report(
                user_data={},  # Could include user name, etc.
                sessions=st.session_state.study_sessions,
                progress_stats=progress_stats
            )
            
            # Offer download
            st.download_button(
                label="📥 Download Progress Report",
                data=pdf_data,
                file_name=f"study_progress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
            
            st.success("✅ Progress report generated successfully!")
        
        except Exception as e:
            st.error(f"Error generating report: {str(e)}")

def generate_flashcard_report():
    """Generate and download flashcard report PDF"""
    if not st.session_state.flashcards:
        st.warning("No flashcards available to include in report.")
        return
    
    with st.spinner("Generating your flashcard report..."):
        try:
            # Calculate flashcard stats
            flashcard_sessions = [s for s in st.session_state.study_sessions 
                                if s.get('activity_type') == 'flashcards']
            
            study_stats = {
                'sessions': len(flashcard_sessions),
                'cards_studied': sum(s.get('flashcards_studied', 0) for s in flashcard_sessions),
                'mastered': sum(s.get('correct_answers', 0) for s in flashcard_sessions)
            }
            
            # Generate PDF
            pdf_data = generators['pdf'].generate_flashcard_report(
                flashcards=st.session_state.flashcards,
                study_stats=study_stats
            )
            
            # Offer download
            st.download_button(
                label="📥 Download Flashcard Report",
                data=pdf_data,
                file_name=f"flashcard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )
            
            st.success("✅ Flashcard report generated successfully!")
        
        except Exception as e:
            st.error(f"Error generating flashcard report: {str(e)}")

# Main content routing (after all functions are defined)
if st.session_state.page == "🏠 Home":
    show_home_page()
elif st.session_state.page == "📝 Notes":
    show_notes_page()
elif st.session_state.page == "📚 Flashcards":
    show_flashcards_page()
elif st.session_state.page == "🧠 Quizzes":
    show_quizzes_page()
elif st.session_state.page == "📊 Progress":
    show_progress_page()
elif st.session_state.page == "📄 Reports":
    show_reports_page()
