import os
from elevenlabs import ElevenLabs
from elevenlabs.client import VoiceSettings

# Initialiseer ElevenLabs client
client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

# Steminstellingen
voice_id = os.getenv("ELEVEN_VOICE_ID")
voice_settings = VoiceSettings(
    stability=0.5,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True,
)

def text_to_speech(text: str, filename: str = "test_output.mp3") -> bytes:
    print("🎤 Start TTS generatie...")

    # Genereer audio met stream=False → dit is een generator
    audio_generator = client.generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2",
        stream=False,
        voice_settings=voice_settings
    )

    # Combineer alle chunks uit de generator tot één bytes-object
    audio_bytes = b"".join(chunk for chunk in audio_generator)

    # Debug output
    print(f"🔊 Lengte audio-output: {len(audio_bytes)} bytes")

    # Sla bestand op
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    print(f"✅ Audio opgeslagen als: {filename}")

    return audio_bytes
