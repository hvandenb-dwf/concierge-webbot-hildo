from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uuid import uuid4
import os
import time
import cloudinary
import cloudinary.uploader
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import TextToSpeechClient, Voice, AudioOutputFormat
from dotenv import load_dotenv

load_dotenv()

# Init FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Init clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
tts = TextToSpeechClient(api_key=os.getenv("ELEVEN_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

voice_id = os.getenv("ELEVEN_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # default to 'Ruth' if not set

@app.post("/upload_url")
async def upload_url(request: Request):
    try:
        body = await request.json()
        url = body.get("url")
        session_id = body.get("session_id", str(uuid4()))
        print(f"🌐 URL ontvangen: {url}, session_id: {session_id}")

        # Simuleer eenvoudige tekstresponse
        text = "Welkom op de website. Wat kan ik voor je doen?"

        start_time = time.time()
        audio_bytes = tts.convert(
            voice=Voice(voice_id=voice_id),
            model="eleven_multilingual_v2",
            output_format=AudioOutputFormat.MP3_44100,
            text=text
        )
        print("💬 Prompt gegenereerd.")

        # Upload naar Cloudinary
        temp_filename = f"/tmp/{uuid4()}.mp3"
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)

        result = cloudinary.uploader.upload(temp_filename, resource_type="video")
        audio_url = result["secure_url"]
        os.remove(temp_filename)

        return {"audio_url": audio_url, "text": text, "session_id": session_id}

    except Exception as e:
        print("⚠️ Fout in /upload_url:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/ask")
async def ask(request: Request):
    try:
        body = await request.json()
        user_input = body.get("text")
        session_id = body.get("session_id", str(uuid4()))
        print(f"📥 Prompt ontvangen: {user_input}, sessie: {session_id}")

        chat_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."},
                {"role": "user", "content": user_input}
            ]
        )

        reply = chat_response.choices[0].message.content

        audio_bytes = tts.convert(
            voice=Voice(voice_id=voice_id),
            model="eleven_multilingual_v2",
            output_format=AudioOutputFormat.MP3_44100,
            text=reply
        )

        temp_filename = f"/tmp/{uuid4()}.mp3"
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)

        result = cloudinary.uploader.upload(temp_filename, resource_type="video")
        audio_url = result["secure_url"]
        os.remove(temp_filename)

        return {"audio_url": audio_url, "text": reply, "session_id": session_id}

    except Exception as e:
        print("❌ Fout in /ask:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
