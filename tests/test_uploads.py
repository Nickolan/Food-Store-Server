import io
import pytest
from unittest.mock import patch

from app.core.security import create_access_token

UPLOAD_ENDPOINT = "/api/v6/uploads/imagen"


def _token(user):
    return create_access_token(data={
        "sub": user.email,
        "id": user.id,
        "roles": [r.codigo for r in user.roles],
    })


@pytest.fixture(autouse=True)
def mock_cloudinary():
    fake_result = {
        "secure_url": "https://res.cloudinary.com/fake",
        "public_id": "fake_id",
        "width": 100,
        "height": 100,
        "format": "jpg",
        "resource_type": "image",
    }
    with patch("cloudinary.uploader.upload", return_value=fake_result) as mock:
        yield mock


def test_subir_imagen_exitosamente(client, admin_user):
    cookies = {"access_token": _token(admin_user)}
    fake_file = io.BytesIO(b"fake image content")
    fake_file.name = "test.jpg"

    response = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("test.jpg", fake_file, "image/jpeg")},
        cookies=cookies,
    )
    
    assert response.status_code == 201
    assert response.json()["secure_url"] == "https://res.cloudinary.com/fake"


def test_subir_sin_archivo(client, admin_user):
    cookies = {"access_token": _token(admin_user)}
    response = client.post(UPLOAD_ENDPOINT, cookies=cookies)
    assert response.status_code == 422