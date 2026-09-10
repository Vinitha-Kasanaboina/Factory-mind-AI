# FactoryMind AI: Industrial Memory & Knowledge Intelligence Platform

FactoryMind AI is a modern, AI-powered knowledge management and retrieval platform designed for manufacturing and industrial environments. It captures, digitizes, indexes, and retrieves critical operational knowledge (SOPs, maintenance guides, machine manuals, troubleshooting procedures, and safety protocols) using OCR, SentenceTransformers vector embeddings, FAISS vector search, and a context-aware RAG AI Chatbot.

---

## Key Features

- **Role-Based Access Control (RBAC)**: Custom User Model with 3 distinct operational roles:
  - **Admin**: System management, user assignment, document purging, full platform control.
  - **Engineer**: Upload SOPs, run OCR parsing, re-index FAISS vector DB, manage categories.
  - **Technician**: Search knowledge base, query AI assistant, inspect page citations, download SOPs.
- **Multiformat Ingestion & OCR**: Supports PDF, Word (`.docx`), Images (`.png`, `.jpg`), and TXT/Markdown documents with automatic text extraction (PyMuPDF & Tesseract OCR).
- **Automated Text Chunking & Summarization**: Splits documents into page-mapped overlapping passages and auto-generates extractive executive summaries.
- **FAISS Vector Search**: High-performance semantic vector similarity search using `sentence-transformers/all-MiniLM-L6-v2`.
- **Context-Aware RAG AI Chatbot**: Technical Q&A assistant providing direct page-level document citations with local intelligent fallback.
- **Executive Industrial Dashboard**: Real-time analytics showing total SOPs, FAISS chunks, category breakdowns, and user activity.
- **Responsive Industrial UI**: Dark/slate modern design system built with Bootstrap 5, custom CSS, AJAX dynamic chat, and glassmorphism cards.

---

## Project Structure

```
django(1)/
├── factorymind/          # Core Django project settings & URL routing
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/             # Custom User model, Roles (Admin/Engineer/Technician), Auth views
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── knowledge/            # Document Store, OCR Extraction & FAISS Vector Indexing Service
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── services/
│       ├── ocr.py        # Text extraction (PyMuPDF, docx, pytesseract)
│       └── vector_store.py # SentenceTransformers & FAISS Vector Manager
├── chatbot/              # RAG Q&A Engine & Dynamic Chat Interface
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── services/
│       └── rag_engine.py # Retrieval-Augmented Generation pipeline
├── dashboard/            # Analytics & Operational Intelligence Overview
│   ├── views.py
│   └── urls.py
├── templates/            # HTML5 Bootstrap 5 Templates
│   ├── base.html
│   ├── accounts/
│   ├── knowledge/
│   ├── chatbot/
│   └── dashboard/
├── static/               # Platform Stylesheets & JavaScript
│   ├── css/custom.css
│   └── js/main.js
├── media/                # Storage directory for uploaded SOP files
├── seed_data.py          # Demo database seeder script
├── requirements.txt      # Dependency manifest
├── manage.py             # Django entrypoint script
└── README.md             # Project documentation
```

---

## Setup & Running Instructions

### 1. Open Terminal & Navigate to Project Directory
```bash
cd Desktop/django(1)
```

### 2. Create & Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell / CMD)
venv\Scripts\activate

# Activate on Linux / macOS
# source venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Demo Data & Demo Users (Recommended)
Run the automated seed script to populate default categories, sample industrial SOPs, FAISS index, and demo accounts:
```bash
python seed_data.py
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to: `http://127.0.0.1:8000/`

---

## Default Demo Credentials (after running `seed_data.py`)

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `admin123` | Full Access + Django Admin |
| **Process Engineer** | `engineer` | `engineer123` | Upload SOPs, Run OCR, Vector Indexing |
| **Field Technician** | `technician` | `tech123` | Search SOPs, AI Chatbot, View Documents |

---

## License & Support
FactoryMind AI - Built for Industrial Memory & Knowledge Intelligence.
