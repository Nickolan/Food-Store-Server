"""
TDD — Módulo de Estadísticas
Ciclo: RED → escribir tests → GREEN → implementar → REFACTOR

Cobertura:
  - RBAC: todos los endpoints rechazan CLIENT (403) y no autenticados (401)
  - Endpoint GET /estadisticas/pedidos-por-estado con datos reales (SQLite-compatible)
  - Servicio: unit tests con repositorio mockeado
  - Repositorio: get_pedidos_por_estado (GROUP BY simple, SQLite-compatible)
"""

import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock
from fastapi import status

from app.core.security import create_access_token
from app.modules.usuario.models import Usuario
from app.modules.modulo3.Pedido.model import Pedido


def _token(user: Usuario) -> str:
    return create_access_token(data={
        "sub": user.email,
        "id": user.id,
        "roles": [r.codigo for r in user.roles],
    })


# ─── RBAC ────────────────────────────────────────────────────────────────────

class TestEstadisticasRBAC:
    """
    Verifica que todos los endpoints rechazan usuarios sin rol ADMIN.
    No se ejecutan queries — FastAPI intercepta antes de llegar al servicio.
    """

    def test_resumen_rechaza_no_autenticado(self, client):
        r = client.get("/api/v6/estadisticas/resumen")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_resumen_rechaza_client(self, client, client_user):
        r = client.get("/api/v6/estadisticas/resumen",
                       cookies={"access_token": _token(client_user)})
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_ventas_rechaza_client(self, client, client_user):
        r = client.get(
            "/api/v6/estadisticas/ventas?desde=2025-01-01&hasta=2025-12-31",
            cookies={"access_token": _token(client_user)},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_productos_top_rechaza_client(self, client, client_user):
        r = client.get("/api/v6/estadisticas/productos-top",
                       cookies={"access_token": _token(client_user)})
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_pedidos_estado_rechaza_client(self, client, client_user):
        r = client.get("/api/v6/estadisticas/pedidos-por-estado",
                       cookies={"access_token": _token(client_user)})
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_ingresos_rechaza_client(self, client, client_user):
        r = client.get(
            "/api/v6/estadisticas/ingresos?desde=2025-01-01&hasta=2025-12-31",
            cookies={"access_token": _token(client_user)},
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    # Triangulación: pedidos_user tampoco tiene acceso
    def test_resumen_rechaza_pedidos_user(self, client, pedidos_user):
        r = client.get("/api/v6/estadisticas/resumen",
                       cookies={"access_token": _token(pedidos_user)})
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ─── Endpoint con datos (SQLite-compatible) ───────────────────────────────────

class TestPedidosPorEstadoEndpoint:
    """
    GET /api/v6/estadisticas/pedidos-por-estado es SQLite-compatible (GROUP BY sin
    funciones de fecha). Verifica estructura de respuesta con datos reales.
    """

    def test_retorna_lista_vacia_sin_pedidos(self, client, admin_user, roles_base):
        r = client.get("/api/v6/estadisticas/pedidos-por-estado",
                       cookies={"access_token": _token(admin_user)})
        assert r.status_code == status.HTTP_200_OK
        assert r.json() == []

    def test_retorna_conteo_correcto_por_estado(
        self, client, session, admin_user, formas_pago, estados_pedido, client_user
    ):
        session.add(Pedido(
            usuario_id=client_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        ))
        session.add(Pedido(
            usuario_id=client_user.id, estado_codigo="PENDIENTE",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        ))
        session.add(Pedido(
            usuario_id=client_user.id, estado_codigo="CANCELADO",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        ))
        session.commit()

        r = client.get("/api/v6/estadisticas/pedidos-por-estado",
                       cookies={"access_token": _token(admin_user)})
        assert r.status_code == status.HTTP_200_OK

        data = {item["estado_codigo"]: item["cantidad"] for item in r.json()}
        assert data["PENDIENTE"] == 2
        assert data["CANCELADO"] == 1

    def test_cada_item_tiene_campos_requeridos(
        self, client, session, admin_user, formas_pago, estados_pedido, client_user
    ):
        session.add(Pedido(
            usuario_id=client_user.id, estado_codigo="CONFIRMADO",
            forma_pago_codigo="MERCADOPAGO", subtotal=100, total=150, costo_envio=50,
        ))
        session.commit()

        r = client.get("/api/v6/estadisticas/pedidos-por-estado",
                       cookies={"access_token": _token(admin_user)})
        assert r.status_code == status.HTTP_200_OK
        for item in r.json():
            assert "estado_codigo" in item
            assert "cantidad" in item
            assert isinstance(item["cantidad"], int)


# ─── Servicio — unit tests con repositorio mockeado ──────────────────────────

class TestEstadisticasService:
    """
    Tests unitarios del servicio. El repositorio está mockeado, por lo que
    no se ejecutan queries y los tests son completamente independientes de la BD.
    """

    def _make_service(self):
        from app.modules.estadisticas.service import EstadisticasService
        repo = MagicMock()
        return EstadisticasService(repo=repo), repo

    # ── get_resumen ──────────────────────────────────────────────────────────

    def test_get_resumen_delega_al_repo(self):
        from app.modules.estadisticas.schemas import ResumenResponse
        service, repo = self._make_service()
        expected = ResumenResponse(
            ventas_hoy=Decimal("100.00"),
            ticket_promedio=Decimal("50.00"),
            pedidos_activos=3,
            ingresos_mes=Decimal("500.00"),
        )
        repo.get_resumen_kpis.return_value = expected

        result = service.get_resumen()

        repo.get_resumen_kpis.assert_called_once()
        assert result.ventas_hoy == Decimal("100.00")
        assert result.pedidos_activos == 3

    def test_get_resumen_montos_son_decimal(self):
        from app.modules.estadisticas.schemas import ResumenResponse
        service, repo = self._make_service()
        repo.get_resumen_kpis.return_value = ResumenResponse(
            ventas_hoy=Decimal("0.00"),
            ticket_promedio=Decimal("0.00"),
            pedidos_activos=0,
            ingresos_mes=Decimal("0.00"),
        )
        result = service.get_resumen()
        assert isinstance(result.ventas_hoy, Decimal)
        assert isinstance(result.ingresos_mes, Decimal)

    # ── get_ventas ───────────────────────────────────────────────────────────

    def test_get_ventas_agrupacion_invalida_lanza_value_error(self):
        service, _ = self._make_service()
        with pytest.raises(ValueError, match="agrupacion"):
            service.get_ventas(date(2025, 1, 1), date(2025, 12, 31), "hour")

    def test_get_ventas_agrupacion_valida_delega_al_repo(self):
        from app.modules.estadisticas.schemas import VentasPeriodoItem
        service, repo = self._make_service()
        repo.get_ventas_periodo.return_value = [
            VentasPeriodoItem(
                periodo="2025-01",
                total_ventas=Decimal("200.00"),
                cantidad_pedidos=4,
            )
        ]
        result = service.get_ventas(date(2025, 1, 1), date(2025, 12, 31), "month")
        repo.get_ventas_periodo.assert_called_once_with(
            date(2025, 1, 1), date(2025, 12, 31), "month"
        )
        assert len(result) == 1
        assert result[0].total_ventas == Decimal("200.00")

    # Triangulación: las 3 agrupaciones válidas no lanzan error
    @pytest.mark.parametrize("agrupacion", ["day", "week", "month"])
    def test_get_ventas_agrupaciones_permitidas(self, agrupacion):
        service, repo = self._make_service()
        repo.get_ventas_periodo.return_value = []
        result = service.get_ventas(date(2025, 1, 1), date(2025, 12, 31), agrupacion)
        assert result == []

    # ── get_productos_top ────────────────────────────────────────────────────

    def test_get_productos_top_delega_con_limit(self):
        service, repo = self._make_service()
        repo.get_productos_top.return_value = []
        service.get_productos_top(limit=5)
        repo.get_productos_top.assert_called_once_with(5)

    def test_get_productos_top_limit_default_es_10(self):
        service, repo = self._make_service()
        repo.get_productos_top.return_value = []
        service.get_productos_top()
        repo.get_productos_top.assert_called_once_with(10)

    # ── get_pedidos_por_estado ───────────────────────────────────────────────

    def test_get_pedidos_por_estado_delega_al_repo(self):
        from app.modules.estadisticas.schemas import PedidosEstadoItem
        service, repo = self._make_service()
        repo.get_pedidos_por_estado.return_value = [
            PedidosEstadoItem(estado_codigo="PENDIENTE", cantidad=5),
            PedidosEstadoItem(estado_codigo="CANCELADO", cantidad=2),
        ]
        result = service.get_pedidos_por_estado()
        assert len(result) == 2
        assert result[0].estado_codigo == "PENDIENTE"

    # ── get_ingresos ─────────────────────────────────────────────────────────

    def test_get_ingresos_delega_al_repo(self):
        service, repo = self._make_service()
        repo.get_ingresos_por_forma_pago.return_value = []
        service.get_ingresos(date(2025, 1, 1), date(2025, 12, 31))
        repo.get_ingresos_por_forma_pago.assert_called_once_with(
            date(2025, 1, 1), date(2025, 12, 31)
        )


# ─── Repositorio — get_pedidos_por_estado (SQLite-compatible) ────────────────

class TestEstadisticasRepository:
    """
    Tests directos del repositorio. Solo cubre get_pedidos_por_estado porque
    las otras queries usan DATE_TRUNC/EXTRACT que requieren PostgreSQL.
    """

    def _make_repo(self, session):
        from app.modules.estadisticas.repository import EstadisticasRepository
        return EstadisticasRepository(session)

    def test_sin_pedidos_retorna_lista_vacia(self, session, roles_base, formas_pago, estados_pedido):
        repo = self._make_repo(session)
        result = repo.get_pedidos_por_estado()
        assert result == []

    def test_agrupa_correctamente_por_estado(
        self, session, client_user, formas_pago, estados_pedido
    ):
        repo = self._make_repo(session)
        for estado in ("PENDIENTE", "PENDIENTE", "CONFIRMADO", "CANCELADO"):
            session.add(Pedido(
                usuario_id=client_user.id,
                estado_codigo=estado,
                forma_pago_codigo="MERCADOPAGO",
                subtotal=0, total=0, costo_envio=50,
            ))
        session.commit()

        result = repo.get_pedidos_por_estado()
        counts = {item.estado_codigo: item.cantidad for item in result}

        assert counts["PENDIENTE"] == 2
        assert counts["CONFIRMADO"] == 1
        assert counts["CANCELADO"] == 1

    def test_retorna_objetos_pedidos_estado_item(
        self, session, client_user, formas_pago, estados_pedido
    ):
        from app.modules.estadisticas.schemas import PedidosEstadoItem
        repo = self._make_repo(session)
        session.add(Pedido(
            usuario_id=client_user.id, estado_codigo="ENTREGADO",
            forma_pago_codigo="MERCADOPAGO", subtotal=0, total=0, costo_envio=50,
        ))
        session.commit()

        result = repo.get_pedidos_por_estado()
        assert all(isinstance(item, PedidosEstadoItem) for item in result)
        assert result[0].cantidad >= 1
