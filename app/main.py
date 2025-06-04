from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import requests
import os
import cloudinary
import cloudinary.uploader
from openai import OpenAI

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init clients
client = OpenAI()
eleven_client = ElevenLabs()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

voice_id = "YUdpWWny7k5yb4QCeweX"  # Ruth

def convert_text_to_audio(text):
    audio = eleven_client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        text=text,
        optimize_streaming_latency=0
    )
    return b"".join(audio)  # Join the generator output

def upload_to_cloudinary(audio_bytes):
    temp_filename = f"temp_{uuid4()}.mp3"
    with open(temp_filename, "wb") as f:
        f.write(audio_bytes)

    result = cloudinary.uploader.upload(temp_filename, resource_type="video")
    os.remove(temp_filename)
    return result["secure_url"]

@app.post("/upload_url")
async def upload_url(request: Request, url: str = Form(...)):
    try:
        print(f"🌐 URL ontvangen: {url}")

        response = requests.get(url)
        text = "Bedankt voor het delen van de pagina. Ik zal je helpen."  # placeholder

        audio_bytes = convert_text_to_audio(text)
        audio_url = upload_to_cloudinary(audio_bytes)

        return {"audio_url": audio_url, "text": text}

    except Exception as e:
        print(f"❌ Fout in /upload_url: {e}")
        return {"error": str(e)}

@app.post("/ask")
async def ask(request: Request, url: str = Form(...)):
    try:
        print(f"🌐 URL ontvangen: {url}")

        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        print(f"🧠 Prompt gegenereerd.")

        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame assistent."},
                {"role": "user", "content": text}
            ]
        )

        text_response = gpt_response.choices[0].message.content.strip()
        print(f"🗣️ TTS starten...")

        audio_bytes = convert_text_to_audio(text_response)
        audio_url = upload_to_cloudinary(audio_bytes)

        return {"audio_url": audio_url, "text": text_response}

    except Exception as e:
        print(f"❌ Fout in /ask: {e}")
        return {"error": str(e)}
