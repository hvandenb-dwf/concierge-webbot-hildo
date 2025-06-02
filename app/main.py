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
import traceback
import cloudinary.uploader
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")
eleven_client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

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

        # Tijdelijk testantwoord (bypass GPT)
        reply = "Welkom bij HandjeHelpen. Wij zetten vrijwilligers in om mensen te ondersteunen."

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

        print("✅ Audio URL:", audio_url)

        return {
            "audio_url": audio_url,
            "transcript": "Testvraag over website",
            "reply": reply,
            "session_id": session_id
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Fout tijdens upload_url: {str(e)}"}, status_code=500)

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("text")
        session_id = data.get("session_id") or str(uuid4())

        print(f"🧠 Vraag ontvangen: {user_input}")

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Je bent een vriendelijke en behulpzame assistent die spreekt in het Nederlands."},
                {"role": "user", "content": user_input},
            ]
        )

        reply = response["choices"][0]["message"]["content"]

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

        print(f"✅ GPT antwoord: {reply}")
        print(f"🎧 Audio URL: {audio_url}")

        return {
            "audio_url": audio_url,
            "reply": reply,
            "session_id": session_id
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": f"Fout tijdens /ask: {str(e)}"}, status_code=500)
