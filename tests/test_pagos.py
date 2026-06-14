import pytest
import uuid
from decimal import Decimal
from unittest.mock import patch

from app.core.security import create_access_token
from app.modules.modulo3.Pago.model import Pago


def _token(user):
    return create_access_token(data={
        "sub": user.email,
        "id": user.id,
        "roles": [r.codigo for r in user.roles],
    })

@pytest.fixture(name="pago")
def pago_fixture(session, pedido_pendiente):
    pago = Pago(
        pedido_id=pedido_pendiente.id,
        mp_status="in_process",
        external_reference=str(uuid.uuid4()),
        idempotency_key=str(uuid.uuid4()),
        transaction_amount=Decimal("0"),
    )
    session.add(pago)
    session.commit()
    session.refresh(pago)
    return pago

# mock de MP
@pytest.fixture(autouse=True)
def mock_mp():
    with patch("mercadopago.SDK") as mock:
        sdk_instance = mock.return_value

        sdk_instance.preference.return_value.create.return_value = {
            "status": 201,
            "response": {
                "init_point": "https://mercadopago.com/checkout?preference_id=123"
            },
        }

        sdk_instance.payment.return_value.get.return_value = {
            "status": 200,
            "response": {
                "external_reference": "some-ref",
                "status": "approved",
                "status_detail": "accredited",
            },
        }

        yield mock

def test_crear_pago_exitoso(client, client_user, pedido_pendiente):
    cookies = {"access_token": _token(client_user)}
    response = client.post(
        "/api/v1/pagos/",
        json={"pedido_id": pedido_pendiente.id},
        cookies=cookies,
    )
    assert response.status_code == 200


def test_crear_pago_pedido_no_pendiente(client, client_user, pedido_confirmado):
    cookies = {"access_token": _token(client_user)}
    response = client.post(
        "/api/v1/pagos/",
        json={"pedido_id": pedido_confirmado.id},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_crear_pago_pedido_inexistente(client, client_user):
    cookies = {"access_token": _token(client_user)}
    response = client.post(
        "/api/v1/pagos/",
        json={"pedido_id": 99999},
        cookies=cookies,
    )
    assert response.status_code == 404


def test_crear_pago_sin_auth(client, pedido_pendiente):
    response = client.post(
        "/api/v1/pagos/",
        json={"pedido_id": pedido_pendiente.id},
    )
    assert response.status_code == 401


def test_listar_pagos_admin(client, admin_user, pago):
    cookies = {"access_token": _token(admin_user)}
    response = client.get("/api/v1/pagos/", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_listar_pagos_client(client, client_user, pago):
    cookies = {"access_token": _token(client_user)}
    response = client.get("/api/v1/pagos/", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    for item in data:
        assert item["pedido_id"] == pago.pedido_id


def test_obtener_pago_por_id(client, admin_user, pago):
    cookies = {"access_token": _token(admin_user)}
    response = client.get(f"/api/v1/pagos/{pago.id}", cookies=cookies)
    assert response.status_code == 200
    assert response.json()["id"] == pago.id


def test_obtener_pago_inexistente(client, admin_user):
    cookies = {"access_token": _token(admin_user)}
    response = client.get("/api/v1/pagos/99999", cookies=cookies)
    assert response.status_code == 404


def test_client_ve_pago_ajeno(client, session, roles_base, pago):
    from app.modules.usuario.models import Usuario, UsuarioRol
    from app.core.security import hash_password

    otro_client = Usuario(
        nombre="Otro",
        apellido="Cliente",
        email="otro_client@test.com",
        password_hash=hash_password("otrapass123"),
    )
    session.add(otro_client)
    session.flush()
    session.refresh(otro_client)
    session.add(UsuarioRol(usuario_id=otro_client.id, rol_codigo="CLIENT"))
    session.commit()
    session.refresh(otro_client)

    cookies = {"access_token": _token(otro_client)}
    response = client.get(f"/api/v1/pagos/{pago.id}", cookies=cookies)
    assert response.status_code == 403


def test_admin_actualiza_pago(client, admin_user, pago):
    cookies = {"access_token": _token(admin_user)}
    response = client.put(
        f"/api/v1/pagos/{pago.id}",
        json={"mp_status": "approved"},
        cookies=cookies,
    )
    assert response.status_code == 200


def test_pedidos_actualiza_pago(client, pedidos_user, pago):
    cookies = {"access_token": _token(pedidos_user)}
    response = client.put(
        f"/api/v1/pagos/{pago.id}",
        json={"mp_status": "approved"},
        cookies=cookies,
    )
    assert response.status_code == 200


def test_actualizar_pago_inexistente(client, admin_user):
    cookies = {"access_token": _token(admin_user)}
    response = client.put(
        "/api/v1/pagos/99999",
        json={"mp_status": "approved"},
        cookies=cookies,
    )
    assert response.status_code == 404


def test_webhook_con_data_id(client, admin_user):
    response = client.post("/api/v1/pagos/webhook?data.id=123")
    assert response.status_code == 200


def test_webhook_sin_data_id(client):
    response = client.post("/api/v1/pagos/webhook")
    assert response.status_code == 200