import streamlit as st
import json
import re
import os
from datetime import datetime
from openai import OpenAI

class QuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with API client"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"  # Default model

    def generate_quiz(self, content, num_questions=5, difficulty="Medium", quiz_type="multiple_choice"):
        """Generate quiz questions based on parameters"""
        prompt = self._create_prompt(content, num_questions, difficulty, quiz_type)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return self._parse_response(response.choices[0].message.content, quiz_type)
        except Exception as e:
            st.error(f"Quiz generation failed: {str(e)}")
            return None

    def _create_prompt(self, content, num_questions, difficulty, quiz_type):
        """Generate the prompt for the AI based on quiz type"""
        type_instructions = {
            "multiple_choice": "Generate multiple choice questions with 4 options each",
            "true_false": "Generate true/false statements",
            "short_answer": "Generate short answer questions with sample answers",
            "fill_blank": "Generate fill-in-the-blank questions"
        }
        
        return f"""
        Create a {num_questions}-question {quiz_type.replace('_', ' ')} quiz about:
        {content}
        
        Difficulty: {difficulty}
        {type_instructions[quiz_type]}
        
        Return ONLY valid JSON in this format:
        {{
            "title": "Quiz Title",
            "questions": [
                {{
                    "question": "Question text",
                    "type": "{quiz_type}",
                    "correct_answer": "Correct answer",
                    {'"options": ["A) Option 1", "B) Option 2", ...],' if quiz_type == "multiple_choice" else ''}
                    {'"sample_answer": "Example answer",' if quiz_type == "short_answer" else ''}
                    "explanation": "Brief explanation"
                }}
            ]
        }}
        """

class AdvancedQuizSystem:
    def __init__(self):
        self.quiz_generator = QuizGenerator()
        self.quiz_types = {
            "Multiple Choice": "multiple_choice",
            "True/False": "true_false", 
            "Short Answer": "short_answer",
            "Fill in Blank": "fill_blank"
        }

    def show_quiz_options(self):
        """Display quiz configuration form"""
        with st.form("quiz_options"):
            st.subheader("📝 Quiz Configuration")
            
            # User inputs
            content = st.text_area("Content to generate quiz about:", height=150)
            num_questions = st.slider("Number of questions:", 3, 20, 10)
            difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"])
            quiz_type = st.radio("Quiz type:", list(self.quiz_types.keys()))
            
            if st.form_submit_button("Generate Quiz"):
                if not content.strip():
                    st.error("Please enter some content first!")
                else:
                    return {
                        "content": content,
                        "num_questions": num_questions,
                        "difficulty": difficulty,
                        "quiz_type": self.quiz_types[quiz_type]
                    }
        return None

    def run_quiz(self, quiz_data):
        """Generate and display the quiz"""
        if not quiz_data:
            return
        
        # Generate quiz
        with st.spinner("Generating your quiz..."):
            quiz = self.quiz_generator.generate_quiz(
                content=quiz_data["content"],
                num_questions=quiz_data["num_questions"],
                difficulty=quiz_data["difficulty"],
                quiz_type=quiz_data["quiz_type"]
            )
        
        if not quiz:
            st.error("Failed to generate quiz")
            return
        
        # Display quiz
        st.session_state.quiz = quiz
        st.session_state.answers = {}
        st.session_state.current_question = 0
        
        self._display_quiz()

    def _display_quiz(self):
        """Render the quiz interface"""
        quiz = st.session_state.quiz
        current_q = st.session_state.current_question
        total_q = len(quiz["questions"])
        
        # Header
        st.header(quiz["title"])
        st.write(f"**Question {current_q+1} of {total_q}**")
        
        # Current question
        question = quiz["questions"][current_q]
        self._display_question(question)
        
        # Navigation
        col1, col2 = st.columns(2)
        if current_q > 0 and col1.button("← Previous"):
            st.session_state.current_question -= 1
            st.rerun()
            
        if current_q < total_q-1 and col2.button("Next →"):
            self._save_answer()
            st.session_state.current_question += 1
            st.rerun()
        elif current_q == total_q-1 and col2.button("Submit Quiz"):
            self._save_answer()
            self._show_results()
    
    def _display_question(self, question):
        """Render a single question based on type"""
        st.subheader(question["question"])
        
        if question["type"] == "multiple_choice":
            options = question.get("options", [])
            selected = st.radio("Select answer:", options, key=f"q_{question['id']}")
            st.session_state.temp_answer = selected
            
        elif question["type"] == "true_false":
            selected = st.radio("True or False?", ["True", "False"], key=f"q_{question['id']}")
            st.session_state.temp_answer = selected
            
        elif question["type"] in ["short_answer", "fill_blank"]:
            answer = st.text_input("Your answer:", key=f"q_{question['id']}")
            st.session_state.temp_answer = answer

    def _save_answer(self):
        """Store the user's answer"""
        current_q = st.session_state.current_question
        st.session_state.answers[current_q] = st.session_state.temp_answer

    def _show_results(self):
        """Calculate and display results"""
        quiz = st.session_state.quiz
        score = 0
        
        st.header("📊 Quiz Results")
        
        for i, question in enumerate(quiz["questions"]):
            user_answer = st.session_state.answers.get(i, "No answer")
            is_correct = self._check_answer(user_answer, question)
            
            if is_correct:
                score += 1
            
            with st.expander(f"Question {i+1}: {question['question']}"):
                if is_correct:
                    st.success(f"✅ Your answer: {user_answer}")
                else:
                    st.error(f"❌ Your answer: {user_answer}")
                    st.info(f"Correct answer: {question['correct_answer']}")
                
                if question.get("explanation"):
                    st.write(f"💡 {question['explanation']}")
        
        # Final score
        st.subheader(f"Score: {score}/{len(quiz['questions']} ({score/len(quiz['questions']*100:.0f}%)")
        
        if st.button("🔄 Take New Quiz"):
            st.session_state.clear()
            st.rerun()

    def _check_answer(self, user_answer, question):
        """Check if answer is correct based on question type"""
        if question["type"] == "multiple_choice":
            return user_answer == question["correct_answer"]
        elif question["type"] == "true_false":
            return str(user_answer).lower() == str(question["correct_answer"]).lower()
        else:  # short_answer or fill_blank
            user_clean = re.sub(r'[^\w\s]', '', str(user_answer).lower().strip())
            correct_clean = re.sub(r'[^\w\s]', '', str(question["correct_answer"]).lower().strip())
            return user_clean == correct_clean

# Main app
def main():
    st.title("🧠 Smart Quiz Generator")
    quiz_system = AdvancedQuizSystem()
    
    if "quiz" not in st.session_state:
        quiz_params = quiz_system.show_quiz_options()
        if quiz_params:
            quiz_system.run_quiz(quiz_params)
    else:
        quiz_system._display_quiz()

if __name__ == "__main__":
    main()
