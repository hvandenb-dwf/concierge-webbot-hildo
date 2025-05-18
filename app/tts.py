import os
from elevenlabs import generate

def text_to_speech(text: str, filename: str = "test_output.mp3") -> bytes:
    print("🎤 Start TTS generatie...")

    audio_generator = generate(
        text=text,
        voice=os.getenv("ELEVEN_VOICE_ID"),
        model="eleven_multilingual_v2",
        api_key=os.getenv("ELEVEN_API_KEY"),
        stream=False,
        output_format="mp3"
    )

    audio_bytes = b"".join(audio_generator)
    print(f"🔊 Lengte audio-output: {len(audio_bytes)} bytes")

    with open(filename, "wb") as f:
        f.write(audio_bytes)

    print(f"✅ Audio opgeslagen als: {filename}")
    return audio_bytes
