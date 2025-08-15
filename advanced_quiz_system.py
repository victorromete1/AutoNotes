import openai
import json
import re
from typing import Dict, List, Optional

class QuizGenerator:
    """Generates quizzes from content with configurable question types and difficulty"""
    
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.question_type_mapping = {
            "multiple_choice": "multiple choice questions",
            "true_false": "true/false questions",
            "short_answer": "short answer questions",
            "mixed": "a mix of multiple choice, true/false, and short answer questions"
        }
        
        self.difficulty_mapping = {
            "easy": "basic level",
            "medium": "intermediate level",
            "hard": "advanced level"
        }

    def generate_quiz(
        self,
        content: str,
        num_questions: int = 8,
        difficulty: str = "medium",
        question_type: str = "mixed"
    ) -> Optional[Dict]:
        """Generate quiz questions from content with specified parameters"""
        
        # Validate inputs
        if not content.strip():
            raise ValueError("Content cannot be empty")
            
        if num_questions < 1 or num_questions > 20:
            raise ValueError("Number of questions must be between 1 and 20")
            
        difficulty = difficulty.lower()
        if difficulty not in self.difficulty_mapping:
            raise ValueError(f"Invalid difficulty level: {difficulty}")
            
        question_type = question_type.lower()
        if question_type not in self.question_type_mapping:
            raise ValueError(f"Invalid question type: {question_type}")

        try:
            prompt = self._build_prompt(content, num_questions, difficulty, question_type)
            response = self._get_completion(prompt)
            return self._parse_response(response, question_type)
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return None

    def _build_prompt(
        self,
        content: str,
        num_questions: int,
        difficulty: str,
        question_type: str
    ) -> str:
        """Construct the prompt for the AI"""
        instructions = [
            f"Generate {num_questions} {self.difficulty_mapping[difficulty]} questions",
            f"Question type: {self.question_type_mapping[question_type]}",
            "Format your response as a JSON object with: title, description, and questions array",
            "Each question should have: question, type, options (if applicable), correct_answer, explanation"
        ]
        
        prompt = f"""
        Create a quiz based on the following content:
        
        {content}
        
        Instructions:
        {'. '.join(instructions)}.
        
        For multiple choice questions, provide 4 options labeled A) to D).
        For true/false questions, the options should be simply True or False.
        For short answer questions, provide a brief expected answer.
        Always include a clear explanation for each answer.
        
        Example format for multiple choice:
        {{
            "question": "What is the capital of France?",
            "type": "multiple_choice",
            "options": ["A) London", "B) Paris", "C) Berlin", "D) Madrid"],
            "correct_answer": "B",
            "explanation": "Paris is the capital of France."
        }}
        
        Return only the JSON object, without any additional text or markdown formatting.
        """
        return prompt

    def _get_completion(self, prompt: str) -> str:
        """Get completion from OpenAI API"""
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content

    def _parse_response(self, response: str, question_type: str) -> Dict:
        """Parse the API response into quiz format"""
        try:
            # Clean the response to extract just the JSON
            json_str = re.sub(r'^.*?\{', '{', response, flags=re.DOTALL)
            json_str = re.sub(r'\}.*?$', '}', json_str, flags=re.DOTALL)
            
            quiz_data = json.loads(json_str)
            
            # Ensure questions match requested type for non-mixed quizzes
            if question_type != "mixed":
                for q in quiz_data.get('questions', []):
                    if q.get('type') != question_type:
                        q['type'] = question_type
                        if question_type == "multiple_choice":
                            q['options'] = ["A) True", "B) False"]  # Fallback options
                            q['correct_answer'] = "A"
                        elif question_type == "true_false":
                            q['options'] = ["True", "False"]
                            q['correct_answer'] = "True"
                        elif question_type == "short_answer":
                            q['options'] = []
                            q['correct_answer'] = "Answer not generated properly"
            
            return quiz_data
        except json.JSONDecodeError:
            print("Failed to parse quiz response")
            return {"title": "Generated Quiz", "description": "", "questions": []}
