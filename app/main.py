from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import os
import tempfile
import uuid

app = FastAPI()

# API clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Maak /tmp beschikbaar als /static
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

@app.post("/ask")
async def ask(file: UploadFile = File(...)):
    try:
        # 🔹 Bewaar de audio tijdelijk
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # 🧠 Whisper transcriptie
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp_path, "rb"),
            response_format="text",
            language="nl"
        )
        print("📝 Transcript:", transcript)

        # 💬 GPT antwoord
        gpt_reply = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."},
                {"role": "user", "content": transcript}
            ]
        ).choices[0].message.content
        print("🤖 GPT:", gpt_reply)

        # 🗣️ ElevenLabs TTS met Ruth
        audio = tts.generate(
            text=gpt_reply,
            voice=Voice(
                voice_id="YUdpWWny7k5yb4QCeweX",
                settings=VoiceSettings(stability=0.3, similarity_boost=0.8)
            ),
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        # 💾 Opslaan als MP3
        filename = f"{uuid.uuid4().hex}.mp3"
        output_path = f"/tmp/{filename}"
        with open(output_path, "wb") as f:
            f.write(b"".join(audio))  # ✅ Fix: combineer generator naar bytes

        # 🌐 Publiceer als URL
        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/static/{filename}"
        return JSONResponse({"audio_url": audio_url})

    except Exception as e:
        print("❌ Fout in /ask:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
