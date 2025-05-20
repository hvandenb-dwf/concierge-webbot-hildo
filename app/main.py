import os
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from openai import OpenAI
from elevenlabs import generate, VoiceSettings
import cloudinary
import cloudinary.uploader

# === API Keys en configuratie ===

# OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ElevenLabs settings
voice_id = os.getenv("ELEVEN_VOICE_ID")
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True
)

# Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# === FastAPI setup ===

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("text")
        print(f"📥 Ontvangen user_input: {user_input!r}")

        if not user_input or not isinstance(user_input, str):
            print("⚠️ Ongeldige of lege invoer ontvangen.")
            return JSONResponse(content={"error": "Ongeldige invoer"}, status_code=400)

        reply = generate_bot_reply(user_input)
        print(f"🧠 GPT antwoord: {reply!r}")

        if not reply or not isinstance(reply, str):
            return JSONResponse(content={"error": "Geen geldig antwoord gegenereerd."}, status_code=500)

        audio_bytes = text_to_speech(reply)
        audio_url = upload_audio_to_cloudinary(audio_bytes, public_id=f"reply_{uuid4()}")

        return JSONResponse(content={
            "reply": reply,
            "audio_url": audio_url
        })

    except Exception as e:
        print(f"❌ Fout in POST /ask: {e}")
        return JSONResponse(content={"error": "Serverfout"}, status_code=500)

# === Functies ===

def generate_bot_reply(user_input: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame conciërge."},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ Fout bij generate_bot_reply: {e}")
        return "Er ging iets mis bij het genereren van een antwoord."


def text_to_speech(text: str) -> bytes:
    try:
        print("🎙️ Start TTS generatie...")
        audio = generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            voice_settings=voice_settings
        )
        return audio
    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        raise


def upload_audio_to_cloudinary(audio_bytes: bytes, public_id: str = None) -> str:
    try:
        print("☁️ Upload naar Cloudinary...")
        result = cloudinary.uploader.upload(
            file=audio_bytes,
            resource_type="video",  # mp3 vereist dit
            public_id=public_id,
            overwrite=True,
            format="mp3"
        )
        return result["secure_url"]
    except Exception as e:
        print(f"❌ Fout bij Cloudinary upload: {e}")
        raise
