# Author: Victor
# Page name: progress_tracker.py
# Page purpose: Progress Tracker for app.py
# Date of creation: 2025-10-10
# this file is responsible for tracking user progress, generating statistics, and creating visualizations of study habits and performance, it makes personalized "tips"from looking at your data.
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

class ProgressTracker:
    def __init__(self):
        """Initialize progress tracker."""
        pass
    
    def add_study_session(self, session_data):
        """Add a study session to progress tracking."""
        session = {
            "session_id": f"session_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "activity_type": session_data.get("type", "study"),  # study, quiz, flashcards
            "subject": session_data.get("subject", "General"),
            "duration_minutes": session_data.get("duration", 0),
            "score": session_data.get("score", None),
            "questions_answered": session_data.get("questions_answered", 0),
            "correct_answers": session_data.get("correct_answers", 0),
            "notes_created": session_data.get("notes_created", 0),
            "flashcards_studied": session_data.get("flashcards_studied", 0)
        }
        return session
    # Calculate statistics for a specific subject or all subjects
    def calculate_subject_stats(self, sessions, subject=None):
        if subject:
            filtered_sessions = [s for s in sessions if s.get("subject") == subject]
        else:
            filtered_sessions = sessions
        
        if not filtered_sessions:
            return {
                "total_sessions": 0,
                "total_study_time": 0,
                "average_score": 0,
                "total_questions": 0,
                "accuracy": 0,
                "improvement_trend": "No data"
            }
        
        quiz_sessions = [s for s in filtered_sessions if s.get("activity_type") == "quiz" and s.get("score") is not None]
        
        total_study_time = sum(s.get("duration_minutes", 0) for s in filtered_sessions)
        total_questions = sum(s.get("questions_answered", 0) for s in filtered_sessions)
        total_correct = sum(s.get("correct_answers", 0) for s in filtered_sessions)
        
        average_score = 0
        if quiz_sessions:
            average_score = sum(s.get("score", 0) for s in quiz_sessions) / len(quiz_sessions)
        
        accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate improvement trend
        improvement_trend = self._calculate_improvement_trend(quiz_sessions)
        
        return {
            "total_sessions": len(filtered_sessions),
            "total_study_time": total_study_time,
            "average_score": round(average_score, 1),
            "total_questions": total_questions,
            "accuracy": round(accuracy, 1),
            "improvement_trend": improvement_trend,
            "quiz_sessions": len(quiz_sessions),
            "notes_created": sum(s.get("notes_created", 0) for s in filtered_sessions),
            "flashcards_studied": sum(s.get("flashcards_studied", 0) for s in filtered_sessions)
        }
    
    def _calculate_improvement_trend(self, quiz_sessions):
        """Calculate if performance is improving, declining, or stable."""
        if len(quiz_sessions) < 2:
            return "Insufficient data"
        
        # Sort by timestamp
        sorted_sessions = sorted(quiz_sessions, key=lambda x: x.get("timestamp", ""))
        
        # Take recent sessions for trend analysis
        recent_sessions = sorted_sessions[-5:] if len(sorted_sessions) >= 5 else sorted_sessions
        
        if len(recent_sessions) < 2:
            return "Insufficient data"
        
        scores = [s.get("score", 0) for s in recent_sessions]
        
        # Simple trend calculation
        first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        difference = second_half_avg - first_half_avg
        
        if difference > 5:
            return "Improving"
        elif difference < -5:
            return "Declining"
        else:
            return "Stable"
    
    def get_weekly_summary(self, sessions):
        """Get summary of activity for the past week."""
        week_ago = datetime.now() - timedelta(days=7)
        week_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s.get("timestamp", "")) > week_ago
        ]
        
        subjects = list(set(s.get("subject", "General") for s in week_sessions))
        subject_summaries = {}
        
        for subject in subjects:
            subject_summaries[subject] = self.calculate_subject_stats(week_sessions, subject)
        
        return {
            "period": "Past 7 days",
            "total_sessions": len(week_sessions),
            "subjects": subject_summaries,
            "total_study_time": sum(s.get("duration_minutes", 0) for s in week_sessions)
        }
    # Creates progress chart
    def create_progress_chart(self, sessions, chart_type="score_over_time"):
        try:
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == "score_over_time":
                quiz_sessions = [s for s in sessions if s.get("activity_type") == "quiz" and s.get("score") is not None]
                if not quiz_sessions:
                    return None
                
                # Sort by timestamp
                quiz_sessions.sort(key=lambda x: x.get("timestamp", ""))
                
                dates = [datetime.fromisoformat(s.get("timestamp", "")).strftime("%m/%d") for s in quiz_sessions[-10:]]
                scores = [s.get("score", 0) for s in quiz_sessions[-10:]]
                
                ax.plot(dates, scores, marker='o', linewidth=2, markersize=8)
                ax.set_title("Quiz Scores Over Time (Last 10 Quizzes)", fontsize=14, fontweight='bold')
                ax.set_ylabel("Score (%)", fontsize=12)
                ax.set_xlabel("Date", fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.set_ylim(0, 100)
                
            elif chart_type == "subject_breakdown":
                subjects = {}
                for session in sessions:
                    subject = session.get("subject", "General")
                    if subject not in subjects:
                        subjects[subject] = 0
                    subjects[subject] += session.get("duration_minutes", 0)
                
                if not subjects:
                    return None
                
                colors = plt.cm.Set3(range(len(subjects)))
                ax.pie(subjects.values(), labels=subjects.keys(), autopct='%1.1f%%', colors=colors)
                ax.set_title("Study Time by Subject", fontsize=14, fontweight='bold')
            
            elif chart_type == "activity_frequency":
                # Weekly activity frequency
                week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                activity_counts = [0] * 7
                
                for session in sessions:
                    session_date = datetime.fromisoformat(session.get("timestamp", ""))
                    weekday = session_date.weekday()
                    activity_counts[weekday] += 1
                
                bars = ax.bar(week_days, activity_counts, color='skyblue', alpha=0.8)
                ax.set_title("Study Sessions by Day of Week", fontsize=14, fontweight='bold')
                ax.set_ylabel("Number of Sessions", fontsize=12)
                ax.set_xlabel("Day", fontsize=12)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            return img_base64
            
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
    
    def get_strengths_and_weaknesses(self, sessions):
        """Analyze user's strengths and weaknesses by subject."""
        subjects = {}
        
        for session in sessions:
            if session.get("activity_type") == "quiz" and session.get("score") is not None:
                subject = session.get("subject", "General")
                if subject not in subjects:
                    subjects[subject] = []
                subjects[subject].append(session.get("score", 0))
        
        analysis = {
            "strengths": [],
            "needs_improvement": [],
            "recommendations": []
        }
        
        for subject, scores in subjects.items():
            if len(scores) >= 2:  # Need at least 2 scores to analyze
                avg_score = sum(scores) / len(scores)
                if avg_score >= 85:
                    analysis["strengths"].append(f"{subject} (avg: {avg_score:.1f}%)")
                elif avg_score < 70:
                    analysis["needs_improvement"].append(f"{subject} (avg: {avg_score:.1f}%)")
        
        # Generate recommendations
        if analysis["needs_improvement"]:
            analysis["recommendations"].extend([
                "Create more flashcards for subjects needing improvement",
                "Schedule regular review sessions for weak subjects",
                "Try different question types to reinforce learning"
            ])
        
        if analysis["strengths"]:
            analysis["recommendations"].append("Continue regular practice in your strong subjects")
        
        return analysis
    
    def generate_study_recommendations(self, sessions):
        """Generate personalized study recommendations."""
        if not sessions:
            return ["Start by creating some notes and taking quizzes to get personalized recommendations!"]
        
        recommendations = []
        recent_sessions = [s for s in sessions if 
                          datetime.fromisoformat(s.get("timestamp", "")) > datetime.now() - timedelta(days=7)]
        
        # Check study frequency
        if len(recent_sessions) < 3:
            recommendations.append("🗓️ Try to study more consistently - aim for at least 3 sessions per week")
        
        # Check quiz performance
        quiz_sessions = [s for s in recent_sessions if s.get("activity_type") == "quiz"]
        if quiz_sessions:
            avg_score = sum(s.get("score", 0) for s in quiz_sessions) / len(quiz_sessions)
            if avg_score < 75:
                recommendations.append("📚 Consider reviewing your notes before taking quizzes")
                recommendations.append("🔄 Try creating flashcards to reinforce key concepts")
        
        # Check study time
        total_time = sum(s.get("duration_minutes", 0) for s in recent_sessions)
        if total_time < 60:  # Less than 1 hour per week
            recommendations.append("⏰ Consider increasing your study time - even 15 minutes daily helps!")
        
        # Subject diversity
        subjects = set(s.get("subject", "General") for s in recent_sessions)
        if len(subjects) == 1:
            recommendations.append("🎯 Try studying multiple subjects to keep learning diverse and engaging")
        
        if not recommendations:
            recommendations.append("🎉 Great job! You're maintaining good study habits. Keep it up!")
        
        return recommendations