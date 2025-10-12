# Advanced AI Study Platform

## Overview

This is a comprehensive Streamlit-based study platform that integrates multiple AI-powered learning tools. The platform features note generation, flashcard creation, quiz systems, progress tracking, and detailed PDF reporting. It uses DeepSeek AI through OpenRouter for completely free operation, with OpenAI as a fallback option.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit with multi-page navigation system
- **Layout**: Wide layout with enhanced sidebar navigation
- **State Management**: Comprehensive session state for notes, flashcards, quizzes, and progress tracking
- **Navigation**: Tab-based interface with dedicated pages for each major feature
- **Responsive Design**: Adaptive layouts for different screen sizes

### Backend Architecture
- **Modular Design**: Separate classes for each major functionality:
  - `NoteGenerator`: AI-powered note creation and summarization
  - `FlashcardGenerator`: Automated flashcard creation from content
  - `QuizGenerator`: Multi-format quiz creation and AI grading
  - `ProgressTracker`: Analytics and performance tracking
  - `PDFReportGenerator`: Comprehensive report generation
- **AI Integration**: Dual API support (OpenRouter/DeepSeek for free usage, OpenAI as fallback)
- **Error Handling**: Comprehensive validation and graceful error recovery

### Data Management
- **Session Storage**: Multi-dimensional data structure storing:
  - Notes with categorization and metadata
  - Flashcards with difficulty levels and study tracking
  - Quiz results with detailed performance analytics
  - Study sessions with progress metrics
- **File Management**: Import/export functionality for flashcards (.flashcard format)
- **Progress Persistence**: Comprehensive activity logging for analytics

### Advanced Features
- **Flashcard System**: 
  - AI-generated flashcards from any content
  - Interactive study sessions with self-assessment
  - Import/export capabilities
  - Spaced repetition tracking
- **Quiz System**:
  - Multiple question types (MCQ, T/F, short answer, fill-in-blank)
  - AI-powered grading with detailed feedback
  - Performance analytics and improvement suggestions
- **Progress Analytics**:
  - Subject-wise performance tracking
  - Visual charts and trend analysis
  - Strengths/weaknesses identification
  - Personalized study recommendations
- **PDF Reporting**:
  - Comprehensive progress reports
  - Flashcard collections for printing
  - Professional formatting with charts and analysis

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o model for note generation
- **API Key Management**: Environment variable-based configuration for security

### Python Libraries
- **streamlit**: Web application framework
- **openai**: Official OpenAI Python client (also used for OpenRouter API)
- **reportlab**: PDF generation for comprehensive reports
- **matplotlib**: Chart and graph generation for analytics
- **pandas**: Data analysis and processing
- **fpdf2**: Alternative PDF generation
- **Pillow**: Image processing capabilities
- **datetime, json, re, os**: Built-in libraries for various utilities

### Development Environment
- **Python Runtime**: Compatible with standard Python environments
- **Environment Variables**: Requires `OPENAI_API_KEY` for API access