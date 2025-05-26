from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import traceback

from app.bot_logic import generate_bot_reply
from app.tts import text_to_speech, speech_to_speech

app = FastAPI()

# Sta frontend requests toe vanuit de browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount de frontend map
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("question")

        if not user_input or not isinstance(user_input, str):
            print("⚠️ Ongeldige of lege invoer ontvangen.")
            return JSONResponse(status_code=400, content={"error": "Ongeldige invoer"})

        print(f"📥 Ontvangen user_input: '{user_input}'")
        reply = generate_bot_reply(user_input)
        print(f"🧠 GPT antwoord: '{reply}'")

        bot_mode = int(os.getenv("BOT_MODE", 2))

        if bot_mode == 3:
            print("🎙️ STS (speech_to_speech) actief")
            audio_url = speech_to_speech(reply)
        else:
            print("🗣️ TTS (text_to_speech) actief")
            audio_url = text_to_speech(reply)

        return {"answer": reply, "audio_url": audio_url}

    except Exception as e:
        print(f"❌ Fout in POST /ask: {e}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
