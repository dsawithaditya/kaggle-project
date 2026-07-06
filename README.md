# kaggle-project
# 📝 Smart Note Taker Agent

## 🎯 Capstone Project
**Course:** 5-Day AI Agents Intensive with Google  
**Track:** Freestyle

---

## 📋 Problem Statement
People struggle to organize their thoughts and ideas efficiently. Manual note categorization is time-consuming.

## 🚀 Solution
An AI-powered note organizer with a dark mode web interface, inspired by Notion, that automatically categorizes notes using Google Gemini AI.

---

## 🔑 Course Concepts Used

| Concept | Implementation |
|---------|----------------|
| **LLM Agent** | Gemini categorizes notes (optional) |
| **Custom Tools** | View, filter, search, export, favorite notes |
| **Sessions & Memory** | JSON file storage (state management) |

---

## 🛠️ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# OR using uv
uv pip install -r requirements.txt
```

### 2. Add your Gemini API key (optional)
```bash
cp .env.example .env
```
#Edit .env and paste your key from Google AI Studio.


### 3. Run
```bash
python smart_note_agent.py
```
Open http://localhost:7860

📁 Project Layout:
```
smart-note-agent/
├── smart_note_agent.py      # Main application (Gradio UI + Agent)
├── .env.example             # Environment template
├── .gitignore               # Files to ignore
├── README.md                # Documentation
├── requirements.txt         # Dependencies
├── app.jsx                  # React frontend (CDN, no build)
├── index.html               # HTML template
├── index.css                # Dark mode styles
├── pyproject.toml           # Project metadata
├── uv.lock                  # Lock file
└── notes.json               # Auto-created (state storage)
```

🧠 How It Works
```
Step	               Description
1. Add Note	         User writes a note (e.g., "Buy groceries")
2. Categorize	       Agent analyzes & categorizes (basic or AI)
3. Organize	Note     tagged with category, priority, status
4. Manage	Search,    filter, favorite, or export
```

🎯 Course Concepts Used
Concept	Implementation
LLM Agent	Gemini categorizes notes (optional)
Custom Tools	Search, filter, export, favorite notes
Sessions & Memory	JSON file storage (notes.json)
📊 API Usage
Mode	API Calls	Features
Without API Key	0 calls	All features (basic categorization)
With API Key	1 call per note	All features + AI categorization

🔑 Rules Followed:
```
✅ No API keys in code

✅ Public repository

✅ 3 course concepts demonstrated

✅ README.md included
```

🎓 Submission
```
Kaggle Writeup: Problem + Solution + Architecture

GitHub Repository: Code + README

Video Demo (optional, +10 bonus points)
```
📝 License

MIT

