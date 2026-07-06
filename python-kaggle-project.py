"""
Smart Note Taker Agent - Capstone Project
5-Day AI Agents Intensive Course with Google

Features:
- Dark mode web interface
- AI-powered note categorization using Gemini
- Local JSON storage
- Notion-inspired features: priorities, due dates, status, search, export
- 3 core concepts: LLM Agent, Custom Tools, Sessions & Memory
"""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
import re

# Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Gradio for web interface
import gradio as gr

# ============================================================
# 1. CONFIGURATION
# ============================================================

# Set your API key here or as environment variable
API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Categories for notes
CATEGORIES = ["Personal", "Ideas", "Work"]

# Priorities
PRIORITIES = ["High", "Medium", "Low"]

# Status options
STATUSES = ["To-Do", "In Progress", "Done"]

# JSON file for persistent storage
NOTES_FILE = "notes.json"

# ============================================================
# 2. GEMINI SETUP (Optional)
# ============================================================

USE_AI = False
model = None

if API_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        USE_AI = True
        print("✅ Gemini AI is active. Extra features enabled.")
    except Exception as e:
        print(f"⚠️ Error initializing Gemini: {e}. Running in basic mode.")
else:
    print("ℹ️ No API key found. Running in basic mode.")

# ============================================================
# 3. NOTE STORAGE (Memory Concept)
# ============================================================

