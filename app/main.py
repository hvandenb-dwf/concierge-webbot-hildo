from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from elevenlabs.client import ElevenLabs, TextToSpeech
from pydantic import BaseModel
from uuid import uuid4
import cloudinary
import cloudinary.uploader
import os
import requests

app = FastAPI()

# CORS configuratie
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ElevenLabs client initialisatie
voice_id = os.getenv("ELEVEN_VOICE_ID")
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
tts_client = TextToSpeech(client=eleven_client)

# Cloudinary configuratie
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

class UploadRequest(BaseModel):
    url: str

@app.post("/upload_url")
async def upload_url(data: UploadRequest):
    print("🌐 URL ontvangen:", data.url)
    html = requests.get(data.url).text
    
    response_text = "Bedankt voor je bericht. We hebben je link ontvangen en gaan ermee aan de slag."

    try:
        audio_bytes = tts_client.text_to_speech(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            optimize_streaming_latency=1,
            text=response_text
        )
    except Exception as e:
        print("❌ Fout in TTS:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

    temp_file_path = f"/tmp/{uuid4()}.mp3"
    with open(temp_file_path, "wb") as f:
        f.write(audio_bytes)

    try:
        upload_result = cloudinary.uploader.upload(temp_file_path, resource_type="video")
        audio_url = upload_result["secure_url"]
    except Exception as e:
        print("❌ Cloudinary fout:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

    print("✅ Upload voltooid:", audio_url)
    return {"audio_url": audio_url}

@app.get("/")
def root():
    return {"message": "Voicebot backend is live."}
