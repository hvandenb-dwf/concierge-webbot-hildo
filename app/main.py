from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.tts import text_to_speech

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    user_input = data.get("question")
    if not user_input:
        return JSONResponse(content={"error": "Lege input"}, status_code=400)

    # (simpele dummy reply)
    reply = f"Hallo! Je zei: {user_input}"

    audio = text_to_speech(reply)
    if not audio:
        return JSONResponse(content={"error": "TTS mislukt"}, status_code=500)

    # Return dummy mp3 link of binaire data
    return JSONResponse(content={"reply": reply})
