from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import cloudinary
import cloudinary.uploader
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
from elevenlabs import TextToSpeech
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# ElevenLabs client setup
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
voice = Voice(voice_id="YUdpWWny7k5yb4QCeweX")
text_to_speech = TextToSpeech(client=eleven_client)

@app.post("/upload_url")
async def upload_url(request: Request, url: str = Form(...)):
    try:
        # Fetch content
        html = requests.get(url).text

        # Genereer antwoordtekst
        antwoord = "Ik heb de pagina gevonden en zal de inhoud verwerken."

        # Genereer audio
        audio_stream = text_to_speech.convert(
            voice=voice,
            model="eleven_multilingual_v2",
            text=antwoord,
        )
        audio_bytes = b"".join(audio_stream)

        # Upload naar Cloudinary
        upload_result = cloudinary.uploader.upload(
            audio_bytes,
            resource_type="video",
            format="mp3"
        )

        return {"url": upload_result["secure_url"]}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
