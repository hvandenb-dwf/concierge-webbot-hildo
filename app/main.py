from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from openai import OpenAI
from elevenlabs.client import ElevenLabs, TextToSpeech
import cloudinary
import cloudinary.uploader
import uuid
import tempfile
import requests

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Voor productie: beperk dit tot je frontend domein
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ElevenLabs client
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

@app.post("/ask")
async def ask_question(request: Request):
    data = await request.json()
    user_input = data.get("message", "")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."},
            {"role": "user", "content": user_input},
        ]
    )
    reply = response.choices[0].message.content

    tts = TextToSpeech()
    audio = tts.convert(
        text=reply,
        voice=os.getenv("ELEVEN_VOICE_ID", "YUdpWWny7k5yb4QCeweX"),  # Ruth
        model_id="eleven_multilingual_v2",
        output_format="mp3"
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio)
        tmp_path = tmp.name

    upload_result = cloudinary.uploader.upload(tmp_path, resource_type="video")
    audio_url = upload_result.get("secure_url")

    return JSONResponse(content={"audio_url": audio_url, "reply": reply})

@app.post("/upload_url")
async def upload_url(url: str = Form(...)):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Vat de pagina samen in één zin."},
            {"role": "user", "content": f"Samenvatting van deze pagina: {url}"},
        ]
    )
    summary = response.choices[0].message.content

    tts = TextToSpeech()
    audio = tts.convert(
        text=summary,
        voice=os.getenv("ELEVEN_VOICE_ID", "YUdpWWny7k5yb4QCeweX"),  # Ruth
        model_id="eleven_multilingual_v2",
        output_format="mp3"
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio)
        tmp_path = tmp.name

    upload_result = cloudinary.uploader.upload(tmp_path, resource_type="video")
    audio_url = upload_result.get("secure_url")

    return JSONResponse(content={"audio_url": audio_url, "summary": summary})
