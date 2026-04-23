from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from config import PIXABAY_API_KEY

router = APIRouter()

class VideoRequest(BaseModel):
    prompt: str

class VideoResponse(BaseModel):
    url: str
    thumbnail: str

async def generate_video(prompt: str) -> dict:
    if not PIXABAY_API_KEY:
        raise HTTPException(status_code=500, detail="Pixabay API key not configured")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://pixabay.com/api/videos/",
            params={"key": PIXABAY_API_KEY, "q": prompt, "per_page": 3}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch from Pixabay")
        data = response.json()
        hits = data.get("hits", [])
        if not hits:
            raise HTTPException(status_code=404, detail="No videos found")
        # Pick the first video's HD URL or standard
        video = hits[0]
        videos = video.get("videos", {})
        # Prefer large, then medium, then small
        for size in ["large", "medium", "small"]:
            if size in videos and videos[size].get("url"):
                url = videos[size]["url"]
                break
        else:
            url = videos.get("tiny", {}).get("url", "")
        thumbnail = video.get("thumbnail", "")
        return {"url": url, "thumbnail": thumbnail}

@router.post("/api/video", response_model=VideoResponse)
async def video_endpoint(request: VideoRequest):
    return await generate_video(request.prompt)
