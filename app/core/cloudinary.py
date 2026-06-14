import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

ALLOWED_FORMATS = ["jpg", "jpeg", "png", "webp"]
MAX_SIZE_BYTES = 5 * 1024 * 1024  # esto es 5MB, como pide el doc pasado en whatsapp

def subir_imagen(file_bytes: bytes, content_type: str, carpeta: str = "foodstore") -> dict:
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen no puede superar los 5MB."
        )
    
    # Validar tipo MIME
    tipos_permitidos = ["image/jpeg", "image/png", "image/webp"]
    if content_type not in tipos_permitidos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Usar: jpg, png, webp."
        )

    result = cloudinary.uploader.upload(
        file_bytes,
        folder=carpeta,
        resource_type="image",
        overwrite=False,
        unique_filename=True,
        allowed_formats=ALLOWED_FORMATS,
    )
    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"],
        "width": result["width"],
        "height": result["height"],
        "format": result["format"],
        "resource_type": result["resource_type"],
    }

def eliminar_imagen(public_id: str) -> None:
    result = cloudinary.uploader.destroy(public_id)
    if result.get("result") not in ["ok", "not found"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo eliminar la imagen con public_id: {public_id}"
        )