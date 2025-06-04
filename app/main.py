from fastapi import FastAPI, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import aiohttp
import os
import cloudinary
import cloudinary.uploader
from uuid import uuid4
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
from openai import OpenAI
import tempfile
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Init clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def generate_bot_reply(user_input):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Je bent een behulpzame Nederlandse voice-assistent."},
            {"role": "user", "content": user_input},
        ]
    )
    return response.choices[0].message.content.strip()

def convert_text_to_audio(text, voice="Ruth"):
    audio = eleven_client.text_to_speech.convert(
        voice=voice,
        model="eleven_multilingual_v2",
        optimize_streaming_latency=1,
        text=text
    )
    return audio

def upload_to_cloudinary(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file_path = tmp_file.name

    upload_result = cloudinary.uploader.upload(
        tmp_file_path,
        resource_type="video",
        folder="voicebot",
        overwrite=True,
        format="mp3"
    )
    return upload_result["secure_url"]

@app.post("/upload_url")
async def upload_url(request: Request):
    form = await request.form()
    url = form.get("url")
    session_id = form.get("session_id")

    if not url:
        raise HTTPException(status_code=400, detail="Geen URL ontvangen")

    print("🌐 URL ontvangen:", url, "session_id:", session_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Kan URL niet downloaden.")
                content = await response.read()
    except Exception as e:
        print("❌ Fout bij downloaden:", str(e))
        raise HTTPException(status_code=500, detail=f"Downloadfout: {str(e)}")

    text_response = f"Ik heb de pagina {url} bekeken."
    audio_url = upload_to_cloudinary(convert_text_to_audio(text_response, voice="Ruth"))

    return {"text": text_response, "audio_url": audio_url}
