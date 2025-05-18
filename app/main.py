from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import os

from app.bot_logic import generate_bot_reply
from app.tts import text_to_speech

app = FastAPI()

# CORS-configuratie (optioneel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        prompt = data.get("text", "").strip()

        if not prompt:
            return Response(content="❌ Geen geldige invoer ontvangen", status_code=400)

        print("🤖 Start GPT-generatie...")
        reply = generate_bot_reply(prompt)
        print(f"🧠 Antwoord: {reply}")

        print("🎤 Start TTS generatie...")
        audio_bytes = text_to_speech(reply)

        return Response(content=audio_bytes, media_type="audio/mpeg")

    except Exception as e:
        print(f"❌ Fout in /ask endpoint: {e}")
        return Response(content=f"❌ Fout: {e}", status_code=500)
