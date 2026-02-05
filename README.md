# FinRAG 📊

**RAG-based Financial Document QA System for Retail Investors**

FinRAG is a full-stack web application that allows retail investors to upload financial documents (PDFs) and ask natural language questions about their contents using AI-powered retrieval-augmented generation (RAG).

## 🚀 Features

- 📄 **PDF Document Processing** - Upload and parse financial documents including annual reports, 10-K filings, earnings reports
- 🔍 **Semantic Search** - Find relevant information using natural language queries
- 💬 **AI-Powered Q&A** - Get accurate answers with GPT-4
- 📊 **Table Extraction** - Intelligent extraction of financial tables and data
- 🔐 **Secure Authentication** - Firebase or Supabase authentication

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Vector Database**: ChromaDB
- **LLM**: OpenAI GPT-4
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **PDF Processing**: PyPDF2, pdfplumber, Camelot

### Frontend
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Firebase Auth / Supabase Auth

## 📁 Project Structure

```
FinRAG/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── config.py        # Configuration and settings
│   │   └── api/
│   │       ├── __init__.py
│   │       └── health.py    # Health check endpoints
│   ├── run.py               # Development server runner
│   └── .env.example         # Environment variables template
├── frontend/                 # React TypeScript frontend (coming soon)
├── requirements.txt          # Python dependencies
├── .env.example             # Root environment template
├── .gitignore
└── README.md
```

## 🏃‍♂️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- OpenAI API key

### Backend Setup

1. **Clone the repository**
   ```bash
   cd FinRAG
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the development server**
   ```bash
   python run.py
   ```

6. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with app info |
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Detailed health with dependencies |

## 🔧 Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | GPT model to use | gpt-4 |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | ./chroma_db |
| `AUTH_PROVIDER` | Auth provider (firebase/supabase) | firebase |

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
