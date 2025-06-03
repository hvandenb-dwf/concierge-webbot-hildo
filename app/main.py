from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from uuid import uuid4
import cloudinary
import cloudinary.uploader
from elevenlabs import ElevenLabs, TextToSpeech
import os
import requests

# === Initialisatie ===
app = FastAPI()

# === CORS instellingen ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === OpenAI client ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === ElevenLabs client ===
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
tts = TextToSpeech(client=eleven_client)

# === Cloudinary configuratie ===
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# === Request body model ===
class AskRequest(BaseModel):
    text: str

# === Endpoint: /ask ===
@app.post("/ask")
async def ask(req: AskRequest):
    # Genereer antwoord via OpenAI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": req.text}],
    )
    answer = response.choices[0].message.content

    # Converteer tekst naar audio via ElevenLabs
    audio = tts.convert(
        voice_id="YUdpWWny7k5yb4QCeweX",
        model_id="eleven_multilingual_v2",
        text=answer,
    )

    # Upload naar Cloudinary
    temp_filename = f"/tmp/{uuid4()}.mp3"
    with open(temp_filename, "wb") as f:
        f.write(audio)
    result = cloudinary.uploader.upload(temp_filename, resource_type="video")

    return {"audio_url": result["secure_url"], "text": answer}

# === Endpoint: /upload_url ===
@app.post("/upload_url")
async def upload_url(url: str = Form(...)):
    # Genereer vaste reactie
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": f"Bekijk deze pagina: {url}. Vat samen in het Nederlands."}
        ],
    )
    answer = response.choices[0].message.content

    # Zet om naar audio
    audio = tts.convert(
        voice_id="YUdpWWny7k5yb4QCeweX",
        model_id="eleven_multilingual_v2",
        text=answer,
    )

    # Upload naar Cloudinary
    temp_filename = f"/tmp/{uuid4()}.mp3"
    with open(temp_filename, "wb") as f:
        f.write(audio)
    result = cloudinary.uploader.upload(temp_filename, resource_type="video")

    return {"audio_url": result["secure_url"], "text": answer}
