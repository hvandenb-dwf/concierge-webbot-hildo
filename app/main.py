from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from elevenlabs import Voice
from elevenlabs.client import ElevenLabs
import os
import cloudinary
import cloudinary.uploader
import tempfile
from uuid import uuid4

app = FastAPI()

# CORS voor frontend toegang
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><body>
    <h2>✅ Webbot is actief</h2>
    </body></html>
    """

@app.post("/upload_url")
async def upload_url(url: str = Form(...), session_id: str = Form(...)):
    print(f"🌐 URL ontvangen: {url}, session_id: {session_id}")

    try:
        html = fetch_url_html(url)
        prompt = f"Vat de volgende website samen in gewone spreektaal voor een klant: {html}"
        text_response = generate_bot_reply(prompt)
        audio_url = upload_to_cloudinary(convert_text_to_audio(text_response))
        return {"text": text_response, "audio_url": audio_url}

    except Exception as e:
        print(f"❌ Fout in /upload_url: {e}")
        return {"error": str(e)}

# Functies
def fetch_url_html(url):
    import requests
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    return response.text[:4000]

def generate_bot_reply(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Je bent een deskundige, vriendelijke Nederlandse voicebot."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def convert_text_to_audio(text: str, voice_id: str = "YUdpWWny7k5yb4QCeweX") -> bytes:
    voice = Voice(voice_id=voice_id)
    audio = eleven_client.text_to_speech.convert(
        voice=voice,
        text=text
    )
    return audio.read()

def upload_to_cloudinary(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio.flush()
        response = cloudinary.uploader.upload(temp_audio.name, resource_type="video")
        return response["secure_url"]
