import cloudinary.uploader
import io

def upload_audio_to_cloudinary(audio_bytes: bytes) -> str:
    upload = cloudinary.uploader.upload(
        io.BytesIO(audio_bytes),
        resource_type="video",
        format="mp3",
        folder="speech",
        use_filename=True,
        unique_filename=True,
        overwrite=True
    )
    return upload["secure_url"]