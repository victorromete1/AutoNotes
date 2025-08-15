import streamlit as st
import json
import re
import os
from datetime import datetime
from openai import OpenAI

class QuizGenerator:
    def __init__(self):
        """Initialize with API client (supports both OpenAI and OpenRouter)"""
        openai_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        if openrouter_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key
            )
            self.model = "deepseek/deepseek-chat"
        elif openai_key:
            self.client = OpenAI(api_key=openai_key)
            self.model = "gpt-4"
        else:
            st.error("No API key found. Please set OPENAI_API_KEY or OPENROUTER_API_KEY.")
            st.stop()

    def generate_quiz(self, content, quiz_type="multiple_choice", num_questions=5, difficulty="Medium"):
        """Generate quiz based on parameters"""
        try:
            prompt = self._create_prompt(content, quiz_type, num_questions, difficulty)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert quiz creator. Return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            quiz = json.loads(response.choices[0].message.content)
            quiz['metadata'] = {
                'created': datetime.now().isoformat(),
                'type': quiz_type,
                'difficulty': difficulty,
                'total_questions': num_questions
            }
            return quiz
            
        except Exception as e:
            st.error(f"Quiz generation failed: {str(e)}")
            return None

    def _create_prompt(self, content, quiz_type, num_questions, difficulty):
        """Generate the appropriate prompt based on quiz type"""
        type_instructions = {
            "multiple_choice": (
                "Generate multiple choice questions with 4 options each. "
                "Format options as A) Option 1, B) Option 2 etc. "
                "Include exactly one correct answer per question."
            ),
            "true_false": (
                "Generate true/false statements. "
                "Ensure answers are unambiguous."
            ),
            "short_answer": (
                "Generate short answer questions. "
                "Include a sample_answer and key points for grading."
            ),
            "fill_blank": (
                "Generate fill-in-the-blank questions. "
                "Include all acceptable answers for each blank."
            ),
            "mixed": (
                "Generate a mix of question types (multiple choice, true/false, short answer). "
                "Distribute evenly unless specified otherwise."
            )
        }
        
        return f"""
        Create a {num_questions}-question {quiz_type.replace('_', ' ')} quiz about:
        {content}
        
        Difficulty: {difficulty}
        {type_instructions[quiz_type]}
        
        Return valid JSON with:
        - title: Quiz title
        - description: Brief description
        - questions: List of question objects with:
          * question: Text of question
          * type: Question type
          * correct_answer: Correct answer
          * explanation: Why it's correct
          * options: For multiple choice
          * sample_answer: For short answer
          * answers: For fill-in-blank
        """

