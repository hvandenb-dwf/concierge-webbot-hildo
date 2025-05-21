import os
from elevenlabs import generate

def text_to_speech(text: str, filename: str = "output.mp3") -> bytes:
    print("🎙️ Start TTS generatie...")

    audio = generate(
        text=text,
        voice=os.getenv("ELEVEN_VOICE_ID"),
        model="eleven_multilingual_v2",
        stability=0.5,
        similarity_boost=0.7,
        style=0.0,
        use_speaker_boost=True
    )

    audio_bytes = bytes(audio)
    print(f"📏 Lengte audio-output: {len(audio_bytes)} bytes")

    with open(filename, "wb") as f:
        f.write(audio_bytes)

    print(f"✅ Audio opgeslagen als: {filename}")
    return audio_bytes
