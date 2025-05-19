from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.bot_logic import generate_bot_reply
from app.tts import text_to_speech
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    user_input = data.get("message")

    try:
        reply = generate_bot_reply(user_input)
        audio_bytes = text_to_speech(reply)

        filename = "test_output.mp3"
        with open(filename, "wb") as f:
            f.write(audio_bytes)

        cloudinary_url = os.getenv("CLOUDINARY_AUDIO_URL")
        return JSONResponse(content={"reply": reply, "audio_url": cloudinary_url})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
