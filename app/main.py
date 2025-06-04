from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from uuid import uuid4
import os
import time
import tempfile
import requests
import cloudinary
import cloudinary.uploader
from elevenlabs.client import ElevenLabs

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Clients ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# === HELPERS ===
def transcribe_audio(audio_file):
    response = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1"
    )
    return response.text

def generate_gpt_reply(user_input):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_input}]
    )
    return response.choices[0].message.content

def convert_text_to_audio(text_response):
    response = tts.text_to_speech.convert(
        voice_id="YUdpWWny7k5yb4QCeweX",
        model_id="eleven_multilingual_v2",
        text=text_response
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        f.write(response.read())
        return f.name

def upload_to_cloudinary(audio_path, session_id):
    result = cloudinary.uploader.upload(
        audio_path,
        resource_type="video",
        folder="concierge_audio",
        public_id=f"ask_{session_id}_{str(uuid4())[:8]}"
    )
    os.remove(audio_path)
    return result["secure_url"]

# === ROUTES ===
@app.post("/upload_url")
async def upload_url(url: str = Form(...), session_id: str = Form(...)):
    print("🌐 URL ontvangen:", url, "session_id:", session_id)

    try:
        html = requests.get(url, timeout=5).text
        prompt = f"Geef een korte vriendelijke samenvatting van deze pagina: {html[:2000]}"
        text_response = generate_gpt_reply(prompt)
        audio_path = convert_text_to_audio(text_response)
        audio_url = upload_to_cloudinary(audio_path, session_id)
        return {"audio_url": audio_url, "text": text_response}
    except Exception as e:
        print("❌ Fout in /upload_url:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask")
async def ask(audio: UploadFile = Form(...), session_id: str = Form(...)):
    print("🎤 Vraag ontvangen van sessie:", session_id)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(await audio.read())
            audio_path = f.name

        with open(audio_path, "rb") as f:
            transcript = transcribe_audio(f)

        print("🧠 Transcript:", transcript)
        text_response = generate_gpt_reply(transcript)
        print("💬 GPT antwoord:", text_response)

        audio_path = convert_text_to_audio(text_response)
        audio_url = upload_to_cloudinary(audio_path, session_id)

        return {"audio_url": audio_url, "text": text_response}

    except Exception as e:
        print("❌ Fout in /ask:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
