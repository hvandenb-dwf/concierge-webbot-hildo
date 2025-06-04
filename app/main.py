from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
import cloudinary
import cloudinary.uploader
import os
from uuid import uuid4

# === INIT ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

# === UTILS ===
def synthesize_audio(text: str) -> str:
    audio = eleven_client.text_to_speech.convert(
        voice=Voice(voice_id=VOICE_ID),
        model="eleven_multilingual_v2",
        text=text
    )

    filename = f"speech_{uuid4().hex}.mp3"
    with open(filename, "wb") as f:
        f.write(audio)

    upload = cloudinary.uploader.upload(filename, resource_type="video")
    os.remove(filename)
    return upload["secure_url"]

# === ROUTES ===
@app.get("/")
def read_root():
    return {"message": "Webbot backend active."}

@app.post("/upload_url")
async def upload_url(prompt: str = Form(...)):
    try:
        audio_url = synthesize_audio(prompt)
        return {"audio_url": audio_url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/ask")
async def ask(prompt: str = Form(...)):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content
        audio_url = synthesize_audio(answer)
        return {"answer": answer, "audio_url": audio_url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
