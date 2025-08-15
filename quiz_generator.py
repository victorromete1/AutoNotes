import json
import os
from openai import OpenAI
import streamlit as st
from datetime import datetime
import random

class QuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with AI client."""
        # Try OpenRouter first (completely free)
        #openrouter_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_key = st.secrets["OPENAI_API_KEY"]
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if openrouter_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key
            )
            self.model = "deepseek/deepseek-chat"
        elif openai_key:
            self.client = OpenAI(api_key=openai_key)
            self.model = "gpt-4o"
        else:
            st.error("⚠️ No API key found. Please set either OPENROUTER_API_KEY or OPENAI_API_KEY.")
            st.stop()
    
    def generate_quiz(self, content, quiz_type="multiple_choice", num_questions=5, difficulty="Medium"):
        """Generate a quiz from given content."""
        try:
            if quiz_type == "multiple_choice":
                prompt = self._create_mcq_prompt(content, num_questions, difficulty)
            elif quiz_type == "true_false":
                prompt = self._create_tf_prompt(content, num_questions, difficulty)
            elif quiz_type == "short_answer":
                prompt = self._create_sa_prompt(content, num_questions, difficulty)
            elif quiz_type == "fill_in_blank":
                prompt = self._create_fib_prompt(content, num_questions, difficulty)
            else:
                prompt = self._create_mcq_prompt(content, num_questions, difficulty)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator creating effective quizzes. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            quiz_text = response.choices[0].message.content.strip()
            
            # Clean up the response
            if quiz_text.startswith("```json"):
                quiz_text = quiz_text[7:]
            if quiz_text.endswith("```"):
                quiz_text = quiz_text[:-3]
            
            quiz_data = json.loads(quiz_text)
            
            # Add metadata
            quiz_data["quiz_id"] = f"quiz_{datetime.now().timestamp()}"
            quiz_data["created"] = datetime.now().isoformat()
            quiz_data["type"] = quiz_type
            quiz_data["difficulty"] = difficulty
            
            return quiz_data
            
        except json.JSONDecodeError as e:
            st.error(f"Error parsing quiz: {e}")
            return None
        except Exception as e:
            st.error(f"Error generating quiz: {e}")
            return None
    
    def _create_mcq_prompt(self, content, num_questions, difficulty):
        return f"""
        Create a {num_questions}-question multiple choice quiz from this content.
        Difficulty: {difficulty}
        
        Content:
        {content}
        
        Return ONLY valid JSON in this format:
        {{
            "title": "Quiz Title",
            "questions": [
                {{
                    "question": "Question text",
                    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                    "correct_answer": "A",
                    "explanation": "Why this answer is correct"
                }}
            ]
        }}
        """
    
    def _create_tf_prompt(self, content, num_questions, difficulty):
        return f"""
        Create a {num_questions}-question true/false quiz from this content.
        Difficulty: {difficulty}
        
        Content:
        {content}
        
        Return ONLY valid JSON in this format:
        {{
            "title": "True/False Quiz",
            "questions": [
                {{
                    "question": "Statement to evaluate",
                    "correct_answer": "True" or "False",
                    "explanation": "Explanation of the answer"
                }}
            ]
        }}
        """
    
    def _create_sa_prompt(self, content, num_questions, difficulty):
        return f"""
        Create a {num_questions}-question short answer quiz from this content.
        Difficulty: {difficulty}
        
        Content:
        {content}
        
        Return ONLY valid JSON in this format:
        {{
            "title": "Short Answer Quiz",
            "questions": [
                {{
                    "question": "Question text",
                    "sample_answer": "Example correct answer",
                    "key_points": ["Point 1", "Point 2", "Point 3"]
                }}
            ]
        }}
        """
    
    def _create_fib_prompt(self, content, num_questions, difficulty):
        return f"""
        Create a {num_questions}-question fill-in-the-blank quiz from this content.
        Difficulty: {difficulty}
        
        Content:
        {content}
        
        Return ONLY valid JSON in this format:
        {{
            "title": "Fill in the Blank Quiz",
            "questions": [
                {{
                    "question": "Text with _____ blanks to fill",
                    "answers": ["word1", "word2"],
                    "explanation": "Explanation of the answers"
                }}
            ]
        }}
        """
    
    def grade_quiz(self, quiz_data, user_answers):
        """Grade a completed quiz and provide feedback."""
        if not quiz_data or not user_answers:
            return None
        
        total_questions = len(quiz_data.get("questions", []))
        correct_answers = 0
        feedback = []
        
        for i, question in enumerate(quiz_data.get("questions", [])):
            user_answer = user_answers.get(f"q_{i}", "")
            correct_answer = question.get("correct_answer", "")
            
            is_correct = False
            if quiz_data.get("type") == "multiple_choice":
                is_correct = user_answer.upper() == correct_answer.upper()
            elif quiz_data.get("type") == "true_false":
                is_correct = user_answer.lower() == correct_answer.lower()
            elif quiz_data.get("type") == "short_answer":
                # For short answer, we'll use AI to grade
                is_correct = self._grade_short_answer(question, user_answer)
            elif quiz_data.get("type") == "fill_in_blank":
                expected_answers = question.get("answers", [])
                is_correct = any(ans.lower() in user_answer.lower() for ans in expected_answers)
            
            if is_correct:
                correct_answers += 1
            
            feedback.append({
                "question_num": i + 1,
                "question": question.get("question", ""),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
                "sample_answer": question.get("sample_answer", "")
            })
        
        score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        return {
            "score": score,
            "correct": correct_answers,
            "total": total_questions,
            "feedback": feedback,
            "grade_letter": self._get_letter_grade(score),
            "completed_at": datetime.now().isoformat()
        }
    
    def _grade_short_answer(self, question, user_answer):
        """Use AI to grade short answer questions."""
        if not user_answer.strip():
            return False
        
        try:
            prompt = f"""
            Grade this short answer question:
            
            Question: {question.get('question', '')}
            Sample Answer: {question.get('sample_answer', '')}
            Key Points: {', '.join(question.get('key_points', []))}
            
            Student Answer: {user_answer}
            
            Return only "CORRECT" or "INCORRECT" based on whether the student answer covers the main concepts.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fair and accurate grader. Be lenient with minor spelling/grammar issues but strict about content accuracy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().upper()
            return "CORRECT" in result
            
        except Exception:
            return False  # Default to incorrect if grading fails
    
    def _get_letter_grade(self, score):
        """Convert numeric score to letter grade."""
        if score >= 97: return "A+"
        elif score >= 93: return "A"
        elif score >= 90: return "A-"
        elif score >= 87: return "B+"
        elif score >= 83: return "B"
        elif score >= 80: return "B-"
        elif score >= 77: return "C+"
        elif score >= 73: return "C"
        elif score >= 70: return "C-"
        elif score >= 67: return "D+"
        elif score >= 65: return "D"
        else: return "F"