class NoteStorage:
    """Handles saving and loading notes from JSON file"""
    
    def __init__(self, filename: str = NOTES_FILE):
        self.filename = filename
        self.notes: List[Dict] = []
        self.load_notes()
    
    def load_notes(self) -> None:
        """Load notes from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.notes = json.load(f)
            except:
                self.notes = []
        else:
            self.notes = []
    
    def save_notes(self) -> None:
        """Save notes to JSON file"""
        with open(self.filename, 'w') as f:
            json.dump(self.notes, f, indent=2)
    
    def add_note(self, note: Dict) -> None:
        """Add a new note"""
        self.notes.append(note)
        self.save_notes()
    
    def get_all(self) -> List[Dict]:
        """Get all notes"""
        return self.notes
    
    def get_by_category(self, category: str) -> List[Dict]:
        """Get notes by category"""
        return [n for n in self.notes if n.get('category') == category]
    
    def get_by_priority(self, priority: str) -> List[Dict]:
        """Get notes by priority"""
        return [n for n in self.notes if n.get('priority') == priority]
    
    def get_by_status(self, status: str) -> List[Dict]:
        """Get notes by status"""
        return [n for n in self.notes if n.get('status') == status]
    
    def get_favorites(self) -> List[Dict]:
        """Get favorite notes"""
        return [n for n in self.notes if n.get('favorite', False)]
    
    def search_notes(self, keyword: str) -> List[Dict]:
        """Search notes by keyword"""
        keyword_lower = keyword.lower()
        results = []
        for note in self.notes:
            if keyword_lower in note.get('text', '').lower():
                results.append(note)
            elif keyword_lower in note.get('category', '').lower():
                results.append(note)
        return results
    
    def delete_note(self, index: int) -> bool:
        """Delete note by index"""
        if 0 <= index < len(self.notes):
            del self.notes[index]
            self.save_notes()
            return True
        return False
    
    def get_count(self) -> int:
        """Get total number of notes"""
        return len(self.notes)
    
    def clear_all(self) -> None:
        """Clear all notes"""
        self.notes = []
        self.save_notes()
    
    def toggle_favorite(self, index: int) -> bool:
        """Toggle favorite status"""
        if 0 <= index < len(self.notes):
            self.notes[index]['favorite'] = not self.notes[index].get('favorite', False)
            self.save_notes()
            return True
        return False

# ============================================================
# 4. SMART NOTE AGENT (Core Agent)
# ============================================================

class SmartNoteAgent:
    """AI-powered note organizer with Notion-like features"""
    
    def __init__(self):
        self.storage = NoteStorage()
        self.categories = CATEGORIES
        self.priorities = PRIORITIES
        self.statuses = STATUSES
        self.use_ai = USE_AI
        
        self.system_prompt = f"""
        You are a Smart Note Taker Agent. Your job is to categorize and prioritize notes.
        
        Rules:
        1. Read the user's note
        2. Classify into ONE category: {', '.join(self.categories)}
        3. Suggest priority (High/Medium/Low) based on urgency
        4. Return format: "Category: [category] | Priority: [priority]"
        
        Examples:
        Note: "Buy milk and eggs" → Category: Personal | Priority: Low
        Note: "Submit project by Friday" → Category: Work | Priority: High
        Note: "Write blog about AI" → Category: Ideas | Priority: Medium
        """
    
    # ============================================================
    # 4a. Agent Brain (LLM Concept) - AI Mode
    # ============================================================
    
    def categorize_note_ai(self, note_text: str) -> Dict:
        """Use Gemini to categorize and prioritize a note"""
        if not self.use_ai or not model:
            return self._basic_categorize(note_text)
        
        try:
            prompt = f"""
            {self.system_prompt}
            
            Note: "{note_text}"
            
            Response:
            """
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # Parse result
            category = self.categories[0]
            priority = "Medium"
            
            if "Category:" in result:
                parts = result.split("|")
                for part in parts:
                    if "Category:" in part:
                        cat = part.replace("Category:", "").strip()
                        if cat in self.categories:
                            category = cat
                    if "Priority:" in part:
                        pri = part.replace("Priority:", "").strip()
                        if pri in self.priorities:
                            priority = pri
            
            return {
                'category': category,
                'priority': priority,
                'status': "To-Do",
                'favorite': False
            }
        except:
            return self._basic_categorize(note_text)
    
    # ============================================================
    # 4b. Basic Mode (Without API Key)
    # ============================================================
    
    def _basic_categorize(self, note_text: str) -> Dict:
        """Simple keyword-based categorization (no API)"""
        text_lower = note_text.lower()
        
        # Determine category
        if any(word in text_lower for word in ['idea', 'think', 'plan', 'brainstorm', 'creative']):
            category = "Ideas"
        elif any(word in text_lower for word in ['meeting', 'project', 'deadline', 'client', 'boss', 'work', 'office']):
            category = "Work"
        else:
            category = "Personal"
        
        # Determine priority
        if any(word in text_lower for word in ['urgent', 'asap', 'deadline', 'critical', 'important']):
            priority = "High"
        elif any(word in text_lower for word in ['later', 'someday', 'maybe']):
            priority = "Low"
        else:
            priority = "Medium"
        
        return {
            'category': category,
            'priority': priority,
            'status': "To-Do",
            'favorite': False
        }
    
    # ============================================================
    # 4c. Main Functions
    # ============================================================
    
    def add_note(self, note_text: str, due_date: str = "", status: str = "To-Do") -> Dict:
        """Add a new note with AI or basic categorization"""
        # Get categorization
        meta = self.categorize_note_ai(note_text)
        
        # Create note object
        note = {
            'id': len(self.storage.notes) + 1,
            'text': note_text,
            'category': meta.get('category', 'Personal'),
            'priority': meta.get('priority', 'Medium'),
            'status': status,
            'due_date': due_date if due_date else "No due date",
            'favorite': False,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save to memory
        self.storage.add_note(note)
        return note
    
    def view_all_notes(self) -> List[Dict]:
        """Tool: View all notes (0 API calls)"""
        return self.storage.get_all()
    
    def filter_by_category(self, category: str) -> List[Dict]:
        """Tool: Filter notes by category (0 API calls)"""
        if category == "All":
            return self.storage.get_all()
        return self.storage.get_by_category(category)
    
    def filter_by_priority(self, priority: str) -> List[Dict]:
        """Tool: Filter notes by priority (0 API calls)"""
        if priority == "All":
            return self.storage.get_all()
        return self.storage.get_by_priority(priority)
    
    def filter_by_status(self, status: str) -> List[Dict]:
        """Tool: Filter notes by status (0 API calls)"""
        if status == "All":
            return self.storage.get_all()
        return self.storage.get_by_status(status)
    
    def search_notes(self, keyword: str) -> List[Dict]:
        """Tool: Search notes by keyword (0 API calls)"""
        return self.storage.search_notes(keyword)
    
    def get_favorites(self) -> List[Dict]:
        """Tool: Get favorite notes (0 API calls)"""
        return self.storage.get_favorites()
    
    def toggle_favorite(self, index: int) -> bool:
        """Tool: Toggle favorite (0 API calls)"""
        return self.storage.toggle_favorite(index)
    
    def count_notes(self) -> int:
        """Tool: Count total notes (0 API calls)"""
        return self.storage.get_count()
    
    def delete_note(self, index: int) -> bool:
        """Tool: Delete a note (0 API calls)"""
        return self.storage.delete_note(index)
    
    def clear_all(self) -> None:
        """Tool: Clear all notes (0 API calls)"""
        self.storage.clear_all()
    
    def get_stats(self) -> Dict:
        """Get statistics about notes"""
        stats = {
            "Total": self.count_notes(),
            "Favorites": len(self.get_favorites())
        }
        
        for cat in self.categories:
            stats[f"📂 {cat}"] = len(self.storage.get_by_category(cat))
        
        for pri in self.priorities:
            stats[f"⚡ {pri}"] = len(self.storage.get_by_priority(pri))
        
        for stat in self.statuses:
            stats[f"📌 {stat}"] = len(self.storage.get_by_status(stat))
        
        return stats
    
    def export_notes(self, format: str = "csv") -> str:
        """Export notes as CSV or TXT"""
        notes = self.storage.get_all()
        
        if format == "csv":
            filename = f"notes_export_{datetime.now().strftime('%Y%m%d')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'text', 'category', 'priority', 'status', 'due_date', 'favorite', 'timestamp'])
                writer.writeheader()
                writer.writerows(notes)
            return f"✅ Notes exported to {filename}"
        
        elif format == "txt":
            filename = f"notes_export_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("📝 SMART NOTE TAKER - EXPORT\n")
                f.write("=" * 60 + "\n\n")
                for note in notes:
                    f.write(f"📌 #{note['id']}\n")
                    f.write(f"📝 {note['text']}\n")
                    f.write(f"📂 {note['category']} | ⚡ {note['priority']} | 📌 {note['status']}\n")
                    f.write(f"📅 {note['timestamp']} | ⭐ {'⭐' if note.get('favorite') else ''}\n")
                    f.write("-" * 40 + "\n\n")
            return f"✅ Notes exported to {filename}"
        
        return "❌ Invalid format"

# ============================================================
# 5. GRADIO UI FUNCTIONS (Dark Mode Frontend)
# ============================================================

# Initialize agent globally
agent = SmartNoteAgent()

def format_notes_display(notes: List[Dict]) -> str:
    """Format notes for display in the UI"""
    if not notes:
        return "📭 No notes found! Click 'Add Note' to create one."
    
    output = ""
    for i, note in enumerate(notes, 1):
        favorite = "⭐ " if note.get('favorite') else "  "
        output += f"""
        ─────────────────────────────────────
        {favorite}**#{note.get('id', i)}** {note.get('text', '')}
        📂 **Category:** {note.get('category', 'Uncategorized')}
        ⚡ **Priority:** {note.get('priority', 'Medium')}
        📌 **Status:** {note.get('status', 'To-Do')}
        📅 **Due:** {note.get('due_date', 'No due date')}
        🕐 **Created:** {note.get('timestamp', 'No date')}
        """
    return output

def add_note_ui(note_text: str, priority: str, status: str, due_date: str) -> tuple:
    """Handle adding a new note"""
    if not note_text or not note_text.strip():
        return "⚠️ Please enter some text for your note!", "", "", "", "", get_stats_ui()
    
    # Agent adds and categorizes the note
    note = agent.add_note(note_text, due_date, status)
    
    # Get updated data
    all_notes = agent.view_all_notes()
    stats = agent.get_stats()
    
    return (
        f"✅ Note added successfully!\n📂 Category: {note['category']}\n⚡ Priority: {note['priority']}\n🕐 Time: {note['timestamp']}",
        "",  # Clear input
        format_notes_display(all_notes),
        format_notes_display(agent.filter_by_category("Personal")),
        format_notes_display(agent.filter_by_category("Ideas")),
        format_notes_display(agent.filter_by_category("Work")),
        get_stats_ui()
    )

def view_all_notes_ui() -> tuple:
    """Handle viewing all notes"""
    notes = agent.view_all_notes()
    stats = agent.get_stats()
    return (
        format_notes_display(notes),
        format_notes_display(agent.filter_by_category("Personal")),
        format_notes_display(agent.filter_by_category("Ideas")),
        format_notes_display(agent.filter_by_category("Work")),
        get_stats_ui()
    )

def search_notes_ui(keyword: str) -> str:
    """Handle searching notes"""
    if not keyword or not keyword.strip():
        return "🔍 Please enter a search term!"
    
    results = agent.search_notes(keyword)
    if results:
        return format_notes_display(results)
    else:
        return f"🔍 No notes found containing '{keyword}'"

def filter_notes_ui(category: str, priority: str, status: str) -> tuple:
    """Handle filtering notes by category, priority, status"""
    notes = agent.view_all_notes()
    
    # Apply filters
    if category != "All":
        notes = [n for n in notes if n.get('category') == category]
    if priority != "All":
        notes = [n for n in notes if n.get('priority') == priority]
    if status != "All":
        notes = [n for n in notes if n.get('status') == status]
    
    stats = agent.get_stats()
    
    return (
        format_notes_display(notes),
        format_notes_display(agent.filter_by_category("Personal")),
        format_notes_display(agent.filter_by_category("Ideas")),
        format_notes_display(agent.filter_by_category("Work")),
        get_stats_ui()
    )

def delete_note_ui(index_str: str) -> tuple:
    """Handle deleting a note"""
    try:
        index = int(index_str) - 1
        if agent.delete_note(index):
            all_notes = agent.view_all_notes()
            stats = agent.get_stats()
            return (
                f"✅ Note #{index_str} deleted successfully!",
                format_notes_display(all_notes),
                format_notes_display(agent.filter_by_category("Personal")),
                format_notes_display(agent.filter_by_category("Ideas")),
                format_notes_display(agent.filter_by_category("Work")),
                get_stats_ui()
            )
        else:
            return "❌ Invalid note number!", "", "", "", "", get_stats_ui()
    except ValueError:
        return "❌ Please enter a valid number!", "", "", "", "", get_stats_ui()

def toggle_favorite_ui(index_str: str) -> str:
    """Handle toggling favorite"""
    try:
        index = int(index_str) - 1
        if agent.toggle_favorite(index):
            note = agent.view_all_notes()[index]
            status = "⭐ Favorited" if note.get('favorite') else "☆ Unfavorited"
            return f"✅ Note #{index_str}: {status}!"
        else:
            return "❌ Invalid note number!"
    except ValueError:
        return "❌ Please enter a valid number!"

def clear_all_ui() -> tuple:
    """Handle clearing all notes"""
    agent.clear_all()
    stats = agent.get_stats()
    return (
        "🗑️ All notes cleared!",
        "📭 No notes found!",
        "📭 No notes found!",
        "📭 No notes found!",
        "📭 No notes found!",
        get_stats_ui()
    )

def export_notes_ui(format: str) -> str:
    """Handle exporting notes"""
    return agent.export_notes(format)

def get_stats_ui() -> str:
    """Get stats for display"""
    stats = agent.get_stats()
    output = "📊 **Statistics**\n\n"
    
    # Show AI status
    if agent.use_ai:
        output += "🤖 **AI Mode:** ✅ Active\n\n"
    else:
        output += "🤖 **AI Mode:** ❌ Inactive (Basic Mode)\n\n"
    
    for key, value in stats.items():
        output += f"• {key}: {value}\n"
    return output

# ============================================================
# 6. GRADIO UI (Dark Mode with Notion Features)
# ============================================================

# Custom CSS for dark mode
custom_css = """
body, .gradio-container {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}
.gr-box, .gr-form, .gr-panel {
    background-color: #161b22 !important;
    border-color: #30363d !important;
}
.gr-button-primary {
    background-color: #238636 !important;
    color: white !important;
}
.gr-button-primary:hover {
    background-color: #2ea043 !important;
}
.gr-button-secondary {
    background-color: #1f6feb !important;
    color: white !important;
}
.gr-button-stop {
    background-color: #da3633 !important;
    color: white !important;
}
h1, h2, h3, label, .gr-markdown {
    color: #e6edf3 !important;
}
.gr-textbox, .gr-dropdown, .gr-number, .gr-datetime {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    border-color: #30363d !important;
}
.gr-textbox:focus, .gr-dropdown:focus {
    border-color: #58a6ff !important;
}
.favorite-btn {
    background-color: #da3633 !important;
    color: #f0f6fc !important;
}
"""

# Create the Gradio interface
with gr.Blocks(
    title="📝 Smart Note Taker Agent",
    theme=gr.themes.Soft(
        primary_hue="green",
        secondary_hue="blue",
        neutral_hue="gray",
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=custom_css
) as demo:
    
    # Header
    gr.Markdown("""
    # 📝 Smart Note Taker Agent
    
    ### 🤖 Powered by Google Gemini AI (Optional)
    
    **Categories:** Personal | Ideas | Work  
    **Priorities:** High | Medium | Low  
    **Status:** To-Do | In Progress | Done
    """)
    
    # ============================================================
    # SECTION 1: ADD NOTE (With Notion-like fields)
    # ============================================================
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## ✏️ Add a Note")
            
            note_input = gr.Textbox(
                label="Write your note here",
                placeholder="e.g., Buy groceries for dinner...",
                lines=3
            )
            
            with gr.Row():
                priority_input = gr.Dropdown(
                    choices=PRIORITIES,
                    label="⚡ Priority",
                    value="Medium"
                )
                status_input = gr.Dropdown(
                    choices=STATUSES,
                    label="📌 Status",
                    value="To-Do"
                )
            
            due_date_input = gr.Textbox(
                label="📅 Due Date (optional)",
                placeholder="e.g., Tomorrow, Dec 31, 2025"
            )
            
            add_btn = gr.Button("➕ Add Note", variant="primary")
            status_output = gr.Textbox(label="Status", interactive=False, lines=2)
        
        with gr.Column(scale=1):
            gr.Markdown("## 📊 Statistics")
            stats_output = gr.Markdown(get_stats_ui())
            
            gr.Markdown("---")
            gr.Markdown("## 🔍 Search Notes")
            search_input = gr.Textbox(
                label="Search by keyword",
                placeholder="Search notes..."
            )
            search_btn = gr.Button("🔍 Search", variant="secondary")
            search_output = gr.Markdown("🔍 Enter a search term above")
    
    # ============================================================
    # SECTION 2: VIEW & MANAGE NOTES
    # ============================================================
    gr.Markdown("## 📋 Manage Notes")
    
    with gr.Tabs():
        with gr.TabItem("📝 All Notes"):
            all_notes_output = gr.Markdown("📭 No notes yet! Add your first note above.")
        
        with gr.TabItem("👤 Personal"):
            personal_output = gr.Markdown("📭 No Personal notes yet!")
        
        with gr.TabItem("💡 Ideas"):
            ideas_output = gr.Markdown("📭 No Ideas notes yet!")
        
        with gr.TabItem("💼 Work"):
            work_output = gr.Markdown("📭 No Work notes yet!")
        
        with gr.TabItem("⭐ Favorites"):
            favorites_output = gr.Markdown("⭐ No favorite notes yet!")
    
    # ============================================================
    # SECTION 3: FILTERS (Advanced)
    # ============================================================
    with gr.Row():
        with gr.Column():
            gr.Markdown("## 🔍 Advanced Filters")
            category_filter = gr.Dropdown(
                choices=["All"] + CATEGORIES,
                label="📂 Category",
                value="All"
            )
            priority_filter = gr.Dropdown(
                choices=["All"] + PRIORITIES,
                label="⚡ Priority",
                value="All"
            )
            status_filter = gr.Dropdown(
                choices=["All"] + STATUSES,
                label="📌 Status",
                value="All"
            )
            filter_btn = gr.Button("🔍 Apply Filters", variant="secondary")
    
    # ============================================================
    # SECTION 4: ACTIONS (Delete, Favorite, Export)
    # ============================================================
    with gr.Row():
        with gr.Column():
            gr.Markdown("## 🗑️ Delete Note")
            delete_input = gr.Number(
                label="Enter note number to delete",
                value=1,
                precision=0,
                minimum=1
            )
            delete_btn = gr.Button("🗑️ Delete Note", variant="stop")
        
        with gr.Column():
            gr.Markdown("## ⭐ Favorite")
            favorite_input = gr.Number(
                label="Enter note number to favorite/unfavorite",
                value=1,
                precision=0,
                minimum=1
            )
            favorite_btn = gr.Button("⭐ Toggle Favorite", variant="secondary")
            favorite_output = gr.Textbox(label="Favorite Status", interactive=False)
        
        with gr.Column():
            gr.Markdown("## 📤 Export Notes")
            export_format = gr.Dropdown(
                choices=["csv", "txt"],
                label="Export Format",
                value="csv"
            )
            export_btn = gr.Button("📤 Export", variant="secondary")
            export_output = gr.Textbox(label="Export Status", interactive=False)
        
        with gr.Column():
            gr.Markdown("## ⚠️ Danger Zone")
            clear_btn = gr.Button("🗑️ Clear All Notes", variant="stop")
    
    # ============================================================
    # SECTION 5: REFRESH
    # ============================================================
    with gr.Row():
        refresh_btn = gr.Button("🔄 Refresh All", variant="secondary")
    
    # ============================================================
    # SECTION 6: VIEW FAVORITES BUTTON
    # ============================================================
    with gr.Row():
        view_favorites_btn = gr.Button("⭐ View Favorites", variant="secondary")
    
    # ============================================================
    # SECTION 7: FOOTER
    # ============================================================
    gr.Markdown("""
    ---
    **📌 Course:** 5-Day AI Agents Intensive with Google  
    **🏷️ Track:** Freestyle  
    **📂 Storage:** Local JSON file (notes.json)
    
    **🤖 AI Status:** {}  
    **💡 Tip:** Add your Gemini API key to enable AI-powered categorization!
    """.format("✅ Active" if agent.use_ai else "❌ Inactive (Basic Mode)"))

    # ============================================================
    # 7. EVENT HANDLERS
    # ============================================================
    
    # Add note
    add_btn.click(
        fn=add_note_ui,
        inputs=[note_input, priority_input, status_input, due_date_input],
        outputs=[
            status_output,
            note_input,
            all_notes_output,
            personal_output,
            ideas_output,
            work_output,
            stats_output
        ]
    )
    
    # Refresh all
    refresh_btn.click(
        fn=view_all_notes_ui,
        inputs=[],
        outputs=[
            all_notes_output,
            personal_output,
            ideas_output,
            work_output,
            stats_output
        ]
    )
    
    # View favorites
    view_favorites_btn.click(
        fn=lambda: format_notes_display(agent.get_favorites()),
        inputs=[],
        outputs=[favorites_output]
    )
    
    # Search
    search_btn.click(
        fn=search_notes_ui,
        inputs=[search_input],
        outputs=[search_output]
    )
    
    # Apply filters
    filter_btn.click(
        fn=filter_notes_ui,
        inputs=[category_filter, priority_filter, status_filter],
        outputs=[
            all_notes_output,
            personal_output,
            ideas_output,
            work_output,
            stats_output
        ]
    )
    
    # Delete note
    delete_btn.click(
        fn=delete_note_ui,
        inputs=[delete_input],
        outputs=[
            status_output,
            all_notes_output,
            personal_output,
            ideas_output,
            work_output,
            stats_output
        ]
    )
    
    # Toggle favorite
    favorite_btn.click(
        fn=toggle_favorite_ui,
        inputs=[favorite_input],
        outputs=[favorite_output]
    )
    
    # Export notes
    export_btn.click(
        fn=export_notes_ui,
        inputs=[export_format],
        outputs=[export_output]
    )
    
    # Clear all
    clear_btn.click(
        fn=clear_all_ui,
        inputs=[],
        outputs=[
            status_output,
            all_notes_output,
            personal_output,
            ideas_output,
            work_output,
            stats_output
        ]
    )
    
    # ============================================================
    # 8. AUTO-LOAD ON START
    # ============================================================
    demo.load(
        fn=view_all_notes_ui,
        inputs=[],
        outputs=[
            all_notes_output,
            personal_output,
            ideas_output,
            work_output,
            stats_output
        ]
    )

# ============================================================
# 9. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    if not API_KEY:
        print("\n" + "="*60)
        print("ℹ️  Running in BASIC MODE (No API Key)")
        print("📝 To enable AI features, add your Gemini API key")
        print("🔑 Get your key: https://aistudio.google.com/apikey")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("✅ Running in AI MODE (Gemini Active)")
        print("="*60 + "\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=False
    )