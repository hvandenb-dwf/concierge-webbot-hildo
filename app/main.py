from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from cloudinary.uploader import upload as cloudinary_upload
from cloudinary.utils import cloudinary_url
import os
import uuid

# Load environment variables
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS instellingen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

@app.post("/upload_url")
async def upload_url(request: Request):
    form = await request.form()
    url = form.get("url")
    if not url:
        return JSONResponse(content={"error": "Missing 'url'"}, status_code=400)

    text = f"Bedankt voor het insturen van deze website. Ik heb '{url}' ontvangen en zal het bekijken."
    audio = eleven_client.generate(
        text=text,
        voice=VOICE_ID
    )

    filename = f"{uuid.uuid4()}.mp3"
    with open(filename, "wb") as f:
        f.write(audio)

    cloudinary_result = cloudinary_upload(filename, resource_type="video")
    audio_url, _ = cloudinary_url(cloudinary_result["public_id"], resource_type="video")

    os.remove(filename)

    return JSONResponse(content={"audio_url": audio_url})


@app.post("/ask")
async def ask(request: Request):
    form = await request.form()
    prompt = form.get("prompt")

    if not prompt:
        return JSONResponse(content={"error": "Missing prompt"}, status_code=400)

    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4"
    )
    reply = completion.choices[0].message.content

    audio = eleven_client.generate(
        text=reply,
        voice=VOICE_ID
    )

    filename = f"{uuid.uuid4()}.mp3"
    with open(filename, "wb") as f:
        f.write(audio)

    cloudinary_result = cloudinary_upload(filename, resource_type="video")
    audio_url, _ = cloudinary_url(cloudinary_result["public_id"], resource_type="video")

    os.remove(filename)

    return JSONResponse(content={"reply": reply, "audio_url": audio_url})
