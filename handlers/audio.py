from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import uuid
import os
from config import ELEVENLABS_API_KEY

router = APIRouter()

class AudioRequest(BaseModel):
    text: str

class AudioResponse(BaseModel):
    url: str

async def generate_audio(text: str) -> dict:
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (default)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to generate audio from ElevenLabs")
        audio_content = response.content
    # Save to static/audio/
    os.makedirs("static/audio", exist_ok=True)
    filename = f"{uuid.uuid4()}.mp3"
    filepath = f"static/audio/{filename}"
    with open(filepath, "wb") as f:
        f.write(audio_content)
    # Return URL relative to static
    return {"url": f"/static/audio/{filename}"}

@router.post("/api/audio", response_model=AudioResponse)
async def audio_endpoint(request: AudioRequest):
    return await generate_audio(request.text)
