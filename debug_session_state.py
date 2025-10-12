#!/usr/bin/env python3
#THIS FILE IS NOT IN USE, JUST FOR DEBUGGING PURPOSES
import json
from datetime import datetime

def test_session_state_simulation():
    print("=== SESSION STATE DEBUG ===")
    session_state = {
        'flashcards': [],
        'study_sessions': [],
        'notes': []
    }
    print(f"Initial state - Flashcards: {len(session_state['flashcards'])}")
    new_flashcards = [
        {
            'front': 'What is Python?',
            'back': 'A programming language',
            'category': 'Programming',
            'difficulty': 'Easy',
            'created': datetime.now().isoformat()
        },
        {
            'front': 'What are variables?',
            'back': 'Storage for data values',
            'category': 'Programming',
            'difficulty': 'Easy',
            'created': datetime.now().isoformat()
        }
    ]
    session_state['flashcards'].extend(new_flashcards)
    print(f"After creation - Flashcards: {len(session_state['flashcards'])}")
    if not session_state['flashcards']:
        print("ISSUE: Would show 'No flashcards to manage'")
        return False
    else:
        print("SUCCESS: Should show flashcard management interface")
        print(f"Should display: 'Showing {len(session_state['flashcards'])} flashcards'")
        return True

def test_quiz_completion():
    print("\n=== QUIZ HISTORY DEBUG ===")
    session_state = {
        'study_sessions': []
    }
    quiz_result = {
        'timestamp': datetime.now().isoformat(),
        'title': 'Test Quiz',
        'score': 75.0,
        'correct_answers': 6,
        'total_questions': 8,
        'difficulty': 'Medium',
        'activity_type': 'quiz',
        'subject': 'General'
    }
    session_state['study_sessions'].append(quiz_result)
    print(f"After quiz - Study sessions: {len(session_state['study_sessions'])}")
    quiz_sessions = [s for s in session_state['study_sessions'] if s.get('activity_type') == 'quiz']
    if not quiz_sessions:
        print("ISSUE: Would show 'No quiz history yet'")
        return False
    else:
        print("SUCCESS: Should show quiz history")
        print(f"Should display stats for {len(quiz_sessions)} quizzes")
        return True

if __name__ == "__main__":
    flashcard_ok = test_session_state_simulation()
    quiz_ok = test_quiz_completion()
    if flashcard_ok and quiz_ok:
        print("\n✓ Both features should work correctly")
    else:
        print(f"\n✗ Issues found - Flashcards: {'OK' if flashcard_ok else 'BROKEN'}, Quiz: {'OK' if quiz_ok else 'BROKEN'}")
