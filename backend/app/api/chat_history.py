"""
Chat History API endpoints for FinRAG.

Provides persistent chat history using JSON file storage.
Each user gets a directory, each document gets a file of sessions.
"""

import os
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.config import get_settings
from app.middleware.auth import get_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat History"])
settings = get_settings()

HISTORY_DIR = os.path.join(settings.upload_directory, "chat_history")


def _get_user_history_path(user_id: str) -> str:
    """Get the history file path for a user."""
    user_dir = os.path.join(HISTORY_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def _load_sessions(user_id: str, document_id: str) -> List[Dict[str, Any]]:
    """Load sessions for a user/document pair."""
    path = os.path.join(_get_user_history_path(user_id), f"{document_id}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_sessions(user_id: str, document_id: str, sessions: List[Dict[str, Any]]):
    """Save sessions for a user/document pair."""
    path = os.path.join(_get_user_history_path(user_id), f"{document_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, default=str)


# ── Models ────────────────────────────────────────────

class MessageModel(BaseModel):
    role: str = Field(..., description="'user' or 'ai'")
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[str] = None


class SessionSummary(BaseModel):
    session_id: str
    document_id: str
    title: str
    message_count: int
    created_at: str
    updated_at: str


class SessionDetail(BaseModel):
    session_id: str
    document_id: str
    title: str
    messages: List[MessageModel]
    created_at: str
    updated_at: str


class SaveMessageRequest(BaseModel):
    role: str = Field(..., description="'user' or 'ai'")
    content: str
    sources: Optional[List[Dict[str, Any]]] = None


# ── Endpoints ─────────────────────────────────────────

@router.get(
    "/sessions/{document_id}",
    response_model=List[SessionSummary],
    summary="List Chat Sessions",
    description="Get all chat sessions for a specific document."
)
async def list_sessions(
    document_id: str,
    user_id: str = Depends(get_user_id)
):
    """List all conversation sessions for a document."""
    sessions = _load_sessions(user_id, document_id)
    return [
        SessionSummary(
            session_id=s["session_id"],
            document_id=document_id,
            title=s.get("title", "Untitled Chat"),
            message_count=len(s.get("messages", [])),
            created_at=s.get("created_at", ""),
            updated_at=s.get("updated_at", ""),
        )
        for s in sessions
    ]


@router.post(
    "/sessions/{document_id}",
    summary="Create New Session",
    description="Create a new chat session for a document."
)
async def create_session(
    document_id: str,
    user_id: str = Depends(get_user_id)
):
    """Create a new chat session."""
    sessions = _load_sessions(user_id, document_id)
    
    session = {
        "session_id": str(uuid.uuid4()),
        "title": "New Chat",
        "messages": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    sessions.append(session)
    _save_sessions(user_id, document_id, sessions)
    
    return {
        "session_id": session["session_id"],
        "document_id": document_id,
        "title": session["title"],
        "created_at": session["created_at"],
    }


@router.get(
    "/sessions/{document_id}/{session_id}",
    response_model=SessionDetail,
    summary="Get Session Messages",
    description="Get all messages in a chat session."
)
async def get_session(
    document_id: str,
    session_id: str,
    user_id: str = Depends(get_user_id)
):
    """Get messages for a specific session."""
    sessions = _load_sessions(user_id, document_id)
    
    for s in sessions:
        if s["session_id"] == session_id:
            return SessionDetail(
                session_id=s["session_id"],
                document_id=document_id,
                title=s.get("title", "Untitled Chat"),
                messages=[MessageModel(**m) for m in s.get("messages", [])],
                created_at=s.get("created_at", ""),
                updated_at=s.get("updated_at", ""),
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Session not found"
    )


@router.post(
    "/sessions/{document_id}/{session_id}/messages",
    summary="Save Message",
    description="Add a message to a chat session."
)
async def save_message(
    document_id: str,
    session_id: str,
    request: SaveMessageRequest,
    user_id: str = Depends(get_user_id)
):
    """Save a message to a session."""
    sessions = _load_sessions(user_id, document_id)
    
    for s in sessions:
        if s["session_id"] == session_id:
            message = {
                "role": request.role,
                "content": request.content,
                "sources": request.sources,
                "timestamp": datetime.utcnow().isoformat(),
            }
            s["messages"].append(message)
            s["updated_at"] = datetime.utcnow().isoformat()
            
            # Auto-title from first user message
            if request.role == "user" and s.get("title", "New Chat") == "New Chat":
                s["title"] = request.content[:60] + ("..." if len(request.content) > 60 else "")
            
            _save_sessions(user_id, document_id, sessions)
            return {"status": "saved", "message_count": len(s["messages"])}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Session not found"
    )


@router.delete(
    "/sessions/{document_id}/{session_id}",
    summary="Delete Session",
    description="Delete a chat session."
)
async def delete_session(
    document_id: str,
    session_id: str,
    user_id: str = Depends(get_user_id)
):
    """Delete a conversation session."""
    sessions = _load_sessions(user_id, document_id)
    sessions = [s for s in sessions if s["session_id"] != session_id]
    _save_sessions(user_id, document_id, sessions)
    return {"status": "deleted", "session_id": session_id}
