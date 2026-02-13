# FinRAG - Financial Document Analysis System

FinRAG is an AI-powered financial document analysis system that leverages Retrieval-Augmented Generation (RAG) to provide insights, summaries, and answers from financial reports, earnings calls, and other documents.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Deployment Server**: Uvicorn
- **AI/LLM**: OpenAI (GPT-4), LangChain
- **Vector Database**: ChromaDB (Semantic Search)
- **PDF Processing**: PyPDF2, pdfplumber, Camelot (for tables)
- **Authentication**: Firebase Admin SDK
- **Task Management**: Tenacity (Retries)
- **Utilities**: Pandas, NumPy

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS + Vanilla CSS (Glassmorphism Design)
- **State Management & Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router DOM v6
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Authentication**: Firebase Client SDK
- **HTTP Client**: Axios

## Prerequisites

- **Python**: 3.9+
- **Node.js**: 18+
- **API Keys**:
  - OpenAI API Key (or Groq API Key)
  - Firebase Project Configuration
  - (Optional) Render/Vercel for deployment

## Interface & Features

1.  **Smart Chat**: Context-aware Q&A with documents.
2.  **Streaming Answers**: Real-time token streaming.
3.  **AI Summaries**: structured executive summaries with sentiment analysis.
4.  **Financial Dashboards**: Auto-extracted metrics and ratios.
5.  **Multi-Doc Comparison**: Side-by-side analysis of multiple reports.
6.  **Analytics**: Usage stats and query performance tracking.
7.  **Alerts**: Price alerts and ticker extraction.
8.  **Export**: Download conversation reports as Markdown.

## How to Run Locally

### 1. Backend Setup

1.  Navigate to the project root (or `backend/` directory if preferred, but `requirements.txt` is in root).
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in `backend/` based on `.env.example`:
    ```ini
    OPENAI_API_KEY=your_key_here
    # ... other config/firebase credentials
    ```
5.  Run the server:
    ```bash
    cd backend
    python run.py
    # OR
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API will be available at `http://localhost:8000`. API Docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

1.  Open a new terminal and navigate to `frontend/`:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Ensure `.env` (or `.env.local`) exists with Firebase config (VITE_FIREBASE_*).
4.  Run the development server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

## Architecture

- **Backend (`backend/app/`)**: REST API server.
    - `api/`: Endpoints (Documents, Chat, Auth, Analytics, etc.)
    - `services/`: Business logic (LLM, Vector Store, PDF Processing)
    - `models/`: Pydantic schemes.
- **Frontend (`frontend/src/`)**: SPA Client.
    - `components/`: Reusable UI components.
    - `pages/`: Route views.
    - `hooks/`: Custom React hooks.
    - `lib/`: API clients and utilities.
