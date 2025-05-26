from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import os
import tempfile
import uuid
import requests
from bs4 import BeautifulSoup

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Host tijdelijke audio output
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

# Eenvoudige sessiegeheugenopslag
SESSION_MEMORY = {}

@app.post("/ask")
async def ask(file: UploadFile = File(...), session_id: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # Transcribeer audio
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp_path, "rb"),
            response_format="text",
            language="nl"
        )

        print(f"🎙️ [{session_id}] Transcript: {transcript}")

        # Bouw sessiegeschiedenis op
        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = [
                {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."}
            ]

        SESSION_MEMORY[session_id].append({"role": "user", "content": transcript})

        # Genereer GPT-reactie
        gpt_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=SESSION_MEMORY[session_id]
        ).choices[0].message.content

        print(f"🤖 [{session_id}] GPT: {gpt_response}")

        SESSION_MEMORY[session_id].append({"role": "assistant", "content": gpt_response})

        # Zet om naar spraak
        audio = tts.generate(
            text=gpt_response,
            voice=Voice(
                voice_id="YUdpWWny7k5yb4QCeweX",  # Ruth
                settings=VoiceSettings(stability=0.3, similarity_boost=0.8)
            ),
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        # Sla audio op
        filename = f"{uuid.uuid4().hex}.mp3"
        output_path = f"/tmp/{filename}"
        with open(output_path, "wb") as f:
            f.write(b"".join(audio))

        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/static/{filename}"
        return JSONResponse({"audio_url": audio_url})

    except Exception as e:
        print(f"❌ [{session_id}] Fout in /ask:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/upload_url")
async def upload_url(request: Request):
    data = await request.json()
    url = data.get("url")
    session_id = data.get("session_id")

    if not url or not session_id:
        return JSONResponse(status_code=400, content={"error": "url and session_id required"})

    try:
        print(f"🌐 [{session_id}] Ophalen van URL: {url}")
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        trimmed = text[:5000]

        prompt = (
            f"Hieronder vind je de tekstinhoud van een bedrijfswebsite:\n\n{trimmed}\n\n"
            f"Vat deze informatie samen en leg uit in welke markt dit bedrijf zich bevindt, wat hun diensten zijn, en noem relevante trends of concurrenten."
        )

        summary = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Je bent een bedrijfsanalist."},
                {"role": "user", "content": prompt}
            ]
        ).choices[0].message.content

        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = []

        SESSION_MEMORY[session_id].insert(0, {
            "role": "system",
            "content": f"Bedrijfsinformatie van {url}: {summary}"
        })

        print(f"📎 [{session_id}] Samenvatting toegevoegd aan sessiegeheugen.")
        return JSONResponse({"status": "ok"})

    except Exception as e:
        print(f"❌ [{session_id}] Fout bij URL-verwerking:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
