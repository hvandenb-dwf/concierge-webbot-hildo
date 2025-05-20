import os
from elevenlabs import ElevenLabs, VoiceSettings

# Initialiseer ElevenLabs client
client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Haal voice ID en stel instellingen in
voice_id = os.getenv("ELEVEN_VOICE_ID")
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True
)

def text_to_speech(text: str, filename: str = "output.mp3") -> bytes:
    print("🎤 Start TTS generatie...")

    audio = client.generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2",
        voice_settings=voice_settings
    )

    audio_bytes = bytes(audio)
    print(f"🔊 Lengte audio-output: {len(audio_bytes)} bytes")

    with open(filename, "wb") as f:
        f.write(audio_bytes)

    print(f"✅ Audio opgeslagen als: {filename}")
    return audio_bytes
