from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import chardet
import openai
import os
from uuid import uuid4
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from openai import OpenAI
from openai._types import FileUpload

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()

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
        url = data.get("url")
        session_id = data.get("session_id") or str(uuid4())

        html = fetch_html(url)
        internal_links = extract_internal_links(url, html)
        pages = [html] + [fetch_html(link) for link in internal_links]

        combined = "\n\n".join(p[:5000] for p in pages[:5])
        prompt = f"Vat de kern samen van deze website en leg uit wat dit bedrijf doet en in welke markt het actief is:\n\n{combined}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een zakelijke analist."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content.strip()

        memory_store.setdefault(session_id, []).append(summary)
        return {"status": "ok", "message": "Analyse toegevoegd.", "session_id": session_id}

    except Exception as e:
        return JSONResponse({"error": f"Scrape of GPT fout: {str(e)}"}, status_code=500)

@app.post("/ask")
async def ask(request: Request):
    form = await request.form()
    session_id = form.get("session_id") or str(uuid4())
    file: UploadFile = form["file"]
    audio_data = await file.read()

    try:
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1",
            file=FileUpload.from_bytes(audio_data, filename="input.webm", content_type="audio/webm"),
            language="nl",
            response_format="text"
        )
        transcript = transcript_response
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
        return JSONResponse({"error": f"Audio fout: {str(e)}"}, status_code=500)

    return {"audio_url": audio_url, "transcript": transcript, "reply": reply, "session_id": session_id}
