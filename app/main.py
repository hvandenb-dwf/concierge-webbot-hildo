from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
from openai import OpenAI
from uuid import uuid4
import cloudinary
import requests
import os
import hashlib
import time
import hmac

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment vars
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
voice_id = os.getenv("VOICE_ID") or "YUdpWWny7k5yb4QCeweX"  # Ruth

CLOUDINARY_UPLOAD_URL = f"https://api.cloudinary.com/v1_1/{cloudinary.config().cloud_name}/auto/upload"

@app.post("/upload_url")
async def upload_url(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}
    print(f"🌐 URL ontvangen: {url}")

    # Simuleer reactie
    text_response = "Ik heb de website bekeken. Wat wil je precies weten?"
    print(f"🧠 Prompt gegenereerd.")

    audio = convert_text_to_audio(text_response)
    audio_url = upload_to_cloudinary(audio)

    return {"audio_url": audio_url, "response": text_response}

def convert_text_to_audio(text: str) -> bytes:
    audio = eleven_client.text_to_speech.convert(
        voice=Voice(voice_id=voice_id),
        model="eleven_multilingual_v2",
        text=text,
    )
    return audio.read()

def upload_to_cloudinary(audio_bytes: bytes, public_id: str = None) -> str:
    timestamp = int(time.time())
    params_to_sign = {
        'timestamp': timestamp,
        'folder': 'voicebot',
        'public_id': public_id or str(uuid4()),
    }

    signature_string = '&'.join([f"{k}={v}" for k, v in sorted(params_to_sign.items())])
    signature = hmac.new(
        os.getenv("CLOUDINARY_API_SECRET").encode(),
        signature_string.encode(),
        hashlib.sha1
    ).hexdigest()

    payload = {
        **params_to_sign,
        'signature': signature,
        'api_key': os.getenv("CLOUDINARY_API_KEY")
    }

    files = {
        'file': ('response.mp3', audio_bytes, 'audio/mpeg')
    }

    response = requests.post(CLOUDINARY_UPLOAD_URL, data=payload, files=files)
    response.raise_for_status()
    print(f"✅ Upload voltooid: {response.json()['secure_url']}")
    return response.json()["secure_url"]
