# Not used broken.
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, timedelta
import io
import base64

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=20,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        )
        self.subheader_style = ParagraphStyle(
            'CustomSubHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        self.highlight_style = ParagraphStyle(
            'Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            backColor=colors.lightgrey,
            borderColor=colors.grey,
            borderWidth=1,
            borderPadding=8,
            fontName='Helvetica-Bold'
        )
    
    def generate_progress_report(self, user_data, sessions, progress_stats):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        story.append(Paragraph("📊 Study Progress Report", self.title_style))
        story.append(Spacer(1, 20))
        report_date = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"Generated on: {report_date}", self.body_style))
        story.append(Paragraph(f"Study Period: {self._get_study_period(sessions)}", self.body_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph("📋 Executive Summary", self.header_style))
        summary_data = self._create_summary_table(progress_stats)
        if summary_data:
            summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("📚 Subject Performance", self.header_style))
        subject_data = self._create_subject_performance_table(progress_stats)
        if subject_data:
            subject_table = Table(subject_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            subject_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            story.append(subject_table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("💪 Strengths & Areas for Improvement", self.header_style))
        from progress_tracker import ProgressTracker
        tracker = ProgressTracker()
        analysis = tracker.get_strengths_and_weaknesses(sessions)
        if analysis["strengths"]:
            story.append(Paragraph("🌟 Strengths:", self.subheader_style))
            for strength in analysis["strengths"]:
                story.append(Paragraph(f"• {strength}", self.body_style))
            story.append(Spacer(1, 10))
        if analysis["needs_improvement"]:
            story.append(Paragraph("📈 Areas for Improvement:", self.subheader_style))
            for weakness in analysis["needs_improvement"]:
                story.append(Paragraph(f"• {weakness}", self.body_style))
            story.append(Spacer(1, 10))
        story.append(Paragraph("🎯 Personalized Recommendations", self.header_style))
        recommendations = tracker.generate_study_recommendations(sessions)
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", self.body_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("📅 Study Habits Analysis", self.header_style))
        habits_data = self._analyze_study_habits(sessions)
        for habit, description in habits_data.items():
            story.append(Paragraph(f"<b>{habit}:</b> {description}", self.body_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("🕐 Recent Activity (Last 7 Days)", self.header_style))
        recent_sessions = [s for s in sessions if datetime.fromisoformat(s.get("timestamp", "")) > datetime.now() - timedelta(days=7)]
        if recent_sessions:
            activity_data = self._create_recent_activity_table(recent_sessions)
            if activity_data:
                activity_table = Table(activity_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1.3*inch])
                activity_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                story.append(activity_table)
        else:
            story.append(Paragraph("No recent activity in the last 7 days.", self.body_style))
        story.append(PageBreak())
        story.append(Paragraph("🎯 Suggested Goals & Next Steps", self.header_style))
        goals = self._generate_goals(progress_stats, sessions)
        for i, goal in enumerate(goals, 1):
            story.append(Paragraph(f"{i}. {goal}", self.body_style))
        story.append(Spacer(1, 40))
        story.append(Paragraph("Generated by AI Study Notes Generator", ParagraphStyle('Footer', parent=self.body_style, alignment=TA_CENTER, fontSize=8, textColor=colors.grey)))
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
    
    def _get_study_period(self, sessions):
        if not sessions:
            return "No sessions recorded"
        dates = [datetime.fromisoformat(s.get("timestamp", "")) for s in sessions]
        earliest = min(dates).strftime("%B %d, %Y")
        latest = max(dates).strftime("%B %d, %Y")
        if earliest == latest:
            return earliest
        return f"{earliest} to {latest}"
    
    def _create_summary_table(self, progress_stats):
        if not progress_stats:
            return None
        overall_stats = progress_stats.get("overall", {})
        data = [
            ["Metric", "Value"],
            ["Total Study Sessions", str(overall_stats.get("total_sessions", 0))],
            ["Total Study Time", f"{overall_stats.get('total_study_time', 0)} minutes"],
            ["Average Quiz Score", f"{overall_stats.get('average_score', 0)}%"],
            ["Questions Answered", str(overall_stats.get("total_questions", 0))],
            ["Overall Accuracy", f"{overall_stats.get('accuracy', 0)}%"],
            ["Performance Trend", overall_stats.get("improvement_trend", "No data")]
        ]
        return data
    
    def _create_subject_performance_table(self, progress_stats):
        if not progress_stats or "subjects" not in progress_stats:
            return None
        data = [["Subject", "Sessions", "Avg Score", "Accuracy", "Trend"]]
        for subject, stats in progress_stats["subjects"].items():
            data.append([
                subject,
                str(stats.get("total_sessions", 0)),
                f"{stats.get('average_score', 0)}%",
                f"{stats.get('accuracy', 0)}%",
                stats.get("improvement_trend", "No data")
            ])
        return data if len(data) > 1 else None
    
    def _create_recent_activity_table(self, recent_sessions):
        if not recent_sessions:
            return None
        data = [["Date", "Activity", "Subject", "Score/Duration"]]
        sorted_sessions = sorted(recent_sessions, key=lambda x: x.get("timestamp", ""), reverse=True)
        for session in sorted_sessions[:10]:
            date = datetime.fromisoformat(session.get("timestamp", "")).strftime("%m/%d")
            activity = session.get("activity_type", "study").title()
            subject = session.get("subject", "General")
            if session.get("score") is not None:
                score_duration = f"{session.get('score', 0)}%"
            else:
                score_duration = f"{session.get('duration_minutes', 0)} min"
            data.append([date, activity, subject, score_duration])
        return data if len(data) > 1 else None
    
    def _analyze_study_habits(self, sessions):
        if not sessions:
            return {"Study Habits": "No data available"}
        habits = {}
        unique_days = set(datetime.fromisoformat(s.get("timestamp", "")).date() for s in sessions)
        total_days = (max(unique_days) - min(unique_days)).days + 1 if len(unique_days) > 1 else 1
        frequency = len(unique_days) / total_days * 100
        habits["Study Frequency"] = f"{frequency:.1f}% of days ({len(unique_days)} days out of {total_days})"
        avg_duration = sum(s.get("duration_minutes", 0) for s in sessions) / len(sessions)
        habits["Average Session Length"] = f"{avg_duration:.1f} minutes"
        subjects = [s.get("subject", "General") for s in sessions]
        most_studied = max(set(subjects), key=subjects.count) if subjects else "None"
        habits["Most Studied Subject"] = most_studied
        activities = [s.get("activity_type", "study") for s in sessions]
        most_activity = max(set(activities), key=activities.count) if activities else "None"
        habits["Preferred Activity"] = most_activity.title()
        return habits
    
    def _generate_goals(self, progress_stats, sessions):
        goals = []
        if not progress_stats:
            return ["Complete your first study session to get personalized goals!"]
        overall_stats = progress_stats.get("overall", {})
        avg_score = overall_stats.get("average_score", 0)
        if avg_score < 80:
            goals.append("Aim to achieve an average quiz score of 80% or higher")
        elif avg_score < 90:
            goals.append("Challenge yourself to reach a 90% average quiz score")
        total_sessions = overall_stats.get("total_sessions", 0)
        if total_sessions < 10:
            goals.append("Build a study habit by completing 10 total study sessions")
        total_time = overall_stats.get("total_study_time", 0)
        if total_time < 120:
            goals.append("Dedicate at least 30 minutes per week to studying")
        if "subjects" in progress_stats and len(progress_stats["subjects"]) == 1:
            goals.append("Explore studying multiple subjects to broaden your knowledge")
        quiz_sessions = sum(1 for s in sessions if s.get("activity_type") == "quiz")
        if quiz_sessions < 3:
            goals.append("Take more quizzes to test your knowledge and track progress")
        if not goals:
            goals.append("Maintain your excellent study habits and continue learning!")
        return goals
    
    def generate_flashcard_report(self, flashcards, study_stats):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        story.append(Paragraph("📚 Flashcard Study Report", self.title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("📊 Summary Statistics", self.header_style))
        story.append(Paragraph(f"Total Flashcards: {len(flashcards)}", self.body_style))
        story.append(Paragraph(f"Study Sessions: {study_stats.get('sessions', 0)}", self.body_style))
        story.append(Paragraph(f"Cards Mastered: {study_stats.get('mastered', 0)}", self.body_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph("📋 Your Flashcards", self.header_style))
        categories = {}
        for card in flashcards:
            category = card.get("category", "General")
            if category not in categories:
                categories[category] = []
            categories[category].append(card)
        for category, cards in categories.items():
            story.append(Paragraph(f"📁 {category}", self.subheader_style))
            for i, card in enumerate(cards, 1):
                story.append(Paragraph(f"<b>Card {i}:</b>", self.body_style))
                story.append(Paragraph(f"<b>Front:</b> {card.get('front', '')}", self.body_style))
                story.append(Paragraph(f"<b>Back:</b> {card.get('back', '')}", self.body_style))
                story.append(Spacer(1, 10))
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
