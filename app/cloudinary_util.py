import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_audio_to_cloudinary(audio_bytes: bytes, public_id: str = None) -> str:
    result = cloudinary.uploader.upload(
        file=audio_bytes,
        resource_type="video",  # nodig voor mp3
        public_id=public_id,
        overwrite=True,
        format="mp3"
    )
    return result["secure_url"]
