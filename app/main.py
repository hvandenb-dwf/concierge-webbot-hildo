from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import text_to_speech
import tempfile
import cloudinary
import cloudinary.uploader
import os

app = FastAPI()

# CORS voor frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Of specifieker: ["https://concierge-frontend-dng1.onrender.com"]
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

@app.post("/ask")
async def ask(file: UploadFile = File(...), session_id: str = Form(...)):
    try:
        # 1. Opslaan audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # 2. Whisper → tekst
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp_path, "rb")
        )
        prompt = transcription.text

        # 3. GPT → antwoord
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = chat_response.choices[0].message.content

        # 4. ElevenLabs → audio
        audio = text_to_speech.convert(
            text=answer,
            voice_id="YUdpWWny7k5yb4QCeweX"  # Ruth
        )

        # 5. Upload naar Cloudinary
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as out:
            out.write(audio)
            out_path = out.name

        upload_result = cloudinary.uploader.upload(out_path, resource_type="video")
        audio_url = upload_result.get("secure_url")

        return {"audio_url": audio_url}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/upload_url")
async def upload_url(request: Request):
    try:
        data = await request.json()
        url = data.get("url")
        session_id = data.get("session_id")

        # Basic bevestiging
        response_text = f"Ik heb de website {url} genoteerd."

        # ElevenLabs → audio
        audio = text_to_speech.convert(
            text=response_text,
            voice_id="YUdpWWny7k5yb4QCeweX"
        )

        # Upload naar Cloudinary
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as out:
            out.write(audio)
            out_path = out.name

        upload_result = cloudinary.uploader.upload(out_path, resource_type="video")
        audio_url = upload_result.get("secure_url")

        return {"audio_url": audio_url}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
