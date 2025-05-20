import os
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from openai import OpenAI
from elevenlabs import ElevenLabs, VoiceSettings
import cloudinary
import cloudinary.uploader

# === Initialiseer externe API clients ===

# OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ElevenLabs
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
voice_id = os.getenv("ELEVEN_VOICE_ID")
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True
)

# Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# === FastAPI setup ===

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("text")
        print(f"📥 Ontvangen user_input: {user_input!r}")

        if not user_input or not isinstance(user_input, str):
            print("⚠️ Ongeldige of lege invoer
