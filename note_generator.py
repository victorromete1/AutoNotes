# Author: Victor
# Page name: Note_generator.py
# Page purpose: Note generation system for app.py
# Date of creation: 2025-10-10
import os
from openai import OpenAI
import streamlit as st
# Defines the note generator class
class NoteGenerator:
    def __init__(self):
        """Initialize the note generator with DeepSeek via OpenRouter."""
        
        # Get OpenRouter API key from Streamlit secrets or environment
        openrouter_key = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        
        if not openrouter_key:
            st.error("⚠️ No OpenRouter API key found. Please set OPENROUTER_API_KEY.")
            st.stop()
        
        # Always use OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        )
        self.model = "deepseek/deepseek-chat"
        self.provider = "OpenRouter (Free DeepSeek)"

    # Generate notes with AI
    def generate_notes(self, user_input, note_type="Summary", detail_level="Intermediate"):
        """
        Generate study notes based on user input and preferences.
        
        Args:
            user_input (str): The content, topic, or questions provided by the user
            note_type (str): Type of notes to generate
            detail_level (str): Level of detail (Basic, Intermediate, Advanced)
        
        Returns:
            str: Generated study notes
        """
        try:
            # Create a detailed prompt based on the note type and detail level
            prompt = self._create_prompt(user_input, note_type, detail_level)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational assistant that creates clear, comprehensive, and well-structured study notes. Your notes should be academically sound, easy to understand, and properly formatted for student use."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate notes: {str(e)}")
    # Create a detailed prompt based on the note type and detail level (basically detects the type of notes it is, and creates personalized prompots for the ai related to the note.)
    def _create_prompt(self, user_input, note_type, detail_level):
        
        base_instructions = {
            "Basic": "Create concise, easy-to-understand notes suitable for beginners. Use simple language and focus on the most important concepts.",
            "Intermediate": "Create comprehensive notes with moderate detail. Include examples and explanations that help reinforce understanding.",
            "Advanced": "Create detailed, thorough notes with in-depth explanations, examples, and connections to related concepts."
        }
        
        detail_instruction = base_instructions.get(detail_level, base_instructions["Intermediate"])
        
        if note_type == "Summary":
            return f"""
            {detail_instruction}
            
            Please create a well-structured summary of the following topic or content:
            {user_input}
            
            Format your response with:
            - Clear headings and subheadings
            - Key points in bullet format where appropriate
            - Important terms or concepts highlighted
            - Logical flow from general to specific concepts
            """
            
        elif note_type == "Detailed Explanation":
            return f"""
            {detail_instruction}
            
            Please create a detailed explanation of the following topic:
            {user_input}
            
            Format your response with:
            - Introduction to the topic
            - Step-by-step explanations where applicable
            - Examples to illustrate key concepts
            - Important definitions and terminology
            - Conclusion summarizing main points
            """
            
        elif note_type == "Key Points":
            return f"""
            {detail_instruction}
            
            Please extract and organize the key points from the following content:
            {user_input}
            
            Format your response with:
            - Main concepts organized hierarchically
            - Essential facts and figures
            - Important relationships between concepts
            - Critical information that would be useful for studying
            """
            
        elif note_type == "Study Guide":
            return f"""
            {detail_instruction}
            
            Please create a comprehensive study guide for the following topic:
            {user_input}
            
            Format your response with:
            - Learning objectives
            - Key concepts and definitions
            - Important facts and figures
            - Practice questions or review points
            - Summary of main takeaways
            """
            
        elif note_type == "Definitions":
            return f"""
            {detail_instruction}
            
            Please identify and define key terms and concepts related to:
            {user_input}
            
            Format your response with:
            - Clear definitions for each term
            - Context for when and how terms are used
            - Examples where helpful
            - Organization from basic to advanced terms
            """
            
        elif note_type == "Summarize":
            return f"""
            {detail_instruction}
            
            Please summarize the following text content into clear, organized study notes:
            {user_input}
            
            Format your response with:
            - Main ideas and themes
            - Supporting details organized logically
            - Key takeaways
            - Important facts or data points
            """
            
        elif note_type == "Extract Key Points":
            return f"""
            {detail_instruction}
            
            Please extract the most important points from the following text:
            {user_input}
            
            Format your response with:
            - Main arguments or ideas
            - Supporting evidence
            - Critical facts and data
            - Conclusions or implications
            """
            
        elif note_type == "Create Study Questions":
            return f"""
            Based on the following content, create study questions along with brief answers:
            {user_input}
            
            Format your response with:
            - Questions that test understanding of key concepts
            - Brief, clear answers to each question
            - A mix of factual recall and conceptual understanding questions
            - Questions organized from basic to more complex
            """
            
        elif note_type == "Organize Content":
            return f"""
            {detail_instruction}
            
            Please organize the following content into well-structured study notes:
            {user_input}
            
            Format your response with:
            - Logical organization with clear headings
            - Information grouped by related concepts
            - Hierarchical structure from general to specific
            - Easy-to-scan formatting for study purposes
            """
         
        elif note_type == "Answer Questions":
            return f"""
            {detail_instruction}
            
            Please provide comprehensive answers to the following questions and format them as study notes:
            {user_input}
            
            Format your response with:
            - Clear answers to each question
            - Supporting explanations and examples
            - Related concepts and connections
            - Additional context where helpful
            """
            
        else:
            # Default case
            return f"""
            {detail_instruction}
            
            Please create comprehensive study notes about:
            {user_input}
            
            Format your response with clear headings, key points, and explanations that would be helpful for studying.
            """
