from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db, Session, Message
from datetime import datetime
from handlers.video import generate_video
from handlers.audio import generate_audio
import re

router = APIRouter()

class MessageRequest(BaseModel):
    session_id: int
    content: str

class SessionCreate(BaseModel):
    pass

@router.get("/api/sessions")
async def get_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    sessions = result.scalars().all()
    return [{"id": s.id, "name": s.name, "created_at": s.created_at.isoformat()} for s in sessions]

@router.post("/api/sessions")
async def create_session(db: AsyncSession = Depends(get_db)):
    new_session = Session(name="New Chat")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return {"id": new_session.id, "name": new_session.name}

@router.get("/api/sessions/{session_id}/messages")
async def get_messages(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content, "timestamp": m.created_at.isoformat()} for m in messages]

@router.post("/api/chat")
async def chat(request: MessageRequest, db: AsyncSession = Depends(get_db)):
    # Save user message
    user_msg = Message(session_id=request.session_id, role="user", content=request.content)
    db.add(user_msg)
    await db.commit()
    
    # Process message
    content_lower = request.content.strip().lower()
    
    # Check for video command: /video <prompt>
    video_match = re.match(r"^/video\s+(.+)$", content_lower, re.IGNORECASE)
    if video_match:
        prompt = video_match.group(1)
        try:
            video_data = await generate_video(prompt)
            assistant_content = f"Generated video: {video_data['url']}"
        except Exception as e:
            assistant_content = f"Error generating video: {str(e)}"
    # Check for audio command: /audio <text>
    elif re.match(r"^/audio\s+(.+)$", content_lower, re.IGNORECASE):
        text_match = re.match(r"^/audio\s+(.+)$", request.content, re.IGNORECASE)
        text = text_match.group(1)
        try:
            audio_data = await generate_audio(text)
            assistant_content = f"Audio generated: {audio_data['url']}"
        except Exception as e:
            assistant_content = f"Error generating audio: {str(e)}"
    else:
        assistant_content = f"You said: {request.content}"
    
    # Save assistant message
    assistant_msg = Message(session_id=request.session_id, role="assistant", content=assistant_content)
    db.add(assistant_msg)
    await db.commit()
    
    # Update session name if first message
    msg_count = await db.scalar(select(Message).where(Message.session_id == request.session_id).count())
    if msg_count == 2:  # user + assistant = 2
        session = await db.get(Session, request.session_id)
        if session.name == "New Chat":
            # Use first few words of user message as name
            session.name = request.content[:30] + ("..." if len(request.content) > 30 else "")
            await db.commit()
    
    return {"role": "assistant", "content": assistant_content}
