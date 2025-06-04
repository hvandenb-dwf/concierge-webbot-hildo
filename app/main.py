from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
from uuid import uuid4
import os
import tempfile
import requests
import cloudinary
import cloudinary.uploader
from bs4 import BeautifulSoup

# ✅ Init FastAPI
app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Je kunt dit beperken tot alleen je frontend domein
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ OpenAI en ElevenLabs clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
voice = Voice(voice_id="YUdpWWny7k5yb4QCeweX")  # Ruth

# ✅ Cloudinary configuratie
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# ✅ Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>✅ Voicebot backend draait.</h1>"

@app.post("/upload_url")
async def upload_url(url: str = Form(...), session_id: str = Form(...)):
    print(f"🌐 URL ontvangen: {url}, session_id: {session_id}")

    try:
        response = requests.get(url, timeout=10)
        html = response.text
    except Exception as e:
        return {"text": f"Fout bij ophalen URL: {e}", "audio_url": ""}

    soup = BeautifulSoup(html, 'html.parser')
    body_text = soup.body.get_text(separator=' ', strip=True)
    short_text = body_text[:300]

    prompt = f"Vat deze bedrijfsinformatie samen in maximaal 3 korte zinnen en spreek de bezoeker aan met 'je': {short_text}"
    print("🧠 Prompt gegenereerd.")

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een vriendelijke en professionele bedrijfsassistent."},
                {"role": "user", "content": prompt}
            ]
        )
        text_response = completion.choices[0].message.content
    except Exception as e:
        return {"text": f"Fout bij genereren samenvatting: {e}", "audio_url": ""}

    print("🔊 TTS starten...")
    audio_url = upload_to_cloudinary(convert_text_to_audio(text_response, voice=voice))

    return {"text": text_response, "audio_url": audio_url}

# ✅ Helpers
def convert_text_to_audio(text, voice):
    try:
        audio = eleven_client.text_to_speech.convert(
            voice=voice,
            text=text
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio.read())
            return tmp.name
    except Exception as e:
        print(f"Fout in TTS: {e}")
        return None

def upload_to_cloudinary(file_path):
    try:
        result = cloudinary.uploader.upload(file_path, resource_type="video")
        return result["secure_url"]
    except Exception as e:
        print(f"Fout bij uploaden naar Cloudinary: {e}")
        return ""
