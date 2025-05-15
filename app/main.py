from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.bot_logic import get_bot_reply
from app.tts import text_to_speech
from app.cloudinary_util import upload_audio

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    user_input = data.get("text")
    bot_reply = get_bot_reply(user_input)
    audio_path = text_to_speech(bot_reply)
    audio_url = upload_audio(audio_path)
    return {"reply": bot_reply, "audio_url": audio_url}
