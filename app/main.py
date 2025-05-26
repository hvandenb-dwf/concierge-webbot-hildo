from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import os
import tempfile
import uuid

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Serve audio files
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

# 🧠 Simpele in-memory session store
SESSION_MEMORY = {}

@app.post("/ask")
async def ask(file: UploadFile = File(...), session_id: str = Form(...)):
    try:
        # 🔊 Bewaar audiobestand tijdelijk
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # 📝 Whisper transcriptie
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp_path, "rb"),
            response_format="text",
            language="nl"
        )

        print(f"🎙️ [{session_id}] Transcript: {transcript}")

        # 🧠 Haal sessiegeschiedenis op of start nieuw
        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = [
                {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."}
            ]

        SESSION_MEMORY[session_id].append({"role": "user", "content": transcript})

        # 💬 GPT (3.5 voor snelheid)
        gpt_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=SESSION_MEMORY[session_id]
        ).choices[0].message.content

        print(f"🤖 [{session_id}] GPT: {gpt_response}")

        SESSION_MEMORY[session_id].append({"role": "assistant", "content": gpt_response})

        # 🗣️ TTS met Ruth
        audio = tts.generate(
            text=gpt_response,
            voice=Voice(
                voice_id="YUdpWWny7k5yb4QCeweX",
                settings=VoiceSettings(stability=0.3, similarity_boost=0.8)
            ),
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        # 💾 Opslaan
        filename = f"{uuid.uuid4().hex}.mp3"
        path = f"/tmp/{filename}"
        with open(path, "wb") as f:
            f.write(b"".join(audio))

        # 🌐 Geef audio URL terug
        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/static/{filename}"
        return JSONResponse({"audio_url": audio_url})

    except Exception as e:
        print(f"❌ [{session_id}] Fout:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
