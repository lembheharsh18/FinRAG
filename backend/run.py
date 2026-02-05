"""
Development server runner for FinRAG.

Run this file directly to start the development server:
    python run.py

Or use uvicorn directly:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
