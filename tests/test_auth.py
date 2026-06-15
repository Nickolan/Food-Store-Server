import pytest
from datetime import datetime
from fastapi import status
from app.core.security import create_access_token


class TestRegister:
    def test_register_exitoso(self, client, roles_base):
        payload = {
            "nombre": "Nuevo",
            "apellido": "User",
            "email": "nuevo@test.com",
            "password": "password123",
        }
        response = client.post("/api/v6/auth/", json=payload)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "nuevo@test.com"
        assert data["roles"][0]["codigo"] == "CLIENT"
        assert "access_token" in response.cookies

    def test_register_email_duplicado(self, client, client_user):
        payload = {
            "nombre": "Otro",
            "apellido": "User",
            "email": client_user.email,
            "password": "password123",
        }
        response = client.post("/api/v6/auth/", json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_corta(self, client, roles_base):
        payload = {
            "nombre": "Corto",
            "apellido": "Pass",
            "email": "corto@test.com",
            "password": "123",
        }
        response = client.post("/api/v6/auth/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestLogin:
    def test_login_exitoso(self, client, admin_user):
        payload = {"email": admin_user.email, "password": "adminpass123"}
        response = client.post("/api/v6/auth/token", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.cookies
        assert response.json()["mensaje"] == "Login exitoso. Sesión iniciada."

    def test_login_wrong_password(self, client, admin_user):
        payload = {"email": admin_user.email, "password": "wrongpass"}
        response = client.post("/api/v6/auth/token", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_usuario_inexistente(self, client, roles_base):
        payload = {"email": "noexiste@test.com", "password": "password123"}
        response = client.post("/api/v6/auth/token", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_usuario_desactivado(self, client, session, roles_base):
        from app.modules.usuario.models import Usuario
        from app.core.security import hash_password

        user = Usuario(
            nombre="Deleted",
            apellido="User",
            email="deleted@test.com",
            password_hash=hash_password("password123"),
            deleted_at=datetime(2025, 1, 1),
        )
        session.add(user)
        session.commit()

        payload = {"email": "deleted@test.com", "password": "password123"}
        response = client.post("/api/v6/auth/token", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLogout:
    def test_logout_exitoso(self, client, admin_user):
        token = create_access_token(data={
            "sub": admin_user.email,
            "id": admin_user.id,
            "roles": [r.codigo for r in admin_user.roles],
        })
        response = client.post("/api/v6/auth/logout", cookies={"access_token": token})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["mensaje"] == "Sesión cerrada exitosamente"


class TestMe:
    def test_me_con_token_valido(self, client, admin_user):
        token = create_access_token(data={
            "sub": admin_user.email,
            "id": admin_user.id,
            "roles": [r.codigo for r in admin_user.roles],
        })
        response = client.get("/api/v6/auth/me", cookies={"access_token": token})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == admin_user.email

    def test_me_sin_token(self, client):
        response = client.get("/api/v6/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRBAC:
    def test_roles_endpoint_admin(self, client, admin_user):
        token = create_access_token(data={
            "sub": admin_user.email,
            "id": admin_user.id,
            "roles": [r.codigo for r in admin_user.roles],
        })
        response = client.get("/api/v6/auth/roles", cookies={"access_token": token})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 4

    def test_roles_endpoint_client_rechazado(self, client, client_user):
        token = create_access_token(data={
            "sub": client_user.email,
            "id": client_user.id,
            "roles": [r.codigo for r in client_user.roles],
        })
        response = client.get("/api/v6/auth/roles", cookies={"access_token": token})
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRateLimit:
    def test_rate_limit_tras_5_intentos_fallidos(self, client, admin_user):
        payload = {"email": admin_user.email, "password": "wrongpass"}
        for _ in range(5):
            client.post("/api/v6/auth/token", json=payload)

        response = client.post("/api/v6/auth/token", json=payload)
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_rate_limit_permite_login_tras_4_fallos(self, client, admin_user):
        payload_fail = {"email": admin_user.email, "password": "wrongpass"}
        for _ in range(4):
            client.post("/api/v6/auth/token", json=payload_fail)

        payload_ok = {"email": admin_user.email, "password": "adminpass123"}
        response = client.post("/api/v6/auth/token", json=payload_ok)
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.cookies
