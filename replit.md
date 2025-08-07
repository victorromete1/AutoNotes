# AI Study Notes Generator

## Overview

This is a Streamlit-based web application that generates comprehensive study notes using OpenAI's GPT-4o model. The application allows users to input topics or content and receive AI-generated study notes with customizable detail levels and note types. Users can manage their notes through categorization, filtering, and export functionality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for web interface
- **Layout**: Wide layout with expandable sidebar for note management
- **State Management**: Streamlit session state for persistent data storage across user interactions
- **Caching**: `@st.cache_resource` decorator for efficient resource management of the note generator instance

### Backend Architecture
- **Core Logic**: Object-oriented design with separate `NoteGenerator` class for AI operations
- **API Integration**: OpenAI API client for GPT-4o model interactions
- **Modular Design**: Separation of concerns with dedicated utility functions in `utils.py`
- **Error Handling**: Built-in validation for API keys and user inputs

### Data Management
- **Session Storage**: Notes stored in Streamlit session state as list of dictionaries
- **Note Structure**: Each note contains title, content, category, timestamp, and metadata
- **Categorization**: Dynamic category system allowing users to organize notes by subject
- **Export Functionality**: Text-based export system for offline access

### AI Integration
- **Model**: OpenAI GPT-4o (latest model as of May 2024)
- **Prompt Engineering**: Dynamic prompt creation based on note type and detail level
- **Customization**: Multiple note types (Summary, Detailed Notes, Q&A, etc.) and detail levels (Basic, Intermediate, Advanced)
- **Response Handling**: Structured response processing with error handling

## External Dependencies

### AI Services
- **OpenAI API**: GPT-4o model for note generation
- **API Key Management**: Environment variable-based configuration for security

### Python Libraries
- **streamlit**: Web application framework
- **openai**: Official OpenAI Python client
- **datetime**: Built-in library for timestamp management
- **json**: Built-in library for data serialization
- **re**: Built-in library for filename sanitization
- **os**: Built-in library for environment variable access

### Development Environment
- **Python Runtime**: Compatible with standard Python environments
- **Environment Variables**: Requires `OPENAI_API_KEY` for API access