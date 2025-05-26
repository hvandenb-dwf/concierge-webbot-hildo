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
from urllib.parse import urljoin, urlparse

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
app.mount("/static", StaticFiles(directory="/tmp"), name="static")

SESSION_MEMORY = {}

@app.post("/ask")
async def ask(file: UploadFile = File(...), session_id: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=open(tmp_path, "rb"),
            response_format="text",
            language="nl"
        )

        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = [
                {"role": "system", "content": "Je bent een behulpzame Nederlandse assistent."}
            ]

        SESSION_MEMORY[session_id].append({"role": "user", "content": transcript})

        gpt_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=SESSION_MEMORY[session_id]
        ).choices[0].message.content

        SESSION_MEMORY[session_id].append({"role": "assistant", "content": gpt_response})

        audio = tts.generate(
            text=gpt_response,
            voice=Voice(
                voice_id="YUdpWWny7k5yb4QCeweX",
                settings=VoiceSettings(stability=0.3, similarity_boost=0.8)
            ),
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        filename = f"{uuid.uuid4().hex}.mp3"
        output_path = f"/tmp/{filename}"
        with open(output_path, "wb") as f:
            f.write(b"".join(audio))

        audio_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/static/{filename}"
        return JSONResponse({"audio_url": audio_url})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/upload_url")
async def upload_url(request: Request):
    data = await request.json()
    url = data.get("url")
    session_id = data.get("session_id")

    if not url or not session_id:
        return JSONResponse(status_code=400, content={"error": "url and session_id required"})

    try:
        base = urlparse(url).netloc
        visited = set()
        pages = []

        def get_clean_text(u):
            try:
                html = requests.get(u, timeout=5).text
                soup = BeautifulSoup(html, "html.parser")
                return soup.get_text(separator=" ", strip=True)
            except:
                return ""

        # 📥 1. Voeg homepage toe
        pages.append(get_clean_text(url))
        visited.add(url)

        # 🔗 2. Zoek interne links op homepage
        soup = BeautifulSoup(requests.get(url, timeout=5).text, "html.parser")
        links = soup.find_all("a", href=True)
        count = 0

        for link in links:
            href = link['href']
            full_url = urljoin(url, href)
            if base in full_url and full_url not in visited:
                visited.add(full_url)
                text = get_clean_text(full_url)
                if text:
                    pages.append(text)
                    count += 1
                if count >= 5:
                    break

        combined = "\n\n".join(p[:3000] for p in pages if p)[:12000]

        prompt = (
            f"Hieronder vind je de inhoud van een bedrijfswebsite verdeeld over meerdere pagina's:\n\n{combined}\n\n"
            f"Vat deze informatie samen:\n"
            f"- Wat doet dit bedrijf precies?\n"
            f"- In welke markt of sector zijn ze actief?\n"
            f"- Wat zijn actuele trends in die sector?\n"
            f"- Noem enkele bekende concurrenten in Nederland of Europa.\n"
            f"Geef een duidelijke, zakelijke analyse."
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
            "content": f"Bedrijfsanalyse van {url}:\n{summary}"
        })

        print(f"✅ [{session_id}] Analyse toegevoegd.")
        return JSONResponse({"status": "ok"})

    except Exception as e:
        print(f"❌ [{session_id}] URL-fout:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})