class AdvancedQuizSystem:
    def __init__(self):
        self.quiz_generator = QuizGenerator()
        self.quiz_types = {
            "Multiple Choice": "multiple_choice",
            "True/False": "true_false",
            "Short Answer": "short_answer",
            "Fill in Blank": "fill_blank",
            "Mixed Types": "mixed"
        }

    def show_settings(self):
        """Display quiz configuration options"""
        st.subheader("⚙️ Quiz Settings")
        
        with st.form("quiz_config"):
            content = st.text_area("Content to quiz on:", height=200)
            
            col1, col2 = st.columns(2)
            with col1:
                num_questions = st.slider("Questions:", 3, 20, 10)
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            
            with col2:
                quiz_type = st.selectbox("Quiz type:", list(self.quiz_types.keys()))
                time_limit = st.checkbox("Enable time limit", False)
                if time_limit:
                    minutes = st.number_input("Minutes:", 1, 120, 30)
            
            if st.form_submit_button("Generate Quiz"):
                if not content.strip():
                    st.error("Please enter content first!")
                else:
                    return {
                        'content': content,
                        'num_questions': num_questions,
                        'difficulty': difficulty,
                        'quiz_type': self.quiz_types[quiz_type],
                        'time_limit': minutes if time_limit else None
                    }
        return None

    def run_quiz(self, quiz_data):
        """Generate and administer the quiz"""
        with st.spinner("Generating your quiz..."):
            quiz = self.quiz_generator.generate_quiz(
                content=quiz_data['content'],
                quiz_type=quiz_data['quiz_type'],
                num_questions=quiz_data['num_questions'],
                difficulty=quiz_data['difficulty']
            )
        
        if not quiz:
            return
        
        # Initialize session state
        if 'quiz_state' not in st.session_state:
            st.session_state.quiz_state = {
                'quiz': quiz,
                'current_question': 0,
                'answers': {},
                'start_time': datetime.now(),
                'completed': False
            }
        
        self._display_quiz()

    def _display_quiz(self):
        """Render the quiz interface"""
        state = st.session_state.quiz_state
        quiz = state['quiz']
        current = state['current_question']
        total = len(quiz['questions'])
        
        # Header
        st.header(f"📝 {quiz['title']}")
        st.caption(quiz['description'])
        
        # Progress
        st.progress((current + 1) / total)
        st.write(f"Question {current + 1} of {total}")
        
        # Current question
        question = quiz['questions'][current]
        self._display_question(question, current)
        
        # Navigation
        cols = st.columns(3)
        if current > 0 and cols[0].button("← Previous"):
            state['current_question'] -= 1
            st.rerun()
            
        if current < total - 1 and cols[1].button("Next →"):
            if current in state['answers']:
                state['current_question'] += 1
                st.rerun()
            else:
                st.warning("Please answer first!")
                
        if current == total - 1 and cols[2].button("Submit Quiz"):
            state['completed'] = True
            st.rerun()
        
        # Time limit display
        if 'time_limit' in quiz.get('metadata', {}):
            self._display_timer(quiz['metadata']['time_limit'])

    def _display_question(self, question, index):
        """Render a question based on its type"""
        st.subheader(f"Question {index + 1}")
        st.markdown(f"**Type:** `{question['type'].replace('_', ' ').title()}`")
        st.write(question['question'])
        
        key = f"q_{index}"
        answer = st.session_state.quiz_state['answers'].get(index)
        
        if question['type'] == 'multiple_choice':
            options = question.get('options', [])
            selected = st.radio("Options:", options, index=None, key=key)
            if selected:
                st.session_state.quiz_state['answers'][index] = {
                    'answer': selected,
                    'letter': self._extract_answer_letter(selected)
                }
        
        elif question['type'] == 'true_false':
            selected = st.radio("True or False?", ["True", "False"], index=None, key=key)
            if selected:
                st.session_state.quiz_state['answers'][index] = selected
        
        elif question['type'] in ['short_answer', 'fill_blank']:
            user_input = st.text_input("Your answer:", key=key)
            if user_input:
                st.session_state.quiz_state['answers'][index] = user_input
        
        if answer:
            st.info("✅ Answered")

    def _display_results(self):
        """Show detailed quiz results"""
        state = st.session_state.quiz_state
        quiz = state['quiz']
        
        st.header("🎯 Quiz Results")
        
        # Calculate score
        total = len(quiz['questions'])
        correct = 0
        results = []
        
        for i, q in enumerate(quiz['questions']):
            user_answer = state['answers'].get(i)
            is_correct = self._grade_answer(user_answer, q)
            
            if is_correct:
                correct += 1
            
            results.append({
                'question': q['question'],
                'user_answer': user_answer,
                'correct_answer': q['correct_answer'],
                'is_correct': is_correct,
                'explanation': q.get('explanation', ''),
                'type': q['type']
            })
        
        score = (correct / total) * 100
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{score:.1f}%")
        col2.metric("Correct", f"{correct}/{total}")
        col3.metric("Grade", self._get_letter_grade(score))
        
        # Detailed review
        with st.expander("📋 Review Questions", expanded=True):
            for i, r in enumerate(results):
                st.subheader(f"Q{i+1}: {r['question']}")
                st.caption(f"Type: {r['type'].replace('_', ' ').title()}")
                
                if r['is_correct']:
                    st.success(f"✅ Your answer: {r['user_answer']}")
                else:
                    st.error(f"❌ Your answer: {r['user_answer']}")
                    st.info(f"Correct answer: {r['correct_answer']}")
                
                if r['explanation']:
                    st.write(f"💡 {r['explanation']}")
                
                st.divider()
        
        # Save results
        self._save_results(quiz, results, score)
        
        # Retake option
        if st.button("🔄 Take New Quiz"):
            st.session_state.clear()
            st.rerun()

    def _grade_answer(self, user_answer, question):
        """Check if answer is correct based on question type"""
        if not user_answer:
            return False
            
        correct = question['correct_answer']
        q_type = question['type']
        
        if q_type == 'multiple_choice':
            if isinstance(user_answer, dict):
                return user_answer['letter'] == self._extract_answer_letter(correct)
            return user_answer == correct
        
        elif q_type == 'true_false':
            return str(user_answer).lower() == str(correct).lower()
        
        elif q_type in ['short_answer', 'fill_blank']:
            user_clean = re.sub(r'[^\w\s]', '', str(user_answer).lower().strip())
            correct_clean = re.sub(r'[^\w\s]', '', str(correct).lower().strip())
            return user_clean == correct_clean
        
        return False

    def _extract_answer_letter(self, answer):
        """Extract option letter from multiple choice answer"""
        match = re.match(r'^([A-Z])[\)\.]?\s*', str(answer).strip())
        return match.group(1) if match else ""

    def _get_letter_grade(self, percentage):
        """Convert percentage to letter grade"""
        if percentage >= 90: return "A"
        elif percentage >= 80: return "B"
        elif percentage >= 70: return "C"
        elif percentage >= 60: return "D"
        else: return "F"

    def _save_results(self, quiz, results, score):
        """Save quiz results to session history"""
        result_data = {
            'title': quiz['title'],
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'correct': sum(1 for r in results if r['is_correct']),
            'total': len(results),
            'difficulty': quiz['metadata']['difficulty'],
            'type': quiz['metadata']['type'],
            'results': results
        }
        
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = []
        st.session_state.quiz_history.append(result_data)

# Main app
def main():
    st.title("🧠 Advanced Quiz System")
    quiz_system = AdvancedQuizSystem()
    
    if 'quiz_state' not in st.session_state:
        params = quiz_system.show_settings()
        if params:
            quiz_system.run_quiz(params)
    else:
        if st.session_state.quiz_state['completed']:
            quiz_system._display_results()
        else:
            quiz_system._display_quiz()

if __name__ == "__main__":
    main()
