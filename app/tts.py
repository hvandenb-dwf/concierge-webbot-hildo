import os
from elevenlabs.client import ElevenLabs, VoiceSettings

# Initialiseer ElevenLabs client
client = ElevenLabs(
    api_key=os.getenv("ELEVEN_API_KEY")
)

voice_id = os.getenv("ELEVEN_VOICE_ID")
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True,
)

def text_to_speech(text: str, filename: str = "output.mp3") -> bytes:
    print("🗣️ Start TTS generatie...")

    try:
        audio = client.generate(
            text=text,
            voice_id=voice_id,
            model="eleven_multilingual_v2",
            voice_settings=voice_settings,
        )
        audio_bytes = bytes(audio)

        print(f"🔊 Lengte audio-output: {len(audio_bytes)} bytes")

        with open(filename, "wb") as f:
            f.write(audio_bytes)

        print(f"✅ Audio opgeslagen als: {filename}")
        return audio_bytes

    except Exception as e:
        print(f"❌ Fout bij text_to_speech: {e}")
        return b""
