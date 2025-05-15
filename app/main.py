from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.bot_logic import generate_bot_reply
from app.tts import text_to_speech
from app.cloudinary_util import upload_to_cloudinary
import tempfile
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    user_input = data.get("prompt")

    if not user_input:
        return JSONResponse(content={"error": "No prompt provided"}, status_code=400)

    # Generate response with GPT
    reply = generate_bot_reply(user_input)

    # Convert to speech
    audio_bytes = text_to_speech(reply)

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    # Upload to Cloudinary
    audio_url = upload_to_cloudinary(tmp_path)

    # Clean up temp file
    os.remove(tmp_path)

    return {"text": reply, "audio_url": audio_url}
# temp update om commit te forceren

