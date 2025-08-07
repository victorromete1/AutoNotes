import streamlit as st
import json
import re
from datetime import datetime
from quiz_generator import QuizGenerator

class AdvancedQuizSystem:
    """Enhanced quiz system with one-by-one questions and detailed progress tracking"""
    
    def __init__(self, quiz_generator):
        self.quiz_generator = quiz_generator
    
    def create_quiz_from_content(self, content, num_questions=10, difficulty="Medium"):
        """Create a quiz from provided content"""
        try:
            # Generate quiz using existing quiz generator
            quiz_data = self.quiz_generator.generate_quiz(
                content=content,
                num_questions=num_questions,
                difficulty=difficulty
            )
            
            if not quiz_data or not isinstance(quiz_data, dict):
                return None
            
            # Ensure proper format
            formatted_quiz = {
                'title': quiz_data.get('title', 'Study Quiz'),
                'description': quiz_data.get('description', 'Test your knowledge'),
                'questions': [],
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'difficulty': difficulty,
                    'total_questions': num_questions
                }
            }
            
            # Process questions
            questions = quiz_data.get('questions', [])
            for i, q in enumerate(questions):
                if isinstance(q, dict):
                    question = {
                        'id': i + 1,
                        'question': q.get('question', ''),
                        'type': q.get('type', 'multiple_choice'),
                        'options': q.get('options', []),
                        'correct_answer': q.get('correct_answer', ''),
                        'explanation': q.get('explanation', ''),
                        'points': 1
                    }
                    formatted_quiz['questions'].append(question)
            
            return formatted_quiz
            
        except Exception as e:
            st.error(f"Error creating quiz: {str(e)}")
            return None
    
    def display_quiz_interface(self, quiz_data):
        """Display the interactive quiz interface"""
        if not quiz_data:
            st.error("No quiz data available")
            return
        
        # Initialize quiz session state
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
            st.session_state.quiz_answers = {}
            st.session_state.quiz_started = True
            st.session_state.quiz_completed = False
            st.session_state.quiz_start_time = datetime.now()
        
        total_questions = len(quiz_data['questions'])
        current_q = st.session_state.current_question
        
        # Quiz header
        st.header(f"📝 {quiz_data['title']}")
        st.write(quiz_data['description'])
        
        # Progress bar
        progress = (current_q) / total_questions
        st.progress(progress)
        st.write(f"Question {current_q + 1} of {total_questions}")
        
        if current_q < total_questions and not st.session_state.quiz_completed:
            # Display current question
            self._display_question(quiz_data['questions'][current_q], current_q)
            
            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if current_q > 0:
                    if st.button("← Previous", key="prev_btn"):
                        st.session_state.current_question -= 1
                        st.rerun()
            
            with col2:
                if current_q < total_questions - 1:
                    if st.button("Next →", key="next_btn", type="primary"):
                        st.session_state.current_question += 1
                        st.rerun()
            
            with col3:
                if current_q == total_questions - 1:
                    if st.button("🏁 Finish Quiz", key="finish_btn", type="primary"):
                        st.session_state.quiz_completed = True
                        st.rerun()
        
        else:
            # Quiz completed - show results
            self._display_quiz_results(quiz_data)
    
    def _display_question(self, question, question_index):
        """Display a single question with appropriate input method"""
        st.subheader(f"Question {question_index + 1}")
        st.write(question['question'])
        
        question_key = f"q_{question_index}"
        
        if question['type'] == 'multiple_choice':
            # Multiple choice question
            options = question.get('options', [])
            if options:
                selected = st.radio(
                    "Choose your answer:",
                    options,
                    key=question_key,
                    index=None
                )
                if selected:
                    st.session_state.quiz_answers[question_index] = selected
        
        elif question['type'] == 'true_false':
            # True/False question
            selected = st.radio(
                "Choose your answer:",
                ["True", "False"],
                key=question_key,
                index=None
            )
            if selected:
                st.session_state.quiz_answers[question_index] = selected
        
        elif question['type'] == 'short_answer':
            # Short answer question
            answer = st.text_input(
                "Your answer:",
                key=question_key,
                placeholder="Type your answer here..."
            )
            if answer:
                st.session_state.quiz_answers[question_index] = answer
        
        elif question['type'] == 'fill_blank':
            # Fill in the blank
            answer = st.text_input(
                "Fill in the blank:",
                key=question_key,
                placeholder="Your answer..."
            )
            if answer:
                st.session_state.quiz_answers[question_index] = answer
        
        # Show if question is answered
        if question_index in st.session_state.quiz_answers:
            st.success("✅ Answered")
    
    def _display_quiz_results(self, quiz_data):
        """Display comprehensive quiz results and analysis"""
        st.header("🎉 Quiz Complete!")
        
        # Calculate score
        total_questions = len(quiz_data['questions'])
        correct_answers = 0
        detailed_results = []
        
        for i, question in enumerate(quiz_data['questions']):
            user_answer = st.session_state.quiz_answers.get(i, "No answer")
            correct_answer = question['correct_answer']
            
            # Grade the answer
            is_correct = self._grade_answer(user_answer, correct_answer, question['type'])
            if is_correct:
                correct_answers += 1
            
            detailed_results.append({
                'question': question['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', ''),
                'type': question['type']
            })
        
        score_percentage = (correct_answers / total_questions) * 100
        
        # Display overall score
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score", f"{score_percentage:.1f}%")
        with col2:
            st.metric("Correct", f"{correct_answers}/{total_questions}")
        with col3:
            grade = self._get_letter_grade(score_percentage)
            st.metric("Grade", grade)
        
        # Performance analysis
        st.subheader("📊 Performance Analysis")
        
        if score_percentage >= 90:
            st.success("🌟 Excellent work! You have a strong understanding of the material.")
        elif score_percentage >= 80:
            st.info("👍 Good job! You understand most concepts well.")
        elif score_percentage >= 70:
            st.warning("📚 Fair performance. Review the areas you missed.")
        else:
            st.error("💪 Keep studying! Focus on the fundamentals.")
        
        # Specific improvement recommendations
        self._show_improvement_recommendations(detailed_results, score_percentage)
        
        # Detailed question review
        with st.expander("📋 Review All Questions"):
            for i, result in enumerate(detailed_results):
                st.write(f"**Question {i+1}:** {result['question']}")
                
                if result['is_correct']:
                    st.success(f"✅ Your answer: {result['user_answer']}")
                else:
                    st.error(f"❌ Your answer: {result['user_answer']}")
                    st.info(f"✓ Correct answer: {result['correct_answer']}")
                
                if result['explanation']:
                    st.write(f"💡 Explanation: {result['explanation']}")
                
                st.divider()
        
        # Save quiz results
        self._save_quiz_results(quiz_data, detailed_results, score_percentage)
        
        # Comparison with previous quizzes
        self._show_progress_comparison()
        
        # Reset quiz button
        if st.button("🔄 Take Another Quiz", type="primary"):
            self._reset_quiz_state()
            st.rerun()
    
    def _grade_answer(self, user_answer, correct_answer, question_type):
        """Grade a single answer based on question type"""
        if not user_answer or user_answer == "No answer":
            return False
        
        if question_type in ['multiple_choice', 'true_false']:
            return str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        
        elif question_type in ['short_answer', 'fill_blank']:
            # More flexible grading for text answers
            user_clean = re.sub(r'[^\w\s]', '', str(user_answer).lower().strip())
            correct_clean = re.sub(r'[^\w\s]', '', str(correct_answer).lower().strip())
            
            # Check for exact match or key words
            if user_clean == correct_clean:
                return True
            
            # Check if user answer contains key terms from correct answer
            correct_words = correct_clean.split()
            user_words = user_clean.split()
            
            if len(correct_words) <= 3:
                # For short answers, require exact match
                return user_clean == correct_clean
            else:
                # For longer answers, check if major terms are present
                matches = sum(1 for word in correct_words if word in user_words)
                return matches >= len(correct_words) * 0.6
        
        return False
    
    def _get_letter_grade(self, percentage):
        """Convert percentage to letter grade"""
        if percentage >= 97:
            return "A+"
        elif percentage >= 93:
            return "A"
        elif percentage >= 90:
            return "A-"
        elif percentage >= 87:
            return "B+"
        elif percentage >= 83:
            return "B"
        elif percentage >= 80:
            return "B-"
        elif percentage >= 77:
            return "C+"
        elif percentage >= 73:
            return "C"
        elif percentage >= 70:
            return "C-"
        elif percentage >= 67:
            return "D+"
        elif percentage >= 65:
            return "D"
        else:
            return "F"
    
    def _show_improvement_recommendations(self, detailed_results, score_percentage):
        """Show specific recommendations for improvement"""
        st.subheader("🎯 Specific Improvement Areas")
        
        # Analyze question types performance
        question_types = {}
        for result in detailed_results:
            q_type = result['type']
            if q_type not in question_types:
                question_types[q_type] = {'correct': 0, 'total': 0}
            
            question_types[q_type]['total'] += 1
            if result['is_correct']:
                question_types[q_type]['correct'] += 1
        
        # Show performance by question type
        for q_type, stats in question_types.items():
            accuracy = (stats['correct'] / stats['total']) * 100
            type_name = q_type.replace('_', ' ').title()
            
            if accuracy < 70:
                st.warning(f"📌 **{type_name} Questions**: {accuracy:.1f}% accuracy - Need more practice")
            elif accuracy < 85:
                st.info(f"📌 **{type_name} Questions**: {accuracy:.1f}% accuracy - Good progress")
            else:
                st.success(f"📌 **{type_name} Questions**: {accuracy:.1f}% accuracy - Strong performance")
        
        # Specific recommendations
        incorrect_answers = [r for r in detailed_results if not r['is_correct']]
        
        if len(incorrect_answers) > 0:
            st.write("**Recommended Study Areas:**")
            for i, result in enumerate(incorrect_answers[:5]):  # Show up to 5 recommendations
                st.write(f"• Review: {result['question'][:100]}...")
        
        # General study tips based on performance
        if score_percentage < 70:
            st.write("**Study Tips:**")
            st.write("• Review fundamental concepts thoroughly")
            st.write("• Create additional flashcards for weak areas")
            st.write("• Practice with similar content")
            st.write("• Consider studying with a partner or group")
    
    def _save_quiz_results(self, quiz_data, detailed_results, score_percentage):
        """Save quiz results to session state"""
        quiz_result = {
            'timestamp': datetime.now().isoformat(),
            'title': quiz_data['title'],
            'score': score_percentage,
            'correct_answers': sum(1 for r in detailed_results if r['is_correct']),
            'total_questions': len(detailed_results),
            'difficulty': quiz_data.get('metadata', {}).get('difficulty', 'Medium'),
            'activity_type': 'quiz',
            'subject': 'General',  # Could be improved to detect subject
            'detailed_results': detailed_results
        }
        
        # Add to study sessions
        if 'study_sessions' not in st.session_state:
            st.session_state.study_sessions = []
        
        st.session_state.study_sessions.append(quiz_result)
        
        # Auto-save the data
        try:
            from data_persistence import DataPersistence
            persistence = DataPersistence()
            persistence.auto_save_data()
        except:
            pass  # Silent fail to avoid disrupting user experience
    
    def _show_progress_comparison(self):
        """Show comparison with previous quiz attempts"""
        if len(st.session_state.get('study_sessions', [])) < 2:
            return
        
        quiz_sessions = [s for s in st.session_state.study_sessions if s.get('activity_type') == 'quiz']
        
        if len(quiz_sessions) >= 2:
            st.subheader("📈 Progress Comparison")
            
            # Get last few quiz scores
            recent_scores = [s['score'] for s in quiz_sessions[-5:]]
            current_score = recent_scores[-1]
            previous_score = recent_scores[-2] if len(recent_scores) >= 2 else None
            
            if previous_score is not None:
                improvement = current_score - previous_score
                
                if improvement > 0:
                    st.success(f"📈 Improved by {improvement:.1f}% from your last quiz!")
                elif improvement < 0:
                    st.info(f"📉 Score dropped by {abs(improvement):.1f}% - keep practicing!")
                else:
                    st.info("🎯 Same score as last time - consistent performance!")
            
            # Show average performance
            avg_score = sum(recent_scores) / len(recent_scores)
            st.metric("Recent Average", f"{avg_score:.1f}%")
            
            if len(recent_scores) >= 3:
                # Show trend
                if recent_scores[-1] > recent_scores[-3]:
                    st.success("📊 Overall upward trend in your scores!")
                elif recent_scores[-1] < recent_scores[-3]:
                    st.warning("📊 Consider reviewing previous material to strengthen fundamentals")
    
    def _reset_quiz_state(self):
        """Reset quiz-related session state"""
        keys_to_reset = [
            'current_question', 'quiz_answers', 'quiz_started', 
            'quiz_completed', 'quiz_start_time'
        ]
        
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
    
    def upload_content_for_quiz(self):
        """Handle content upload for quiz generation"""
        st.subheader("📤 Upload Content for Quiz")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload a file to create quiz from:",
            type=['txt', 'md', 'pdf', 'docx'],
            help="Upload text files, PDFs, or Word documents"
        )
        
        content = ""
        if uploaded_file:
            try:
                if uploaded_file.type == "text/plain":
                    content = str(uploaded_file.read(), "utf-8")
                elif uploaded_file.type == "text/markdown":
                    content = str(uploaded_file.read(), "utf-8")
                else:
                    st.warning("PDF and DOCX support coming soon. Please convert to text format.")
                    return None
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                return None
        
        # Text input as alternative
        text_content = st.text_area(
            "Or paste content directly:",
            value=content,
            height=200,
            placeholder="Paste your study material here..."
        )
        
        if text_content.strip():
            return text_content
        
        return None