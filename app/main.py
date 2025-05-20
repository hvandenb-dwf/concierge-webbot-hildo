import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.bot_logic import generate_bot_reply
from app.tts import text_to_speech
from uuid import uuid4
import tempfile

app = FastAPI()

# Serveer statische frontend (bijv. index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("text")
        print(f"📥 Ontvangen user_input: {user_input!r}")

        if not user_input or not isinstance(user_input, str):
            print("⚠️ Ongeldige of lege invoer ontvangen.")
            return JSONResponse(content={"error": "Ongeldige invoer"}, status_code=400)

        reply = generate_bot_reply(user_input)
        print(f"🧠 GPT antwoord: {reply!r}")

        if not reply or not isinstance(reply, str):
            print("⚠️ Leeg GPT-antwoord ontvangen.")
            return JSONResponse(content={"error": "Geen antwoord gegenereerd"}, status_code=500)

        audio_bytes = text_to_speech(reply)
        print(f"🔊 Lengte gegenereerde audio: {len(audio_bytes)} bytes")

        # Sla audio tijdelijk op
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name

        return FileResponse(temp_path, media_type="audio/mpeg", filename="antwoord.mp3")

    except Exception as e:
        print(f"❌ Fout in POST /ask: {e}")
        return JSONResponse(content={"error": "Interne serverfout"}, status_code=500)
