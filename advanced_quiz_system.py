import streamlit as st
import json
import re
from datetime import datetime
from quiz_generator import QuizGenerator


class AdvancedQuizSystem:
    """Enhanced quiz system with comprehensive features"""

    def __init__(self, quiz_generator):
        self.quiz_generator = quiz_generator
        self.quiz_types = {
            "Multiple Choice": "multiple_choice",
            "True/False": "true_false",
            "Short Answer": "short_answer",
            "Fill in the Blank": "fill_in_blank",
            "Mixed (All Types)": "mixed"
        }

    def show_quiz_settings(self):
        """Display quiz configuration options"""
        st.subheader("⚙️ Quiz Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            num_questions = st.slider("Number of questions", 3, 20, 10)
            difficulty = st.selectbox(
                "Difficulty level",
                ["Easy", "Medium", "Hard"],
                index=1
            )
        
        with col2:
            selected_types = st.multiselect(
                "Question types",
                list(self.quiz_types.keys()),
                default=["Multiple Choice"]
            )
            
            if "Mixed (All Types)" in selected_types:
                selected_types = list(self.quiz_types.keys())[:-1]  # Exclude "Mixed"
            
            time_limit = st.checkbox("Enable time limit (minutes)", False)
            if time_limit:
                minutes = st.number_input("Minutes", 1, 60, 30)
        
        return {
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_types": [self.quiz_types[t] for t in selected_types],
            "time_limit": minutes if time_limit else None
        }

    def create_quiz_from_content(self, content, num_questions=10, difficulty="Medium", question_types=["multiple_choice"]):
        """Create a quiz from provided content with selected question types"""
        try:
            # For mixed quizzes, distribute questions among types
            if len(question_types) > 1:
                quiz_parts = []
                base_count = num_questions // len(question_types)
                remainder = num_questions % len(question_types)
                
                for i, q_type in enumerate(question_types):
                    count = base_count + (1 if i < remainder else 0)
                    if count > 0:
                        part = self._generate_quiz_part(content, count, difficulty, q_type)
                        if part:
                            quiz_parts.append(part)
                
                # Combine all parts
                if not quiz_parts:
                    return None
                
                combined_quiz = {
                    'title': "Mixed Quiz",
                    'description': f"Test covering {len(question_types)} question types",
                    'questions': [],
                    'metadata': {
                        'created': datetime.now().isoformat(),
                        'difficulty': difficulty,
                        'total_questions': num_questions,
                        'original_content': content,
                        'question_types': question_types
                    }
                }
                
                for part in quiz_parts:
                    combined_quiz['questions'].extend(part['questions'])
                
                return combined_quiz
            else:
                # Single question type quiz
                return self._generate_quiz_part(content, num_questions, difficulty, question_types[0])
                
        except Exception as e:
            st.error(f"Error creating quiz: {str(e)}")
            return None

    def _generate_quiz_part(self, content, num_questions, difficulty, question_type):
        """Generate a quiz of specific type"""
        quiz_data = self.quiz_generator.generate_quiz(
            content=content,
            num_questions=num_questions,
            difficulty=difficulty,
            quiz_type=question_type
        )

        if not quiz_data or not isinstance(quiz_data, dict):
            return None

        formatted_quiz = {
            'title': quiz_data.get('title', f'{question_type.replace("_", " ").title()} Quiz'),
            'description': quiz_data.get('description', 'Test your knowledge'),
            'questions': [],
            'metadata': {
                'created': datetime.now().isoformat(),
                'difficulty': difficulty,
                'total_questions': num_questions,
                'original_content': content,
                'question_types': [question_type]
            }
        }

        for i, q in enumerate(quiz_data.get('questions', [])):
            if isinstance(q, dict):
                question = {
                    'id': i + 1,
                    'question': q.get('question', ''),
                    'type': question_type,
                    'correct_answer': q.get('correct_answer', ''),
                    'explanation': q.get('explanation', ''),
                    'points': 1
                }
                
                # Add type-specific fields
                if question_type == "multiple_choice":
                    question['options'] = q.get('options', [])
                elif question_type == "short_answer":
                    question['sample_answer'] = q.get('sample_answer', '')
                    question['key_points'] = q.get('key_points', [])
                elif question_type == "fill_in_blank":
                    question['answers'] = q.get('answers', [])
                
                formatted_quiz['questions'].append(question)

        return formatted_quiz

    def display_quiz_interface(self, quiz_data):
        """Display the interactive quiz interface"""
        if not quiz_data:
            st.error("No quiz data available")
            return

        # Initialize quiz state if not exists
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = {
                'current_question': 0,
                'answers': {},
                'started': True,
                'completed': False,
                'start_time': datetime.now(),
                'question_types': quiz_data['metadata'].get('question_types', ['multiple_choice'])
            }

        total = len(quiz_data['questions'])
        current = st.session_state.quiz_state['current_question']

        # Quiz header
        st.header(f"📝 {quiz_data['title']}")
        st.write(quiz_data['description'])
        
        # Display question types being used
        if len(st.session_state.quiz_state['question_types']) > 1:
            types_str = ", ".join([t.replace("_", " ").title() for t in st.session_state.quiz_state['question_types']])
            st.caption(f"Question types: {types_str}")

        # Progress
        if st.session_state.quiz_state['completed']:
            progress = 1.0
            status = "Quiz completed!"
        else:
            progress = (current) / total
            status = f"Question {current + 1} of {total}"

        st.progress(progress)
        st.write(status)

        # Display current question or results
        if not st.session_state.quiz_state['completed']:
            self._display_question(quiz_data['questions'][current], current)
            self._display_navigation(total, current)
        else:
            self._display_quiz_results(quiz_data)

    def _display_question(self, question, index):
        """Display a single question with type-specific formatting"""
        st.subheader(f"Question {index + 1}")
        
        # Display question type badge
        q_type = question.get('type', 'multiple_choice')
        type_color = {
            'multiple_choice': 'blue',
            'true_false': 'green',
            'short_answer': 'orange',
            'fill_in_blank': 'purple'
        }.get(q_type, 'gray')
        
        st.markdown(f"**Type:** :{type_color}[{q_type.replace('_', ' ').title()}]")
        st.write(question['question'])

        key = f"q_{index}"

        if q_type == 'multiple_choice':
            options = question.get('options', [])
            selected = st.radio("Select answer:", options, key=key, index=None)
            if selected:
                st.session_state.quiz_state['answers'][index] = {
                    'answer': selected,
                    'letter': self._extract_answer_letter(selected),
                    'type': q_type
                }

        elif q_type == 'true_false':
            selected = st.radio("Select answer:", ["True", "False"], key=key, index=None)
            if selected:
                st.session_state.quiz_state['answers'][index] = {
                    'answer': selected,
                    'type': q_type
                }

        elif q_type in ['short_answer', 'fill_in_blank']:
            answer = st.text_input("Your answer:", key=key)
            if answer:
                st.session_state.quiz_state['answers'][index] = {
                    'answer': answer,
                    'type': q_type
                }

        if index in st.session_state.quiz_state['answers']:
            st.info("🔵 Answered")

    def _display_navigation(self, total, current):
        """Display navigation buttons"""
        col1, col2, col3 = st.columns([1,1,1])

        with col1:
            if current > 0 and st.button("← Previous"):
                st.session_state.quiz_state['current_question'] -= 1
                st.rerun()

        with col2:
            if current < total - 1 and st.button("Next →"):
                if current in st.session_state.quiz_state['answers']:
                    st.session_state.quiz_state['current_question'] += 1
                    st.rerun()
                else:
                    st.warning("Please answer the question first")

        with col3:
            if current == total - 1 and st.button("🏁 Finish Quiz"):
                if current in st.session_state.quiz_state['answers']:
                    st.session_state.quiz_state['completed'] = True
                    st.rerun()
                else:
                    st.warning("Please answer the question first")

    def _display_quiz_results(self, quiz_data):
        """Display comprehensive quiz results with type-specific insights"""
        st.header("🎉 Quiz Complete!")

        total = len(quiz_data['questions'])
        correct = 0
        results = []
        question_types = {}
        type_performance = {}

        # Calculate results and performance by type
        for i, q in enumerate(quiz_data['questions']):
            q_type = q['type']
            user_answer = st.session_state.quiz_state['answers'].get(i, {}).get('answer', "No answer")
            is_correct = self._grade_answer(user_answer, q, q_type)

            if is_correct:
                correct += 1

            # Track performance by question type
            if q_type not in question_types:
                question_types[q_type] = {'correct': 0, 'total': 0}
                type_performance[q_type] = []
            
            question_types[q_type]['total'] += 1
            if is_correct:
                question_types[q_type]['correct'] += 1
            
            type_performance[q_type].append(is_correct)

            results.append({
                'question': q['question'],
                'user_answer': user_answer,
                'correct_answer': q['correct_answer'],
                'is_correct': is_correct,
                'explanation': q.get('explanation', ''),
                'type': q_type,
                'options': q.get('options', []),
                'sample_answer': q.get('sample_answer', '')
            })

        score = (correct / total) * 100

        # Display score summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{score:.1f}%")
        col2.metric("Correct", f"{correct}/{total}")
        col3.metric("Grade", self._get_letter_grade(score))

        # Performance insights
        st.subheader("📊 Performance Insights")
        self._display_performance_analysis(score, question_types, results, type_performance)

        # Detailed review
        with st.expander("📋 Review All Questions", expanded=True):
            for i, r in enumerate(results):
                st.write(f"**Q{i+1}:** {r['question']}")
                st.caption(f"Type: {r['type'].replace('_', ' ').title()}")
                
                if r['is_correct']:
                    st.success(f"✅ Your answer: {r['user_answer']}")
                else:
                    st.error(f"❌ Your answer: {r['user_answer']}")
                    st.info(f"✓ Correct: {r['correct_answer']}")
                
                # Special display for multiple choice with incorrect answers
                if r['type'] == 'multiple_choice' and not r['is_correct']:
                    self._display_mcq_analysis(r['options'], r['correct_answer'], r['user_answer'])
                
                if r.get('explanation'):
                    st.write(f"💡 Explanation: {r['explanation']}")
                
                if r.get('sample_answer') and r['type'] == 'short_answer':
                    st.write(f"📝 Sample answer: {r['sample_answer']}")
                
                st.divider()

        # Save results
        self._save_quiz_results(quiz_data, results, score)

        # Navigation
        col1, col2 = st.columns(2)
        if col1.button("🔄 Retake Quiz", type="primary"):
            self._reset_quiz_state()
            st.session_state.retake_quiz = {
                'content': quiz_data['metadata']['original_content'],
                'num_questions': quiz_data['metadata']['total_questions'],
                'difficulty': quiz_data['metadata']['difficulty'],
                'question_types': quiz_data['metadata']['question_types']
            }
            st.rerun()

        if col2.button("⬅️ Back to Quiz Setup"):
            self._reset_quiz_state()
            st.session_state.quiz_active = False
            st.rerun()

    def _display_mcq_analysis(self, options, correct_answer, user_answer):
        """Provide detailed analysis for multiple choice questions"""
        correct_letter = self._extract_answer_letter(correct_answer)
        user_letter = self._extract_answer_letter(user_answer)
        
        st.subheader("Multiple Choice Analysis")
        
        # Display all options with color coding
        for option in options:
            option_letter = self._extract_answer_letter(option)
            
            if option_letter == correct_letter:
                st.success(f"✅ {option} (Correct Answer)")
            elif option_letter == user_letter:
                st.error(f"❌ {option} (Your Choice)")
            else:
                st.write(f"▪️ {option}")
        
        # Add strategic advice
        st.write("\n**How to improve:**")
        st.write("- Eliminate obviously wrong options first")
        st.write("- Look for qualifiers like 'always', 'never' which often make statements false")
        st.write("- When unsure, choose the most comprehensive option")

    def _display_performance_analysis(self, score, question_types, results, type_performance):
        """Display detailed performance analysis and recommendations"""
        # Overall performance assessment
        if score >= 90:
            st.success("🌟 Outstanding performance! You've mastered this material.")
        elif score >= 80:
            st.info("👍 Strong performance! You understand most concepts well.")
        elif score >= 70:
            st.warning("📚 Good effort. Review these areas to improve:")
        else:
            st.error("💪 Needs improvement. Focus on these fundamentals:")

        # Performance by question type with detailed insights
        st.subheader("By Question Type")
        for q_type, stats in question_types.items():
            type_name = q_type.replace('_', ' ').title()
            accuracy = (stats['correct'] / stats['total']) * 100
            
            col1, col2 = st.columns([2,3])
            with col1:
                if accuracy >= 80:
                    st.success(f"**{type_name}:** {accuracy:.1f}% accuracy")
                elif accuracy >= 60:
                    st.info(f"**{type_name}:** {accuracy:.1f}% accuracy")
                else:
                    st.error(f"**{type_name}:** {accuracy:.1f}% accuracy")
            
            with col2:
                # Type-specific advice
                if q_type == "multiple_choice":
                    st.write("🔍 Review incorrect options to understand distractors")
                elif q_type == "true_false":
                    st.write("🔍 Watch for absolute terms that often make statements false")
                elif q_type == "short_answer":
                    st.write("🔍 Compare your answers with sample responses")
                elif q_type == "fill_in_blank":
                    st.write("🔍 Focus on key terms and vocabulary")

        # Specific recommendations for incorrect answers
        incorrect = [r for r in results if not r['is_correct']]
        if incorrect:
            st.subheader("🔍 Focus Areas")
            st.write("You missed these concepts:")
            for i, r in enumerate(incorrect[:5]):  # Show top 5 missed
                st.write(f"- {r['question'][:100]}...")
                if r['type'] == 'multiple_choice':
                    st.write(f"  You chose: {self._extract_answer_letter(r['user_answer'])} | Correct: {self._extract_answer_letter(r['correct_answer'])}")

        # Study recommendations
        st.subheader("📚 Study Tips")
        if score >= 90:
            st.write("- Challenge yourself with more advanced material")
            st.write("- Help others learn these concepts")
        elif score >= 70:
            st.write("- Review your incorrect answers carefully")
            st.write("- Create flashcards for key concepts")
        else:
            st.write("- Review the foundational concepts thoroughly")
            st.write("- Practice with similar quizzes regularly")
            st.write("- Study in shorter, more frequent sessions")

        # Special section for multiple choice performance
        if "multiple_choice" in question_types:
            mcq_stats = question_types["multiple_choice"]
            if mcq_stats['total'] > 0:
                mcq_accuracy = (mcq_stats['correct'] / mcq_stats['total']) * 100
                if mcq_accuracy < 80:
                    st.subheader("🧠 Multiple Choice Strategy")
                    st.write("Improve your test-taking skills:")
                    st.write("- Read all options before answering")
                    st.write("- Eliminate obviously wrong answers first")
                    st.write("- Watch for 'all of the above' and 'none of the above' options")
                    st.write("- Manage your time to review marked questions")

    def _extract_answer_letter(self, answer):
        """Extract letter from multiple choice answer"""
        if not answer:
            return ""
        match = re.match(r'^([A-Za-z])[\)\.]?\s*', str(answer).strip())
        return match.group(1).upper() if match else ""

    def _grade_answer(self, user_answer, question, q_type):
        """Grade a single answer with type-specific logic"""
        if not user_answer or user_answer == "No answer":
            return False

        correct_answer = question['correct_answer']

        if q_type == 'multiple_choice':
            user_letter = self._extract_answer_letter(user_answer)
            correct_letter = self._extract_answer_letter(correct_answer)
            return user_letter == correct_letter

        elif q_type == 'true_false':
            return str(user_answer).upper() == str(correct_answer).upper()

        elif q_type == 'short_answer':
            # Use AI grading for short answers
            return self.quiz_generator._grade_short_answer(question, user_answer)

        elif q_type == 'fill_in_blank':
            expected_answers = question.get('answers', [])
            user_clean = re.sub(r'[^\w\s]', '', str(user_answer).lower().strip()
            return any(
                re.sub(r'[^\w\s]', '', str(ans).lower().strip()) in user_clean
                for ans in expected_answers
            )

        return False

    def _get_letter_grade(self, percentage):
        """Convert percentage to letter grade"""
        if percentage >= 97: return "A+"
        elif percentage >= 93: return "A"
        elif percentage >= 90: return "A-"
        elif percentage >= 87: return "B+"
        elif percentage >= 83: return "B"
        elif percentage >= 80: return "B-"
        elif percentage >= 77: return "C+"
        elif percentage >= 73: return "C"
        elif percentage >= 70: return "C-"
        elif percentage >= 67: return "D+"
        elif percentage >= 65: return "D"
        else: return "F"

    def _save_quiz_results(self, quiz_data, results, score):
        """Save quiz results to session state"""
        quiz_result = {
            'timestamp': datetime.now().isoformat(),
            'title': quiz_data['title'],
            'score': score,
            'correct_answers': sum(1 for r in results if r['is_correct']),
            'total_questions': len(results),
            'difficulty': quiz_data['metadata']['difficulty'],
            'activity_type': 'quiz',
            'original_content': quiz_data['metadata']['original_content'],
            'question_types': quiz_data['metadata']['question_types'],
            'detailed_results': results
        }

        if 'study_sessions' not in st.session_state:
            st.session_state.study_sessions = []
        st.session_state.study_sessions.append(quiz_result)

    def _reset_quiz_state(self):
        """Reset quiz state"""
        if 'quiz_state' in st.session_state:
            del st.session_state.quiz_state
        if 'retake_quiz' in st.session_state:
            del st.session_state.retake_quiz

    def display_quiz_history(self):
        """Display quiz history with retake functionality"""
        quiz_sessions = [s for s in st.session_state.get('study_sessions', []) 
                        if s.get('activity_type') == 'quiz']

        if not quiz_sessions:
            st.info("No quiz history yet. Complete your first quiz to see results!")
            return

        st.header("📚 Quiz History")

        # Stats summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Quizzes", len(quiz_sessions))
        avg_score = sum(s['score'] for s in quiz_sessions) / len(quiz_sessions)
        col2.metric("Average Score", f"{avg_score:.1f}%")
        best_score = max(s['score'] for s in quiz_sessions)
        col3.metric("Best Score", f"{best_score:.1f}%")

        # Recent attempts
        st.subheader("Recent Attempts")
        for i, session in enumerate(reversed(quiz_sessions[-5:])):  # Show last 5
            with st.expander(f"{session['title']} - {session['score']:.1f}% - {session['timestamp'][:10]}"):
                col1, col2 = st.columns([3,1])
                with col1:
                    st.write(f"📅 Date: {session['timestamp'][:10]}")
                    st.write(f"🔢 Score: {session['score']:.1f}%")
                    st.write(f"✅ Correct: {session['correct_answers']}/{session['total_questions']}")
                    st.write(f"📊 Difficulty: {session['difficulty']}")
                    types_str = ", ".join([t.replace("_", " ").title() for t in session.get('question_types', ['multiple_choice'])])
                    st.write(f"🎚️ Question types: {types_str}")

                with col2:
                    if st.button("🔄 Retake This Quiz", key=f"retake_{i}"):
                        st.session_state.retake_quiz = {
                            'content': session['original_content'],
                            'num_questions': session['total_questions'],
                            'difficulty': session['difficulty'],
                            'question_types': session.get('question_types', ['multiple_choice'])
                        }
                        st.session_state.page = "🧠 Quizzes"
                        st.session_state.quiz_active = False
                        st.rerun()
