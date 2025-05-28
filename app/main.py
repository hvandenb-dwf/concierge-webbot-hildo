from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import chardet
import os
import io
from uuid import uuid4
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from openai import OpenAI
from openai.types import File as TypedFile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

memory_store = {}  # {session_id: [memory lines]}

def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=10)
    raw = response.content
    encoding = chardet.detect(raw)['encoding'] or 'utf-8'
    html = raw.decode(encoding, errors='replace')
    return html

def extract_internal_links(base_url: str, html: str, max_links: int = 5) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/') or base_url in href:
            full_url = urljoin(base_url, href)
            if full_url.startswith(base_url):
                links.add(full_url)
        if len(links) >= max_links:
            break
    return list(links)

@app.post("/upload_url")
async def upload_url(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        print("❌ JSON fout:", e)
        return JSONResponse({"error": "Ongeldige JSON in verzoek"}, status_code=400)

    url = data.get("url")
    session_id = data.get("session_id") or str(uuid4())

    try:
        html = fetch_html(url)
        internal_links = extract_internal_links(url, html)
        pages = [html] + [fetch_html(link) for link in internal_links]
    except Exception as e:
        print("❌ Scrape fout:", e)
        return JSONResponse({"error": f"Scrape fout: {str(e)}"}, status_code=500)

    combined = "\n\n".join(p[:5000] for p in pages[:5])
    prompt = f"Vat de kern samen van deze website en leg uit wat dit bedrijf doet en in welke markt het actief is:\n\n{combined}"

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een zakelijke analist."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT fout:", e)
        return JSONResponse({"error": f"GPT fout: {str(e)}"}, status_code=500)

    memory_store.setdefault(session_id, []).append(summary)
    return {"status": "ok", "message": "Analyse toegevoegd.", "session_id": session_id}

@app.post("/ask")
async def ask(request: Request):
    try:
        form = await request.form()
        print("✅ Formulier ontvangen")

        session_id = form.get("session_id") or str(uuid4())
        print("🔑 Sessie-ID:", session_id)

        file: UploadFile = form["file"]
        audio_data = await file.read()
        print("🎧 Audio ontvangen (bytes):", len(audio_data))

        typed_file = TypedFile.from_data(
            data=audio_data,
            filename="input.webm",
            content_type="audio/webm"
        )

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=typed_file,
            response_format="text",
            language="nl"
        )
        transcript = transcription.strip()
        print("✍️ Transcript:", transcript)
    except Exception as e:
        print("❌ Whisper fout:", e)
        return JSONResponse({"error": f"Whisper fout: {str(e)}"}, status_code=500)

    history = memory_store.get(session_id, [])
    messages = [
        {"role": "system", "content": "Je bent een vriendelijke Nederlandstalige assistent."}
    ] + [{"role": "user", "content": h} for h in history] + [{"role": "user", "content": transcript}]

    try:
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        reply = gpt_response.choices[0].message.content.strip()
        print("🤖 GPT antwoord:", reply)
    except Exception as e:
        print("❌ GPT fout:", e)
        return JSONResponse({"error": f"GPT fout: {str(e)}"}, status_code=500)

    memory_store.setdefault(session_id, []).append(transcript)
    memory_store[session_id].append(reply)

    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import Voice

        eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
        audio = eleven_client.generate(
            text=reply,
            voice=Voice(voice_id="YUdpWWny7k5yb4QCeweX"),
            model="eleven_monolingual_v1",
            output_format="mp3_44100_128"
        )
        print("🔊 Audio gegenereerd")

        import cloudinary.uploader
        upload = cloudinary.uploader.upload(
            audio,
            resource_type="video",
            format="mp3",
            folder="speech",
            use_filename=True,
            unique_filename=True,
            overwrite=True
        )
        audio_url = upload["secure_url"]
        print("☁️ Upload voltooid:", audio_url)
    except Exception as e:
        print("❌ Audio fout:", e)
        return JSONResponse({"error": f"Audio fout: {str(e)}"}, status_code=500)

    return {"audio_url": audio_url, "transcript": transcript, "reply": reply, "session_id": session_id}
