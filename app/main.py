from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
import cloudinary
import cloudinary.uploader
import tempfile
import os

app = FastAPI()

# CORS
origins = [
    "https://concierge-frontend-dng1.onrender.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# Voice settings
voice = Voice(voice_id="YUdpWWny7k5yb4QCeweX")  # Ruth

def upload_to_cloudinary(file_path):
    result = cloudinary.uploader.upload(file_path, resource_type="video")
    return result["secure_url"]

@app.post("/upload_url")
async def upload_url():
    try:
        audio_stream = eleven_client.text_to_speech.convert(
            voice=voice,
            model="eleven_multilingual_v2",
            text="Hallo! Ik ben je digitale assistent. Hoe kan ik je helpen?"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_stream)
            tmp_path = tmp.name

        cloudinary_url = upload_to_cloudinary(tmp_path)
        os.remove(tmp_path)
        return {"cloudinary_url": cloudinary_url}
    except Exception as e:
        return {"error": str(e)}

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("question", "")
        if not user_input:
            return {"error": "No question provided."}

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame Nederlandse digitale assistent."},
                {"role": "user", "content": user_input},
            ]
        )
        bot_reply = gpt_response.choices[0].message.content

        audio_stream = eleven_client.text_to_speech.convert(
            voice=voice,
            model="eleven_multilingual_v2",
            text=bot_reply
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_stream)
            tmp_path = tmp.name

        cloudinary_url = upload_to_cloudinary(tmp_path)
        os.remove(tmp_path)
        return {"answer": bot_reply, "cloudinary_url": cloudinary_url}

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return HTMLResponse("<h1>Backend is actief</h1>")
