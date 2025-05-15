import cloudinary
import cloudinary.uploader
import os

# Cloudinary config uit environment
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def upload_to_cloudinary(file_path: str) -> str:
    try:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",  # nodig voor .mp3
            folder="voicebot"
        )
        return result["secure_url"]
    except Exception as e:
        return f"Fout bij upload: {e}"
