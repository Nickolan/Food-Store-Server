import pytest
from decimal import Decimal
from fastapi import status
from app.core.security import create_access_token
from app.modules.modulo3.Pedido.model import Pedido


def _token(user):
    return create_access_token(data={
        "sub": user.email,
        "id": user.id,
        "roles": [r.codigo for r in user.roles],
    })


class TestPedidoCRUD:
    def test_listar_pedidos_admin(self, client, admin_user, pedido_pendiente):
        response = client.get("/pedidos/", cookies={"access_token": _token(admin_user)})
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_listar_pedidos_client_ve_solo_propios(self, client, client_user, pedido_pendiente):
        pedido_pendiente.usuario_id = client_user.id
        response = client.get("/pedidos/", cookies={"access_token": _token(client_user)})
        assert response.status_code == status.HTTP_200_OK
        for p in response.json():
            assert p["usuario_id"] == client_user.id

    def test_obtener_pedido_por_id(self, client, admin_user, pedido_pendiente):
        response = client.get(
            f"/pedidos/{pedido_pendiente.id}",
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == pedido_pendiente.id

    def test_obtener_pedido_inexistente(self, client, admin_user):
        response = client.get("/pedidos/99999", cookies={"access_token": _token(admin_user)})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_crear_pedido_como_cliente(self, client, client_user, formas_pago):
        payload = {"forma_pago_codigo": "MERCADOPAGO", "items": []}
        response = client.post(
            "/pedidos/", json=payload,
            cookies={"access_token": _token(client_user)},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["estado_codigo"] == "PENDIENTE"
        assert data["usuario_id"] == client_user.id


class TestPedidoFSM:
    def test_pendiente_a_confirmado(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "CONFIRMADO"},
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado_codigo"] == "CONFIRMADO"

    def test_confirmado_a_en_prep(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="CONFIRMADO",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "EN_PREP"},
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado_codigo"] == "EN_PREP"

    def test_en_prep_a_en_camino(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="EN_PREP",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "EN_CAMINO"},
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado_codigo"] == "EN_CAMINO"

    def test_en_camino_a_entregado(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="EN_CAMINO",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "ENTREGADO"},
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado_codigo"] == "ENTREGADO"

    def test_transicion_invalida_retorna_400(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "ENTREGADO"},
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_estado_terminal_no_transiciona(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="ENTREGADO",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "CANCELADO"},
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPedidoRBAC:
    def test_client_no_puede_avanzar_estado(self, client, session, client_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=client_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "CONFIRMADO"},
            cookies={"access_token": _token(client_user)},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_pedidos_puede_avanzar_estado(self, client, session, pedidos_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=pedidos_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.put(
            f"/pedidos/{pedido.id}", json={"estado_codigo": "CONFIRMADO"},
            cookies={"access_token": _token(pedidos_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["estado_codigo"] == "CONFIRMADO"


class TestPedidoCancelacion:
    def test_cancelar_pedido_sin_motivo_retorna_422(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.delete(
            f"/pedidos/{pedido.id}",
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_cancelar_pedido_con_motivo(self, client, session, admin_user, formas_pago, estados_pedido):
        pedido = Pedido(
            usuario_id=admin_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        )
        session.add(pedido)
        session.commit()
        session.refresh(pedido)
        response = client.delete(
            f"/pedidos/{pedido.id}?motivo=Cliente+arrepentido",
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
