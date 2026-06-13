import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET)

def subir_imagen(file_bytes: bytes, carpeta: str = "food-store-cloudinary") -> str:
    """
    Sube una imagen a Cloudinary y devuelve la URL de la imagen subida.
    """
    result = cloudinary.uploader.upload(file_bytes, folder=carpeta)
    return result['secure_url']