from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from database import init_db
from handlers.chat import router as chat_router
from handlers.video import router as video_router
from handlers.audio import router as audio_router

app = FastAPI(title="AI Video Maker Studio")

# Include routers
app.include_router(chat_router)
app.include_router(video_router)
app.include_router(audio_router)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html", "r") as f:
        return f.read()
