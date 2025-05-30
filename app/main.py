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
import io
import cloudinary.uploader
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

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

        print("✅ Upload data ontvangen:", data)

        html = fetch_html(url)
        internal_links = extract_internal_links(url, html)
        pages = [html] + [fetch_html(link) for link in internal_links]
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Scrape fout: {str(e)}"}, status_code=500)

    combined = "\n\n".join(p[:5000] for p in pages[:5])
    prompt = f"Vat de kern samen van deze website en leg uit wat dit bedrijf doet en in welke markt het actief is:\n\n{combined}"

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent Eva, een vriendelijke Nederlandstalige assistent."},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content.strip()

        # Maak reply natuurlijker voor spraak
        reply = reply.replace('“', '"').replace('”', '"')
        reply = reply.replace('’', "'").replace('‘', "'")
        reply = reply.replace('...', '.').replace('..', '.')
        reply = reply.replace('\n', ' ')

        if not reply.lower().startswith(('ja', 'nee', 'natuurlijk', 'zeker', 'goed')):
            reply = "Natuurlijk. " + reply
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"GPT fout: {str(e)}"}, status_code=500)

    memory_store.setdefault(session_id, []).append(prompt)
    memory_store[session_id].append(reply)

    try:
        eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
        audio_stream = eleven_client.generate(
            text=reply,
            voice=Voice(voice_id="YUdpWWny7k5yb4QCeweX"),  # Eva
            model="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        audio_bytes = b"".join(audio_stream)

        upload = cloudinary.uploader.upload(
            io.BytesIO(audio_bytes),
            resource_type="video",
            format="mp3",
            folder="speech",
            use_filename=True,
            unique_filename=True,
            overwrite=True
        )
        audio_url = upload["secure_url"]
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Audio fout: {str(e)}"}, status_code=500)

    return {
        "audio_url": audio_url,
        "transcript": prompt,
        "reply": reply,
        "session_id": session_id
    }