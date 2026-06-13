from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.core.cloudinary import subir_imagen, eliminar_imagen
from app.core.deps import require_roles
from urllib.parse import unquote

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.post(
    "/imagen",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
async def upload_imagen(
    file: UploadFile = File(...),
    carpeta: str = "foodstore/productos"
):
    contenido = await file.read()
    result = subir_imagen(
        file_bytes=contenido,
        content_type=file.content_type,
        carpeta=carpeta
    )
    return result

@router.delete(
    "/imagen/{public_id:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(["ADMIN", "STOCK"]))],
)
async def delete_imagen(public_id: str):
    public_id_decoded = unquote(public_id)
    eliminar_imagen(public_id_decoded)