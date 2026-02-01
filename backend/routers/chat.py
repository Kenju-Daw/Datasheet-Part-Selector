"""
Chat Router - API endpoints for Guided Part Selector (GPS-001)
Handles chat sessions, message history, and LLM interaction.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from models import get_session, ChatSession, ChatMessage
from models.schemas import (
    ChatSessionCreate, ChatSessionResponse, 
    ChatMessageCreate, ChatMessageResponse
)
from services.chat_engine import process_user_message

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionCreate,
    session: AsyncSession = Depends(get_session)
):
    """Start a new chat session"""
    new_session = ChatSession(
        title=request.title or "New Conversation"
    )
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    
    # Return empty session
    return ChatSessionResponse(
        id=new_session.id,
        title=new_session.title,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        messages=[]
    )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    session: AsyncSession = Depends(get_session)
):
    """List recent chat sessions"""
    result = await session.execute(
        select(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
    )
    sessions = result.scalars().all()
    # We won't load messages for list view to save bandwidth
    return [ChatSessionResponse.model_validate(s) for s in sessions]

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get full chat history for a session"""
    result = await session.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Sort messages by date
    chat_session.messages.sort(key=lambda m: m.created_at)
    
    return ChatSessionResponse.model_validate(chat_session)

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    message: ChatMessageCreate,
    db_session: AsyncSession = Depends(get_session)
):
    """
    Send a message to the AI
    1. Saves user message
    2. Triggers AI response (GPS-001)
    3. Returns AI response
    """
    # Verify session exists
    result = await db_session.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session timestamp
    chat_session.updated_at = datetime.utcnow()
    
    # Process message logic (in service)
    # This saves both user message and assistant response
    assistant_msg = await process_user_message(
        db_session, 
        session_id, 
        message.content
    )
    
    return ChatMessageResponse.model_validate(assistant_msg)
