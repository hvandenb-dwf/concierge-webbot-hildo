from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from elevenlabs import ElevenLabs
import cloudinary
import cloudinary.uploader
import os
import uuid
import tempfile

# === CONFIGURATIE ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Ruth
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100"

# === FASTAPI SETUP ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update eventueel voor striktere beveiliging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === HELPER FUNCTIES ===
def generate_response(prompt: str) -> str:
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Je bent een behulpzame Nederlandse conciërge."},
            {"role": "user", "content": prompt},
        ],
        model="gpt-4",
    )
    return chat_completion.choices[0].message.content.strip()

def synthesize_audio(text: str) -> str:
    audio = eleven_client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=text,
        model_id=MODEL_ID,
        output_format=OUTPUT_FORMAT
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        f.write(audio)
        temp_path = f.name

    result = cloudinary.uploader.upload(temp_path, resource_type="video")
    os.remove(temp_path)

    return result["secure_url"]

# === ROUTES ===
@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")

    if not prompt:
        return JSONResponse(status_code=400, content={"error": "Geen prompt ontvangen."})

    try:
        text_reply = generate_response(prompt)
        audio_url = synthesize_audio(text_reply)

        return {
            "text": text_reply,
            "audio_url": audio_url
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
def root():
    return {"message": "Voicebot backend is live."}
