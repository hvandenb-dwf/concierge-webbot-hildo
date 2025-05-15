from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import os

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

def test_voice():
    audio_stream = client.generate(
        text="Hallo, dit is een test van de webbot met ElevenLabs.",
        voice="Rachel",
        model="eleven_multilingual_v2",
        voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.8),
        stream=True  # Dit is belangrijk!
    )

    with open("test_output.mp3", "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)

    print("✅ Audio opgeslagen als test_output.mp3")

if __name__ == "__main__":
    test_voice()
