from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, TextToSpeech
import cloudinary
import cloudinary.uploader
import os
import tempfile

app = FastAPI()

# CORS zodat frontend toegang heeft
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pas eventueel aan naar specifieke domeinen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

eleven_client = ElevenLabs(
    api_key=os.getenv("ELEVEN_API_KEY")
)

voice = Voice(
    voice_id=os.getenv("VOICE_ID"),  # bv. "pNInz6obpgDQGcFmaJgB"
    stability=0.3,
    similarity_boost=0.8,
)

text_to_speech = TextToSpeech(client=eleven_client)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


@app.post("/upload_url")
async def upload_url(url: str = Form(...), session_id: str = Form(...)):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Je bent een behulpzame voice-assistent die mensen helpt informatie van websites samen te vatten."},
            {"role": "user", "content": f"Geef een korte en duidelijke uitleg over deze website: {url}"}
        ]
    )

    text = response.choices[0].message.content

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(text_to_speech.convert(
            voice=voice,
            model="eleven_multilingual_v2",
            text=text
        ))
        tmp_path = tmp.name

    upload_result = cloudinary.uploader.upload(tmp_path, resource_type="video")
    audio_url = upload_result["secure_url"]

    return JSONResponse(content={"audio_url": audio_url, "text": text})


@app.post("/ask")
async def ask(audio: UploadFile, session_id: str = Form(...)):
    # Opslaan van audio en Whisper-transcriptie
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=open(tmp_path, "rb")
    )

    user_input = transcript.text

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Je bent een vriendelijke Nederlandstalige voice-assistent."},
            {"role": "user", "content": user_input}
        ]
    )

    text = response.choices[0].message.content

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_out:
        tmp_out.write(text_to_speech.convert(
            voice=voice,
            model="eleven_multilingual_v2",
            text=text
        ))
        tmp_out_path = tmp_out.name

    upload_result = cloudinary.uploader.upload(tmp_out_path, resource_type="video")
    audio_url = upload_result["secure_url"]

    return JSONResponse(content={"audio_url": audio_url, "text": text})
