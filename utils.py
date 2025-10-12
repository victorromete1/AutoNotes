# Author: Victor
# Page name: utils.py
# Page purpose: Utilities for app.py
# Date of creation: 2025-10-10
import re
from datetime import datetime

def sanitize_filename(filename):
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove any trailing periods or spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "note"
    
    # Limit length to prevent filesystem issues
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def export_notes_as_text(notes):
    if not notes:
        return "No notes to export."
    
    exported_content = f"Study Notes Export\n"
    exported_content += f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    exported_content += "=" * 50 + "\n\n"
    
    # Group notes by category
    categories = {}
    for note in notes:
        category = note.get('category', 'General')
        if category not in categories:
            categories[category] = []
        categories[category].append(note)
    
    # Export notes organized by category
    for category, category_notes in sorted(categories.items()):
        exported_content += f"CATEGORY: {category.upper()}\n"
        exported_content += "-" * 30 + "\n\n"
        
        for note in category_notes:
            exported_content += f"Title: {note['title']}\n"
            exported_content += f"Created: {note['timestamp']}\n"
            exported_content += f"Category: {note.get('category', 'General')}\n"
            exported_content += "-" * 20 + "\n"
            exported_content += f"{note['content']}\n"
            exported_content += "\n" + "=" * 50 + "\n\n"
    
    return exported_content

def format_note_preview(content, max_length=100):
    if len(content) <= max_length:
        return content
    
    # Find the last complete word within the limit
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + "..."

def count_words(text):
    if not text.strip():
        return 0
    
    return len(text.split())

def validate_note_data(title, content, category):
    errors = []
    
    if not title or not title.strip():
        errors.append("Note title is required")
    elif len(title.strip()) > 200:
        errors.append("Note title is too long (maximum 200 characters)")
    
    if not content or not content.strip():
        errors.append("Note content is required")
    elif len(content.strip()) > 50000:
        errors.append("Note content is too long (maximum 50,000 characters)")
    
    if not category or not category.strip():
        errors.append("Note category is required")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
