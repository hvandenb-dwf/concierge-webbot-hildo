from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.bot_logic import generate_bot_reply
from app.tts import text_to_speech

app = FastAPI()

# CORS-configuratie voor lokaal testen of gebruik in browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Voicebot is live."}

@app.post("/ask")
async def ask(request: Request):
    try:
        data = await request.json()
        user_input = data.get("message", "")

        print("🤖 Start GPT-generatie...")
        reply = generate_bot_reply(user_input)

        print("🎤 Start TTS-generatie...")
        audio_bytes = text_to_speech(reply)

        return JSONResponse(content={
            "reply": reply,
            "audio_length_bytes": len(audio_bytes)
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
