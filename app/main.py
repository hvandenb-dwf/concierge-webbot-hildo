from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import text_to_speech
import cloudinary
import cloudinary.uploader
import os
import tempfile
from uuid import uuid4

# ========== INIT ==========

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Ruth

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# ========== /UPLOAD_URL ==========

@app.post("/upload_url")
async def upload_url(url: str = Form(...), session_id: str = Form(...)):
    prompt = f"Geef een vriendelijke samenvatting in het Nederlands van wat je vindt op {url}."
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Je bent een behulpzame Nederlandse voice-assistent."},
            {"role": "user", "content": prompt}
        ]
    )
    text = response.choices[0].message.content.strip()

    audio = text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
        temp.write(audio)
        temp_path = temp.name

    upload_result = cloudinary.uploader.upload(temp_path, resource_type="video")
    audio_url = upload_result["secure_url"]

    return JSONResponse(content={"text": text, "audio_url": audio_url})


# ========== /ASK ==========

@app.post("/ask")
async def ask(audio: UploadFile, session_id: str = Form(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    transcript_response = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(tmp_path, "rb"),
        response_format="text"
    )
    user_input = transcript_response.strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Je bent een behulpzame Nederlandse voice-assistent."},
            {"role": "user", "content": user_input}
        ]
    )
    reply = response.choices[0].message.content.strip()

    audio = text_to_speech.convert(
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=reply
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
        temp.write(audio)
        temp_path = temp.name

    upload_result = cloudinary.uploader.upload(temp_path, resource_type="video")
    audio_url = upload_result["secure_url"]

    return JSONResponse(content={"text": reply, "audio_url": audio_url})
