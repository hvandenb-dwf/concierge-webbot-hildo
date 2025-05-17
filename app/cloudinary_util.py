import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_audio_to_cloudinary(filepath: str) -> str:
    response = cloudinary.uploader.upload(
        filepath,
        resource_type="video",  # mp3 valt onder 'video'
        folder="voicebot-audio",
        use_filename=True,
        unique_filename=True,
        overwrite=False,
        upload_preset="concierge_voicebot"  # essentieel bij signed preset
    )
    return response["secure_url"]
