def generate_audio(text: str, filename: str = "test_output.mp3") -> str:
    try:
        print("🎤 Start TTS generatie...")
        audio_stream = eleven_client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2",
            voice_settings=voice_settings
        )

        audio_bytes = audio_stream.read()
        print(f"🔊 Lengte audio-output: {len(audio_bytes)} bytes")

        if len(audio_bytes) < 100:
            raise ValueError("⚠️ Audio-output is te klein of leeg. TTS mogelijk mislukt.")

        with open(filename, "wb") as f:
            f.write(audio_bytes)

        print(f"✅ Audio opgeslagen als: {filename}")

        # Upload naar Cloudinary
        print("☁️ Upload naar Cloudinary gestart...")
        cloudinary_url = upload_audio_to_cloudinary(filename)
        print(f"✅ Upload succesvol: {cloudinary_url}")

        return cloudinary_url

    except Exception as e:
        print(f"❌ Fout in generate_audio: {e}")
        raise
