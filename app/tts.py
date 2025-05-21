import os
from elevenlabs import ElevenLabsClient, VoiceSettings

client = ElevenLabsClient(api_key=os.getenv("ELEVEN_API_KEY"))

voice_settings = VoiceSettings(
    stability=0.3,
    similarity_boost=0.7,
    style=0.0,
    use_speaker_boost=True
)

def text_to_speech(text, voice="Rachel"):
    try:
        audio = client.tts.generate(
            text=text,
            voice=voice,
            model="eleven_multilingual_v2",
            voice_settings=voice_settings
        )
        return audio
    except Exception as e:
        print(f"❌ Fout in text_to_speech: {e}")
        return None
