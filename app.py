import streamlit as st
import json
from datetime import datetime
import sys
import os

# Import our modules
from note_generator import NoteGenerator
from flashcard_generator import FlashcardGenerator
from quiz_generator import QuizGenerator
from progress_tracker import ProgressTracker
from pdf_report_generator import PDFReportGenerator
from data_persistence import DataPersistence
from advanced_quiz_system import AdvancedQuizSystem
from utils import sanitize_filename

# Page config
st.set_page_config(
    page_title="AI Study Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'notes' not in st.session_state:
    st.session_state.notes = []
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []
if 'study_sessions' not in st.session_state:
    st.session_state.study_sessions = []
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

# Initialize generators
@st.cache_resource
def initialize_generators():
    return {
        'notes': NoteGenerator(),
        'flashcards': FlashcardGenerator(),
        'quiz': QuizGenerator(),
        'progress': ProgressTracker(),
        'reports': PDFReportGenerator()
    }

generators = initialize_generators()
persistence = DataPersistence()

def auto_save():
    """Auto-save user data"""
    try:
        persistence.auto_save_data()
    except Exception:
        pass  # Silent auto-save

def show_sidebar():
    with st.sidebar:
        st.title("🎓 AI Study Platform")
        st.markdown("---")
        
        # Navigation
        pages = [
            "🏠 Home",
            "📝 Notes", 
            "📚 Flashcards",
            "🧠 Quizzes",
            "📊 Progress",
            "📄 Reports"
        ]
        
        selected = st.radio("Navigate:", pages, key="navigation")
        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        st.subheader("📈 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Notes", len(st.session_state.notes))
            st.metric("Flashcards", len(st.session_state.flashcards))
        with col2:
            sessions = len(st.session_state.study_sessions)
            st.metric("Sessions", sessions)
            if sessions > 0:
                avg_score = sum(s.get('score', 0) for s in st.session_state.study_sessions if 'score' in s) / max(1, len([s for s in st.session_state.study_sessions if 'score' in s]))
                st.metric("Avg Score", f"{avg_score:.1f}%")
        
        st.markdown("---")
        
        # Data management
        st.subheader("💾 Data Management")
        
        # Export data
        all_data = {
            'notes': st.session_state.notes,
            'flashcards': st.session_state.flashcards,
            'study_sessions': st.session_state.study_sessions,
            'exported_at': datetime.now().isoformat()
        }
        
        st.download_button(
            "📥 Export All Data",
            data=json.dumps(all_data, indent=2),
            file_name=f"study_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )
        
        # Import data
        uploaded_file = st.file_uploader("📤 Import Data", type=['json'])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                if 'notes' in data:
                    st.session_state.notes = data['notes']
                if 'flashcards' in data:
                    st.session_state.flashcards = data['flashcards']
                if 'study_sessions' in data:
                    st.session_state.study_sessions = data['study_sessions']
                auto_save()
                st.success("✅ Data imported!")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {str(e)}")

def show_home_page():
    st.title("🎓 Welcome to Your AI Study Platform")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 **Supercharge Your Learning with AI**
        
        Transform your study experience with our comprehensive AI-powered tools:
        
        📝 **Smart Notes** - Generate organized notes from any topic or uploaded content  
        📚 **AI Flashcards** - Create interactive flashcards automatically  
        🧠 **Intelligent Quizzes** - Take personalized quizzes with detailed feedback  
        📊 **Progress Tracking** - Monitor your learning journey with detailed analytics  
        📄 **Study Reports** - Get comprehensive progress reports
        
        ### 🌟 **Why Choose Our Platform?**
        - **100% Free** - Uses DeepSeek AI for unlimited access
        - **No Installation** - Works directly in your browser
        - **Auto-Save** - Your progress is saved automatically
        - **File Upload** - Support for text files and documents
        """)
    
    with col2:
        st.markdown("### 🏃‍♂️ **Quick Start**")
        
        if st.button("📝 Create Notes", use_container_width=True):
            st.session_state.page = "📝 Notes"
            st.rerun()
        
        if st.button("📚 Make Flashcards", use_container_width=True):
            st.session_state.page = "📚 Flashcards"
            st.rerun()
        
        if st.button("🧠 Take Quiz", use_container_width=True):
            st.session_state.page = "🧠 Quizzes"
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.notes or st.session_state.flashcards or st.session_state.study_sessions:
            st.markdown("### 📈 **Recent Activity**")
            
            # Show recent items
            all_items = []
            
            for note in st.session_state.notes[-3:]:
                all_items.append(f"📝 {note.get('title', 'Untitled Note')}")
            
            for session in st.session_state.study_sessions[-3:]:
                activity = session.get('activity_type', 'study')
                if activity == 'quiz':
                    score = session.get('score', 0)
                    all_items.append(f"🧠 Quiz: {score:.1f}%")
                elif activity == 'flashcards':
                    cards = session.get('flashcards_studied', 0)
                    all_items.append(f"📚 Studied {cards} cards")
            
            for item in all_items[-5:]:
                st.write(f"• {item}")

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
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Generate Notes", type="primary", use_container_width=True):
            if user_input.strip():
                with st.spinner("Creating notes with AI..."):
                    try:
                        generated_notes = generators['notes'].generate_notes(
                            user_input, 
                            note_type=note_type,
                            detail_level=detail_level if input_method == "📖 Topic/Subject" else "Intermediate"
                        )
                        
                        # Generate title if not provided
                        if not note_title:
                            note_title = generators['notes'].generate_title(user_input)
                        
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
                            'duration_minutes': 5,
                            'notes_created': 1
                        }
                        st.session_state.study_sessions.append(session)
                        
                        auto_save()
                        
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
                            for card in flashcards:
                                card['category'] = category
                            
                            st.session_state.flashcards.extend(flashcards)
                            auto_save()
                            st.success(f"✅ Generated {len(flashcards)} flashcards!")
                            
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
                        auto_save()
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
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

def show_flashcards_page():
    st.title("📚 AI Flashcards")
    
    if not hasattr(st.session_state, 'flashcards'):
        st.session_state.flashcards = []
    
    tab1, tab2, tab3 = st.tabs(["📖 Study Session", "➕ Create Flashcards", "📚 My Collection"])
    
    with tab1:
        st.subheader("📖 Study Flashcards")
        
        if not st.session_state.flashcards:
            st.info("📝 No flashcards available yet! Create some flashcards first using the Create tab.")
            return
        
        # Study options
        col1, col2 = st.columns(2)
        with col1:
            categories = list(set([card.get('category', 'General') for card in st.session_state.flashcards]))
            selected_category = st.selectbox("Select category:", ["All"] + categories)
        
        with col2:
            difficulty_filter = st.selectbox("Filter by difficulty:", ["All", "Easy", "Medium", "Hard"])
        
        # Filter flashcards
        study_cards = st.session_state.flashcards
        if selected_category != "All":
            study_cards = [card for card in study_cards if card.get('category', 'General') == selected_category]
        if difficulty_filter != "All":
            study_cards = [card for card in study_cards if card.get('difficulty', 'Medium') == difficulty_filter]
        
        if not study_cards:
            st.warning("No flashcards match your filters.")
            return
        
        st.info(f"🎯 {len(study_cards)} flashcards available for study")
        
        # Study session
        if 'study_session_active' not in st.session_state:
            if st.button("🚀 Start Study Session", type="primary"):
                st.session_state.study_session_active = True
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False
                st.session_state.cards_studied = 0
                st.session_state.cards_correct = 0
                st.rerun()
        else:
            # Study session in progress
            current_card = study_cards[st.session_state.current_card_index]
            
            # Progress
            progress = (st.session_state.current_card_index + 1) / len(study_cards)
            st.progress(progress, text=f"Card {st.session_state.current_card_index + 1} of {len(study_cards)}")
            
            # Card display
            st.markdown("---")
            st.markdown("### 🎴 Question")
            st.markdown(f"**{current_card['front']}**")
            
            if st.session_state.show_answer:
                st.markdown("### 💡 Answer")
                st.markdown(f"**{current_card['back']}**")
                
                # Self-assessment buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("❌ Incorrect"):
                        move_to_next_card(study_cards, False)
                with col2:
                    if st.button("✅ Correct"):
                        move_to_next_card(study_cards, True)
                with col3:
                    if st.button("⏭️ Skip"):
                        move_to_next_card(study_cards, False)
                with col4:
                    if st.button("🛑 End Session"):
                        end_flashcard_session()
            else:
                if st.button("👀 Show Answer", type="primary"):
                    st.session_state.show_answer = True
                    st.rerun()
    
    with tab2:
        st.subheader("➕ Create New Flashcards")
        
        # Creation methods
        creation_method = st.radio(
            "Choose creation method:",
            ["📝 AI Generate from Text", "✋ Manual Entry"],
            horizontal=True
        )
        
        if creation_method == "📝 AI Generate from Text":
            content = st.text_area(
                "Enter content to generate flashcards from:",
                placeholder="Paste your study material, notes, or any text content...",
                height=150
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                num_cards = st.slider("Number of cards:", 3, 15, 6)
            with col2:
                difficulty = st.selectbox("Difficulty level:", ["Easy", "Medium", "Hard"])
            with col3:
                category = st.text_input("Category:", value="General")
            
            if st.button("🚀 Generate Flashcards", type="primary"):
                if content.strip():
                    with st.spinner("Creating flashcards with AI..."):
                        try:
                            new_flashcards = generators['flashcards'].generate_flashcards(
                                content, num_cards=num_cards, difficulty=difficulty
                            )
                            
                            # Add metadata
                            for card in new_flashcards:
                                card['category'] = category
                                card['created'] = datetime.now().isoformat()
                                card['id'] = f"ai_{datetime.now().timestamp()}"
                            
                            st.session_state.flashcards.extend(new_flashcards)
                            auto_save()
                            
                            st.success(f"✅ Created {len(new_flashcards)} flashcards!")
                            
                            # Preview created cards
                            with st.expander("📖 Preview Created Cards"):
                                for i, card in enumerate(new_flashcards):
                                    st.write(f"**Card {i+1}:**")
                                    st.write(f"Front: {card['front']}")
                                    st.write(f"Back: {card['back']}")
                                    st.write("---")
                        
                        except Exception as e:
                            st.error(f"Error creating flashcards: {str(e)}")
                else:
                    st.warning("Please enter some content to generate flashcards from.")
        
        else:  # Manual Entry
            st.markdown("#### Create Individual Flashcard")
            
            with st.form("add_flashcard"):
                front_text = st.text_area("Front (Question/Term):", height=100)
                back_text = st.text_area("Back (Answer/Definition):", height=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    card_category = st.text_input("Category:", value="General")
                with col2:
                    card_difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
                
                submitted = st.form_submit_button("➕ Add Flashcard", type="primary")
                
                if submitted and front_text.strip() and back_text.strip():
                    new_card = {
                        'front': front_text.strip(),
                        'back': back_text.strip(),
                        'category': card_category,
                        'difficulty': card_difficulty,
                        'created': datetime.now().isoformat(),
                        'id': f"manual_{datetime.now().timestamp()}"
                    }
                    st.session_state.flashcards.append(new_card)
                    auto_save()
                    st.success("✅ Flashcard added successfully!")
                elif submitted:
                    st.warning("Please fill in both front and back of the flashcard.")
    
    with tab3:
        st.subheader("📚 Flashcard Collection")
        
        if not st.session_state.flashcards:
            st.info("No flashcards yet. Create some first!")
            return
        
        # Collection stats
        total_cards = len(st.session_state.flashcards)
        categories = list(set([card.get('category', 'General') for card in st.session_state.flashcards]))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Cards", total_cards)
        with col2:
            st.metric("Categories", len(categories))
        with col3:
            # Export functionality
            flashcard_data = json.dumps(st.session_state.flashcards, indent=2)
            st.download_button(
                "📥 Export All",
                data=flashcard_data,
                file_name=f"flashcards_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        # Filter and display cards
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_category = st.selectbox("Filter by category:", ["All"] + categories, key="collection_filter")
        
        with filter_col2:
            search_term = st.text_input("🔍 Search cards:", key="collection_search")
        
        # Apply filters
        display_cards = st.session_state.flashcards
        if filter_category != "All":
            display_cards = [card for card in display_cards if card.get('category', 'General') == filter_category]
        if search_term:
            display_cards = [card for card in display_cards if 
                           search_term.lower() in card['front'].lower() or 
                           search_term.lower() in card['back'].lower()]
        
        # Display cards
        for i, card in enumerate(display_cards):
            with st.expander(f"🎴 {card['front'][:50]}... ({card.get('category', 'General')})"):
                st.write(f"**Front:** {card['front']}")
                st.write(f"**Back:** {card['back']}")
                st.write(f"**Category:** {card.get('category', 'General')}")
                st.write(f"**Difficulty:** {card.get('difficulty', 'Medium')}")
                
                if st.button("🗑️ Delete", key=f"delete_card_{i}"):
                    st.session_state.flashcards.remove(card)
                    auto_save()
                    st.rerun()

def move_to_next_card(study_cards, was_correct):
    """Helper function to move to next card"""
    if was_correct:
        st.session_state.cards_correct += 1
    
    st.session_state.cards_studied += 1
    st.session_state.current_card_index += 1
    st.session_state.show_answer = False
    
    if st.session_state.current_card_index >= len(study_cards):
        end_flashcard_session()
    else:
        st.rerun()

def end_flashcard_session():
    """End the flashcard study session"""
    accuracy = (st.session_state.cards_correct / st.session_state.cards_studied) * 100 if st.session_state.cards_studied > 0 else 0
    
    # Save session data
    session = {
        'timestamp': datetime.now().isoformat(),
        'activity_type': 'flashcards',
        'subject': 'Mixed',
        'duration_minutes': 15,
        'flashcards_studied': st.session_state.cards_studied,
        'correct_answers': st.session_state.cards_correct,
        'questions_answered': st.session_state.cards_studied,
        'score': accuracy
    }
    
    if not hasattr(st.session_state, 'study_sessions'):
        st.session_state.study_sessions = []
    
    st.session_state.study_sessions.append(session)
    
    st.success(f"🎉 Study session complete! You studied {st.session_state.cards_studied} cards with {accuracy:.1f}% accuracy!")
    
    # Clean up session state
    for key in ['study_session_active', 'current_card_index', 'show_answer', 'cards_studied', 'cards_correct']:
        if key in st.session_state:
            del st.session_state[key]
    
    auto_save()
    st.rerun()

def show_quizzes_page():
    st.title("🧠 AI Quizzes")
    
    # Initialize the advanced quiz system
    if 'quiz_system' not in st.session_state:
        st.session_state.quiz_system = AdvancedQuizSystem()
    
    # Use the advanced quiz system
    st.session_state.quiz_system.show_quiz_interface()

def show_progress_page():
    st.title("📊 Progress Analytics")
    
    tracker = generators['progress']
    
    if not st.session_state.study_sessions:
        st.info("📈 No study data yet. Start studying to see your progress here!")
        return
    
    # Progress overview
    progress_data = tracker.calculate_progress(st.session_state.study_sessions)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", progress_data['total_sessions'])
    with col2:
        st.metric("Study Time", f"{progress_data['total_hours']:.1f}h")
    with col3:
        st.metric("Average Score", f"{progress_data['avg_score']:.1f}%")
    with col4:
        st.metric("This Week", f"{progress_data['sessions_this_week']} sessions")
    
    # Progress charts
    st.subheader("📈 Performance Trends")
    
    # Score over time chart
    if progress_data['score_trend']:
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        dates = [datetime.fromisoformat(session['timestamp']).date() for session in st.session_state.study_sessions if 'score' in session]
        scores = [session['score'] for session in st.session_state.study_sessions if 'score' in session]
        
        ax.plot(dates, scores, marker='o', linestyle='-', color='#1f77b4')
        ax.set_title('Score Trend Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Score (%)')
        ax.grid(True, alpha=0.3)
        
        st.pyplot(fig)
    
    # Subject breakdown
    st.subheader("📚 Subject Performance")
    
    subjects = {}
    for session in st.session_state.study_sessions:
        subject = session.get('subject', 'General')
        if subject not in subjects:
            subjects[subject] = {'sessions': 0, 'total_score': 0, 'avg_score': 0}
        
        subjects[subject]['sessions'] += 1
        if 'score' in session:
            subjects[subject]['total_score'] += session['score']
    
    for subject in subjects:
        if subjects[subject]['sessions'] > 0:
            subjects[subject]['avg_score'] = subjects[subject]['total_score'] / subjects[subject]['sessions']
    
    if subjects:
        for subject, data in subjects.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{subject}**")
                st.progress(data['avg_score'] / 100)
            with col2:
                st.metric("Avg", f"{data['avg_score']:.1f}%")

def show_reports_page():
    st.title("📄 Study Reports")
    
    if not st.session_state.study_sessions:
        st.info("📄 No study data available yet. Complete some activities to generate reports!")
        return
    
    report_generator = generators['reports']
    
    # Report options
    col1, col2 = st.columns(2)
    
    with col1:
        report_type = st.selectbox(
            "Report Type:",
            ["Complete Progress Report", "Flashcard Collection", "Quiz Performance", "Study Summary"]
        )
    
    with col2:
        time_period = st.selectbox(
            "Time Period:",
            ["All Time", "Last 7 Days", "Last 30 Days", "This Month"]
        )
    
    if st.button("📄 Generate Report", type="primary"):
        with st.spinner("Generating your report..."):
            try:
                if report_type == "Complete Progress Report":
                    pdf_data = report_generator.generate_progress_report(
                        st.session_state.study_sessions,
                        st.session_state.notes,
                        st.session_state.flashcards
                    )
                    
                    st.download_button(
                        "📥 Download Progress Report",
                        data=pdf_data,
                        file_name=f"progress_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                
                elif report_type == "Flashcard Collection":
                    if st.session_state.flashcards:
                        pdf_data = report_generator.export_flashcards_to_pdf(st.session_state.flashcards)
                        
                        st.download_button(
                            "📥 Download Flashcard Collection",
                            data=pdf_data,
                            file_name=f"flashcards_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.warning("No flashcards available to export.")
                
                st.success("✅ Report generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")

# Main app
def main():
    show_sidebar()
    
    # Route to appropriate page
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

if __name__ == "__main__":
    main()