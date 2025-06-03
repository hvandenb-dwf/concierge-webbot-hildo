from fastapi import FastAPI, Request, Form
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

# === ROUTES ===
@app.post("/upload_url")
async def upload_url(url: str = Form(...), session_id: str = Form(...)):
    print("🌐 URL ontvangen:", url, "session_id:", session_id)

    try:
        # 1. Haal HTML op
        html = requests.get(url, timeout=5).text

        # 2. Genereer reactie met GPT
        prompt = f"Geef een korte vriendelijke samenvatting van deze pagina: {html[:2000]}"
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        antwoord = gpt_response.choices[0].message.content

        # 3. Zet om naar audio met ElevenLabs
        audio = tts.text_to_speech.convert(
            voice_id="YUdpWWny7k5yb4QCeweX",
            model_id="eleven_multilingual_v2",
            text=antwoord
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio)
            audio_path = f.name

        # 4. Upload naar Cloudinary
        cloud_result = cloudinary.uploader.upload(
            audio_path,
            resource_type="video",
            folder="concierge_audio",
            public_id=f"reply_{session_id}_{str(uuid4())[:8]}"
        )

        os.remove(audio_path)

        return {"audio_url": cloud_result["secure_url"], "text": antwoord}

    except Exception as e:
        print("❌ Fout in /upload_url:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    user_input = data.get("question", "")
    session_id = data.get("session_id", str(uuid4()))

    print("🤖 Vraag ontvangen:", user_input, "| session_id:", session_id)

    try:
        # 1. Antwoord van GPT ophalen
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}]
        )
        antwoord = gpt_response.choices[0].message.content

        # 2. Audio genereren
        audio = tts.text_to_speech.convert(
            voice_id="YUdpWWny7k5yb4QCeweX",
            model_id="eleven_multilingual_v2",
            text=antwoord
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio)
            audio_path = f.name

        # 3. Upload naar Cloudinary
        cloud_result = cloudinary.uploader.upload(
            audio_path,
            resource_type="video",
            folder="concierge_audio",
            public_id=f"ask_{session_id}_{str(uuid4())[:8]}"
        )

        os.remove(audio_path)

        return {"audio_url": cloud_result["secure_url"], "text": antwoord}

    except Exception as e:
        print("❌ Fout in /ask:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
