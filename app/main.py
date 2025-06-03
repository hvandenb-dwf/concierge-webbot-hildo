from fastapi import FastAPI, Request, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from elevenlabs import ElevenLabs
from elevenlabs.text_to_speech import TextToSpeech
from elevenlabs import Voice
import cloudinary
import cloudinary.uploader
import os
import tempfile
import uuid
import requests
import shutil

# === CONFIGURATIE ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
tts = TextToSpeech(client=eleven)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

VOICE_ID = "YUdpWWny7k5yb4QCeweX"  # Ruth

# === HELPER FUNCTIES ===
def generate_gpt_response(user_input):
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Beantwoord alles in het Nederlands."},
            {"role": "user", "content": user_input}
        ]
    )
    return chat_completion.choices[0].message.content.strip()

def text_to_audio_url(text: str):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.convert(
            text=text,
            voice=Voice(voice_id=VOICE_ID),
            output_path=f.name
        )
        upload_result = cloudinary.uploader.upload(f.name, resource_type="video")
        return upload_result["secure_url"]

# === API MODEL ===
class UploadRequest(BaseModel):
    url: str
    session_id: str

# === ENDPOINTS ===
@app.post("/upload_url")
async def upload_url(request: UploadRequest):
    # Simuleer scraping of ophalen van content
    text_response = f"Je vroeg informatie over {request.url}. Hier is een samenvatting: ..."
    audio_url = text_to_audio_url(text_response)
    return {"audio_url": audio_url, "text": text_response}

@app.post("/ask")
async def ask_audio(file: UploadFile, session_id: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Stuur audio naar Whisper (OpenAI)
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="nl"
            )

        gpt_response = generate_gpt_response(transcript)
        audio_url = text_to_audio_url(gpt_response)
        return {"audio_url": audio_url, "text": gpt_response}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def root():
    return {"status": "Voicebot backend draait correct."}
