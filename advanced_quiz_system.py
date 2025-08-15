import streamlit as st
import json
import re
from datetime import datetime
from quiz_generator import QuizGenerator


class AdvancedQuizSystem:
    """Enhanced quiz system with comprehensive features"""

    def __init__(self, quiz_generator):
        self.quiz_generator = quiz_generator
        self.question_types = {
            "Multiple Choice": "multiple_choice",
            "True/False": "true_false",
            "Short Answer": "short_answer",
            "Fill in the Blank": "fill_blank",
            "Mixed (All Types)": "mixed"
        }

    def create_quiz_from_content(self, content, num_questions=10, difficulty="Medium", question_type="mixed"):
        """Create a quiz from provided content with specified question types"""
        try:
            # Convert display name to internal type
            internal_type = self.question_types.get(question_type, "mixed")
            
            quiz_data = self.quiz_generator.generate_quiz(
                content=content,
                num_questions=num_questions,
                difficulty=difficulty,
                question_type=internal_type)

            if not quiz_data or not isinstance(quiz_data, dict):
                return None

            formatted_quiz = {
                'title': quiz_data.get('title', 'Study Quiz'),
                'description': quiz_data.get('description', 'Test your knowledge'),
                'questions': [],
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'difficulty': difficulty,
                    'total_questions': num_questions,
                    'original_content': content,
                    'question_type': question_type
                }
            }

            for i, q in enumerate(quiz_data.get('questions', [])):
                if isinstance(q, dict):
                    formatted_quiz['questions'].append({
                        'id': i + 1,
                        'question': q.get('question', ''),
                        'type': q.get('type', 'multiple_choice'),
                        'options': q.get('options', []),
                        'correct_answer': q.get('correct_answer', ''),
                        'explanation': q.get('explanation', ''),
                        'points': 1,
                        'time_spent': 0  # Track time spent per question
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
                'start_time': datetime.now(),
                'question_times': [0] * len(quiz_data['questions'])
            }

        total = len(quiz_data['questions'])
        current = st.session_state.quiz_state['current_question']

        # Quiz header
        st.header(f"📝 {quiz_data['title']}")
        st.write(quiz_data['description'])

        # Display question type badge
        question_type = quiz_data['metadata'].get('question_type', 'Mixed')
        st.markdown(f"**Question Type:** `{question_type}` | **Difficulty:** `{quiz_data['metadata']['difficulty']}`")

        # Progress
        if st.session_state.quiz_state['completed']:
            progress = 1.0
            status = "Quiz completed!"
        else:
            progress = (current) / total
            status = f"Question {current + 1} of {total}"

        st.progress(progress)
        st.write(status)

        # Timer display
        elapsed = (datetime.now() - st.session_state.quiz_state['start_time']).seconds
        st.caption(f"⏱️ Elapsed time: {elapsed // 60}m {elapsed % 60}s")

        # Display current question or results
        if not st.session_state.quiz_state['completed']:
            self._display_question(quiz_data['questions'][current], current)
            self._display_navigation(total, current)
        else:
            self._display_quiz_results(quiz_data)

    def _display_question(self, question, index):
        """Display a single question with time tracking"""
        st.subheader(f"Question {index + 1}")
        
        # Question type badge
        q_type = question['type'].replace('_', ' ').title()
        st.markdown(f"`{q_type}` | `{question['points']} point{'s' if question['points'] > 1 else ''}`")
        
        st.write(question['question'])

        key = f"q_{index}"

        # Start time tracking for this question
        if f"q_{index}_start" not in st.session_state:
            st.session_state[f"q_{index}_start"] = datetime.now()

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

        # Update time spent on this question
        if f"q_{index}_start" in st.session_state:
            time_spent = (datetime.now() - st.session_state[f"q_{index}_start"]).seconds
            st.session_state.quiz_state['question_times'][index] = time_spent
            st.caption(f"Time spent: {time_spent}s")

        if index in st.session_state.quiz_state['answers']:
            st.info("🔵 Answered")

    def _display_quiz_results(self, quiz_data):
        """Display comprehensive quiz results with enhanced analytics"""
        st.header("🎉 Quiz Complete!")
        
        total = len(quiz_data['questions'])
        correct = 0
        results = []
        question_types = {}
        time_stats = {
            'total': sum(st.session_state.quiz_state['question_times']),
            'average': sum(st.session_state.quiz_state['question_times']) / total if total > 0 else 0,
            'per_question': st.session_state.quiz_state['question_times']
        }

        for i, q in enumerate(quiz_data['questions']):
            user_answer = st.session_state.quiz_state['answers'].get(i, "No answer")
            is_correct = self._grade_answer(user_answer, q['correct_answer'], q['type'])

            if is_correct:
                correct += 1

            # Track performance by question type
            q_type = q['type']
            if q_type not in question_types:
                question_types[q_type] = {'correct': 0, 'total': 0, 'time_spent': []}
            question_types[q_type]['total'] += 1
            question_types[q_type]['time_spent'].append(time_stats['per_question'][i])
            if is_correct:
                question_types[q_type]['correct'] += 1

            results.append({
                'question': q['question'],
                'user_answer': user_answer['answer'] if isinstance(user_answer, dict) else user_answer,
                'correct_answer': q['correct_answer'],
                'is_correct': is_correct,
                'explanation': q.get('explanation', ''),
                'type': q['type'],
                'time_spent': time_stats['per_question'][i],
                'question_number': i+1
            })

        score = (correct / total) * 100
        elapsed_time = (datetime.now() - st.session_state.quiz_state['start_time']).seconds

        # Display score summary
        st.subheader("📊 Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score", f"{score:.1f}%")
        col2.metric("Correct", f"{correct}/{total}")
        col3.metric("Grade", self._get_letter_grade(score))
        col4.metric("Total Time", f"{elapsed_time//60}m {elapsed_time%60}s")

        # Performance breakdown
        st.subheader("📈 Performance Breakdown")
        
        # Overall performance assessment
        with st.expander("🔍 Overall Performance", expanded=True):
            self._display_performance_analysis(score, question_types, results)
        
        # Question type performance
        with st.expander("📚 By Question Type", expanded=False):
            self._display_question_type_analysis(question_types)
        
        # Time analysis
        with st.expander("⏱ Time Analysis", expanded=False):
            self._display_time_analysis(time_stats, results)
        
        # Detailed question review
        with st.expander("📝 Question Review", expanded=False):
            self._display_detailed_question_review(results)

        # Save results
        self._save_quiz_results(quiz_data, results, score, time_stats)

        # Navigation buttons
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
        """Display detailed performance analysis"""
        st.write(f"**Overall Score:** {score:.1f}%")
        
        # Performance gauge
        gauge_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
        st.markdown(f"""
        <div style="background: linear-gradient(to right, #f0f0f0, #f0f0f0 {score}%, white {score}%);
                    height: 20px; border-radius: 10px; position: relative; margin: 10px 0;">
            <div style="position: absolute; left: {score}%; top: -5px; width: 2px; height: 30px; background: {gauge_color};"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Performance assessment
        if score >= 90:
            st.success("🌟 Outstanding performance! You've mastered this material.")
        elif score >= 80:
            st.info("👍 Strong performance! You understand most concepts well.")
        elif score >= 70:
            st.warning("📚 Good effort. Review these areas to improve:")
        else:
            st.error("💪 Needs improvement. Focus on these fundamentals:")
        
        # Incorrect questions analysis
        incorrect = [r for r in results if not r['is_correct']]
        if incorrect:
            st.write("**Most Challenging Questions:**")
            for i, r in enumerate(incorrect[:3]):  # Show top 3 most challenging
                st.write(f"- Question {r['question_number']}: {r['question'][:100]}...")
                st.write(f"  Your answer: {r['user_answer']} | Correct: {r['correct_answer']}")

    def _display_question_type_analysis(self, question_types):
        """Display performance analysis by question type"""
        for q_type, stats in question_types.items():
            type_name = q_type.replace('_', ' ').title()
            accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            avg_time = sum(stats['time_spent']) / len(stats['time_spent']) if stats['time_spent'] else 0
            
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"**{type_name}** ({stats['total']} questions)")
                st.progress(accuracy/100)
            
            with col2:
                st.write(f"{accuracy:.1f}%")
                st.caption(f"⏱️ {avg_time:.1f}s avg")
            
            st.write("")

    def _display_time_analysis(self, time_stats, results):
        """Display time spent analysis"""
        st.write(f"**Total Time:** {time_stats['total']} seconds")
        st.write(f"**Average per Question:** {time_stats['average']:.1f} seconds")
        
        # Fastest and slowest questions
        if results:
            fastest = min(results, key=lambda x: x['time_spent'])
            slowest = max(results, key=lambda x: x['time_spent'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("⚡ **Fastest Question**")
                st.write(f"Q{fastest['question_number']}: {fastest['time_spent']}s")
                st.write(fastest['question'][:50] + "...")
            
            with col2:
                st.write("🐢 **Slowest Question**")
                st.write(f"Q{slowest['question_number']}: {slowest['time_spent']}s")
                st.write(slowest['question'][:50] + "...")
        
        # Time vs correctness analysis
        correct_times = [r['time_spent'] for r in results if r['is_correct']]
        incorrect_times = [r['time_spent'] for r in results if not r['is_correct']]
        
        if correct_times and incorrect_times:
            avg_correct = sum(correct_times)/len(correct_times)
            avg_incorrect = sum(incorrect_times)/len(incorrect_times)
            st.write(f"⏱️ **Correct answers took:** {avg_correct:.1f}s avg")
            st.write(f"⏱️ **Incorrect answers took:** {avg_incorrect:.1f}s avg")

    def _display_detailed_question_review(self, results):
        """Display detailed review of each question with expandable sections"""
        for r in results:
            with st.expander(f"Question {r['question_number']} ({r['type'].replace('_', ' ').title()}) - {'✅ Correct' if r['is_correct'] else '❌ Incorrect'}", expanded=False):
                st.write(f"**Question:** {r['question']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Your Answer:** {r['user_answer']}")
                with col2:
                    st.write(f"**Time Spent:** {r['time_spent']} seconds")
                
                if not r['is_correct']:
                    st.error(f"**Correct Answer:** {r['correct_answer']}")
                
                if r['explanation']:
                    st.info(f"**Explanation:** {r['explanation']}")
                
                # Add space for user notes
                note_key = f"note_{r['question_number']}"
                user_note = st.text_area("Add your own notes about this question:", key=note_key)
                if user_note:
                    r['user_note'] = user_note

    def _save_quiz_results(self, quiz_data, results, score, time_stats):
        """Save quiz results to session state with time tracking"""
        quiz_result = {
            'timestamp': datetime.now().isoformat(),
            'title': quiz_data['title'],
            'score': score,
            'correct_answers': sum(1 for r in results if r['is_correct']),
            'total_questions': len(results),
            'difficulty': quiz_data['metadata']['difficulty'],
            'activity_type': 'quiz',
            'original_content': quiz_data['metadata']['original_content'],
            'question_type': quiz_data['metadata']['question_type'],
            'time_spent': time_stats['total'],
            'detailed_results': results,
            'performance_by_type': {
                q_type: {
                    'correct': stats['correct'],
                    'total': stats['total'],
                    'accuracy': (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0,
                    'avg_time': sum(stats['time_spent']) / len(stats['time_spent']) if stats['time_spent'] else 0
                }
                for q_type, stats in self._get_question_type_stats(results).items()
            }
        }

        if 'study_sessions' not in st.session_state:
            st.session_state.study_sessions = []
        st.session_state.study_sessions.append(quiz_result)

    def _get_question_type_stats(self, results):
        """Calculate statistics by question type"""
        stats = {}
        for r in results:
            q_type = r['type']
            if q_type not in stats:
                stats[q_type] = {'correct': 0, 'total': 0, 'time_spent': []}
            stats[q_type]['total'] += 1
            stats[q_type]['time_spent'].append(r['time_spent'])
            if r['is_correct']:
                stats[q_type]['correct'] += 1
        return stats

    # ... (keep all other existing methods unchanged) ...
