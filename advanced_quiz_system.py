import streamlit as st
import json
import re
from datetime import datetime
from quiz_generator import QuizGenerator


class AdvancedQuizSystem:
    """Enhanced quiz system with comprehensive features"""

    def __init__(self, quiz_generator):
        self.quiz_generator = quiz_generator

        def create_quiz_from_content(self, content, num_questions=10, difficulty="Medium", question_type="Mixed Questions"):
            """Create a quiz from provided content with specified question types"""
            try:
                # Generate quiz from content
                quiz_data = self.quiz_generator.generate_quiz(
                    content=content,
                    num_questions=num_questions,
                    difficulty=difficulty
                )

                if not quiz_data or not isinstance(quiz_data, dict):
                    return None

                questions = quiz_data.get('questions', [])

                # Filter questions based on question_type
                if question_type != "Mixed Questions":
                    question_type_map = {
                        "Multiple Choice Only": "multiple_choice",
                        "True/False Only": "true_false",
                        "Short Answer Only": "short_answer"
                    }
                    target_type = question_type_map.get(question_type)
                    if target_type:
                        questions = [q for q in questions if q.get('type') == target_type]

                # Limit to requested number of questions
                questions = questions[:num_questions]

                formatted_quiz = {
                    'title': quiz_data.get('title', 'Study Quiz'),
                    'description': quiz_data.get('description', 'Test your knowledge'),
                    'questions': [],
                    'metadata': {
                        'created': datetime.now().isoformat(),
                        'difficulty': difficulty,
                        'total_questions': len(questions),
                        'original_content': content,
                        'question_type': question_type
                    }
                }

                for i, q in enumerate(questions):
                    if isinstance(q, dict):
                        formatted_quiz['questions'].append({
                            'id': i + 1,
                            'question': q.get('question', ''),
                            'type': q.get('type', 'multiple_choice'),
                            'options': q.get('options', []),
                            'correct_answer': q.get('correct_answer', ''),
                            'explanation': q.get('explanation', ''),
                            'points': 1
                        })

                return formatted_quiz

            except Exception as e:
                st.error(f"Error creating quiz: {str(e)}")
                return None


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
                'start_time': datetime.now()
            }

        total = len(quiz_data['questions'])
        current = st.session_state.quiz_state['current_question']

        # Quiz header
        st.header(f"📝 {quiz_data['title']}")
        st.caption(f"Question Type: {quiz_data['metadata']['question_type']} | Difficulty: {quiz_data['metadata']['difficulty']}")
        st.write(quiz_data['description'])

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
        """Display a single question"""
        st.subheader(f"Question {index + 1}")
        st.markdown(f"**Type:** {question['type'].replace('_', ' ').title()}")
        st.write(question['question'])

        key = f"q_{index}"

        if question['type'] == 'multiple_choice':
            options = question.get('options', [])
            selected = st.radio("Select answer:", options, key=key, index=None)
            if selected:
                st.session_state.quiz_state['answers'][index] = {
                    'answer': selected,
                    'letter': self._extract_answer_letter(selected)
                }

        elif question['type'] == 'true_false':
            selected = st.radio("Select answer:", ["True", "False"], key=key, index=None)
            if selected:
                st.session_state.quiz_state['answers'][index] = selected

        elif question['type'] in ['short_answer', 'fill_blank']:
            answer = st.text_input("Your answer:", key=key)
            if answer:
                st.session_state.quiz_state['answers'][index] = answer

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
        """Display comprehensive quiz results"""
        st.header("🎉 Quiz Complete!")
        st.subheader(f"Quiz Type: {quiz_data['metadata']['question_type']}")

        total = len(quiz_data['questions'])
        correct = 0
        results = []
        question_types = {}
        time_taken = datetime.now() - st.session_state.quiz_state['start_time']

        for i, q in enumerate(quiz_data['questions']):
            user_answer = st.session_state.quiz_state['answers'].get(i, "No answer")
            is_correct = self._grade_answer(user_answer, q['correct_answer'], q['type'])

            if is_correct:
                correct += 1

            # Track performance by question type
            q_type = q['type']
            if q_type not in question_types:
                question_types[q_type] = {'correct': 0, 'total': 0}
            question_types[q_type]['total'] += 1
            if is_correct:
                question_types[q_type]['correct'] += 1

            results.append({
                'question': q['question'],
                'user_answer': user_answer['answer'] if isinstance(user_answer, dict) else user_answer,
                'correct_answer': q['correct_answer'],
                'is_correct': is_correct,
                'explanation': q.get('explanation', ''),
                'type': q['type'],
                'question_number': i+1
            })

        score = (correct / total) * 100

        # Display score summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{score:.1f}%")
        col2.metric("Correct", f"{correct}/{total}")
        col3.metric("Time Taken", f"{time_taken.seconds//60}m {time_taken.seconds%60}s")

        # Performance insights
        st.subheader("📊 Detailed Performance Analysis")
        
        # Overall performance assessment
        with st.expander("🔍 Overall Performance", expanded=True):
            self._display_performance_analysis(score, question_types, results)
        
        # Question-by-question review
        with st.expander("📝 Question-by-Question Review", expanded=False):
            for r in results:
                with st.container():
                    col1, col2 = st.columns([4,1])
                    with col1:
                        st.write(f"**Q{r['question_number']}:** {r['question']}")
                        st.caption(f"Type: {r['type'].replace('_', ' ').title()}")
                    with col2:
                        st.markdown("**Correct** ✅" if r['is_correct'] else "**Incorrect** ❌")
                    
                    with st.expander(f"View details for Q{r['question_number']}", expanded=False):
                        if not r['is_correct']:
                            st.error(f"❌ Your answer: {r['user_answer']}")
                            st.success(f"✓ Correct answer: {r['correct_answer']}")
                        else:
                            st.success(f"✅ Your answer: {r['user_answer']}")
                        
                        if r['explanation']:
                            st.info(f"💡 Explanation: {r['explanation']}")
                    st.divider()

        # Question type breakdown
        with st.expander("📈 Question Type Breakdown", expanded=False):
            for q_type, stats in question_types.items():
                type_name = q_type.replace('_', ' ').title()
                accuracy = (stats['correct'] / stats['total']) * 100
                
                col1, col2 = st.columns([2,3])
                with col1:
                    st.metric(f"{type_name} Accuracy", f"{accuracy:.1f}%")
                with col2:
                    st.progress(accuracy/100)
            
            # Difficulty adjustment suggestion
            if score > 80 and quiz_data['metadata']['difficulty'] != "Hard":
                st.info("💡 You're doing well! Consider increasing the difficulty next time.")
            elif score < 50 and quiz_data['metadata']['difficulty'] != "Easy":
                st.warning("💡 This was challenging. You might want to try an easier level next time.")

        # Save results
        self._save_quiz_results(quiz_data, results, score, time_taken)

        # Navigation
        col1, col2 = st.columns(2)
        if col1.button("🔄 Retake Quiz", type="primary"):
            self._reset_quiz_state()
            st.session_state.retake_quiz = {
                'content': quiz_data['metadata']['original_content'],
                'num_questions': quiz_data['metadata']['total_questions'],
                'difficulty': quiz_data['metadata']['difficulty'],
                'question_type': quiz_data['metadata']['question_type']
            }
            st.rerun()

        if col2.button("⬅️ Back to Quiz Setup"):
            self._reset_quiz_state()
            st.session_state.quiz_active = False
            st.rerun()

    def _display_performance_analysis(self, score, question_types, results):
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

        # Performance by question type
        st.subheader("By Question Type")
        for q_type, stats in question_types.items():
            type_name = q_type.replace('_', ' ').title()
            accuracy = (stats['correct'] / stats['total']) * 100

            if accuracy >= 80:
                st.success(f"• {type_name}: {accuracy:.1f}% accuracy")
            elif accuracy >= 60:
                st.info(f"• {type_name}: {accuracy:.1f}% accuracy")
            else:
                st.error(f"• {type_name}: {accuracy:.1f}% accuracy")

        # Specific recommendations
        incorrect = [r for r in results if not r['is_correct']]
        if incorrect:
            st.subheader("🔍 Focus Areas")
            st.write("You missed these concepts:")
            for i, r in enumerate(incorrect[:5]):  # Show top 5 missed
                st.write(f"- {r['question'][:100]}...")

        # Study recommendations
        st.subheader("📚 Study Tips")
        if score >= 90:
            st.write("- Challenge yourself with more advanced material")
            st.write("- Help others learn these concepts")
        elif score >= 70:
            st.write("- Review your incorrect answers")
            st.write("- Create flashcards for key concepts")
        else:
            st.write("- Review the foundational concepts")
            st.write("- Practice with similar quizzes")
            st.write("- Study in shorter, more frequent sessions")

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

        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_difficulty = st.selectbox("Filter by difficulty:", ["All"] + sorted(list(set(s['difficulty'] for s in quiz_sessions))))
        with col2:
            filter_type = st.selectbox("Filter by type:", ["All"] + sorted(list(set(s.get('question_type', 'Mixed Questions') for s in quiz_sessions))))
        with col3:
            sort_by = st.selectbox("Sort by:", ["Date (Newest)", "Date (Oldest)", "Score (Highest)", "Score (Lowest)"])

        # Apply filters
        filtered_sessions = quiz_sessions
        if filter_difficulty != "All":
            filtered_sessions = [s for s in filtered_sessions if s['difficulty'] == filter_difficulty]
        if filter_type != "All":
            filtered_sessions = [s for s in filtered_sessions if s.get('question_type', 'Mixed Questions') == filter_type]

        # Apply sorting
        reverse_sort = True
        if sort_by == "Date (Newest)":
            key = lambda x: x['timestamp']
        elif sort_by == "Date (Oldest)":
            key = lambda x: x['timestamp']
            reverse_sort = False
        elif sort_by == "Score (Highest)":
            key = lambda x: x['score']
        else:  # "Score (Lowest)"
            key = lambda x: x['score']
            reverse_sort = False

        filtered_sessions = sorted(filtered_sessions, key=key, reverse=reverse_sort)

        # Recent attempts
        st.subheader("Quiz Attempts")
        for i, session in enumerate(filtered_sessions):
            with st.expander(f"{session['title']} - {session['score']:.1f}% - {session['timestamp'][:10]}"):
                col1, col2 = st.columns([3,1])
                with col1:
                    st.write(f"📅 Date: {session['timestamp'][:10]}")
                    st.write(f"🔢 Score: {session['score']:.1f}% ({session['correct_answers']}/{session['total_questions']})")
                    st.write(f"📊 Difficulty: {session['difficulty']}")
                    st.write(f"❓ Type: {session.get('question_type', 'Mixed Questions')}")
                    st.write(f"⏱️ Time: {session.get('time_taken', 'N/A')}")

                with col2:
                    if st.button("🔄 Retake This Quiz", key=f"retake_{i}"):
                        st.session_state.retake_quiz = {
                            'content': session['original_content'],
                            'num_questions': session['total_questions'],
                            'difficulty': session['difficulty'],
                            'question_type': session.get('question_type', 'Mixed Questions')
                        }
                        st.session_state.page = "🧠 Quizzes"
                        st.session_state.quiz_active = False
                        st.rerun()

    def _extract_answer_letter(self, answer):
        """Extract letter from multiple choice answer"""
        match = re.match(r'^([A-Za-z])[\)\.]?\s*', str(answer).strip())
        return match.group(1).upper() if match else ""

    def _grade_answer(self, user_answer, correct_answer, q_type):
        """Grade a single answer"""
        if not user_answer or user_answer == "No answer":
            return False

        if q_type in ['multiple_choice', 'true_false']:
            if isinstance(user_answer, dict):
                return user_answer['letter'].upper() == str(correct_answer).upper()
            return str(user_answer).upper() == str(correct_answer).upper()

        elif q_type in ['short_answer', 'fill_blank']:
            user_clean = re.sub(r'[^\w\s]', '', str(user_answer).lower().strip())
            correct_clean = re.sub(r'[^\w\s]', '', str(correct_answer).lower().strip())
            return user_clean == correct_clean

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

    def _save_quiz_results(self, quiz_data, results, score, time_taken):
        """Save quiz results to session state"""
        quiz_result = {
            'timestamp': datetime.now().isoformat(),
            'title': quiz_data['title'],
            'score': score,
            'correct_answers': sum(1 for r in results if r['is_correct']),
            'total_questions': len(results),
            'difficulty': quiz_data['metadata']['difficulty'],
            'question_type': quiz_data['metadata'].get('question_type', 'Mixed Questions'),
            'activity_type': 'quiz',
            'original_content': quiz_data['metadata']['original_content'],
            'detailed_results': results,
            'time_taken': f"{time_taken.seconds//60}m {time_taken.seconds%60}s"
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
