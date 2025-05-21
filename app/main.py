from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import traceback
import tempfile
import cloudinary
import cloudinary.uploader
from openai import OpenAI
from elevenlabs import ElevenLabsClient, VoiceSettings
from uuid import uuid4

# Configuratie
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
eleven_client = ElevenLabsClient(api_key=os.getenv("ELEVEN_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

def generate_bot_reply(user_input: str) -> str:
    messages = [
        {"role": "system", "content": "Je bent een behulpzame Nederlandse conciërge."},
        {"role": "user", "content": user_input}
    ]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content

def text_to_speech(text: str) -> str:
    try:
        voice_id = os.getenv("ELEVEN_VOICE_ID", "Rachel")

        audio = eleven_client.text_to_speech.generate(
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
            voice_settings=VoiceSettings(
                stability=0.4,
                similarity_boost=0.7,
                style=0.0,
                use_speaker_boost=True,
            )
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio)
            temp_file_path = f.name

        upload_result = cloudinary.uploader.upload(temp_file_path, resource_type="video")
        return upload_result['secure_url']

    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        raise

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("question")

        if not user_input or not isinstance(user_input, str):
            print("⚠️ Ongeldige of lege invoer ontvangen.")
            return JSONResponse(status_code=400, content={"error": "Ongeldige invoer"})

        print(f"📥 Ontvangen user_input: '{user_input}'")
        reply = generate_bot_reply(user_input)
        print(f"🧠 GPT antwoord: '{reply}'")

        print("🎙️ Start TTS generatie...")
        audio_url = text_to_speech(reply)

        return {"answer": reply, "audio_url": audio_url}

    except Exception as e:
        print(f"❌ Fout in POST /ask: {e}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
