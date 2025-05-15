import os
from elevenlabs import ElevenLabs
from elevenlabs.client import VoiceSettings

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

VOICE_ID = os.getenv("ELEVEN_VOICE_ID") or "Rachel"  # Of gebruik je eigen voice ID

def text_to_speech(text: str) -> bytes:
    try:
        audio_stream = client.text_to_speech.convert_as_stream(
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=text,
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75)
        )
        return b"".join(audio_stream)
    except Exception as e:
        return f"Fout bij text-to-speech: {e}".encode()
