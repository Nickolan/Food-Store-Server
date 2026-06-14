import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import WebSocket

from app.core.websocket import ConnectionManager  


@pytest.fixture
def manager():
    """Instancia limpia de ConnectionManager para cada test."""
    return ConnectionManager()


@pytest.fixture
def ws():
    """WebSocket simulado."""
    return AsyncMock(spec=WebSocket)


@pytest.fixture
def ws2():
    """Segundo WebSocket simulado (para tests multi-socket)."""
    return AsyncMock(spec=WebSocket)


@pytest.mark.asyncio
async def test_connect_acepta_y_asigna_room(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    ws.accept.assert_called_once()
    assert ws in manager.rooms.get("role:admin", set())


@pytest.mark.asyncio
async def test_connect_multiples_roles(manager, ws):
    await manager.connect(ws, "pedidos", user_id=2)
    ws.accept.assert_called_once()
    assert ws in manager.rooms.get("role:pedidos", set())


@pytest.mark.asyncio
async def test_disconnect_limpia_todo(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    manager.disconnect(ws)
    for sockets in manager.rooms.values():
        assert ws not in sockets


@pytest.mark.asyncio
async def test_disconnect_room_huerfana(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    manager.disconnect(ws)
    assert "role:admin" not in manager.rooms


@pytest.mark.asyncio
async def test_join_order_room(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    manager.join_order_room(ws, order_id=42)
    assert ws in manager.rooms.get("order:42", set())


@pytest.mark.asyncio
async def test_leave_order_room(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    manager.join_order_room(ws, order_id=42)
    manager.leave_order_room(ws, order_id=42)
    assert ws not in manager.rooms.get("order:42", set())


@pytest.mark.asyncio
async def test_broadcast_to_role(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    await manager.broadcast_to_role("admin", "ev", {})
    ws.send_json.assert_called_once_with({"event": "ev", "data": {}})


@pytest.mark.asyncio
async def test_broadcast_to_order(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    manager.join_order_room(ws, order_id=42)
    await manager.broadcast_to_order(42, "ev", {})
    ws.send_json.assert_called_with({"event": "ev", "data": {}})


@pytest.mark.asyncio
async def test_broadcast_to_roles_no_duplica(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    manager.rooms.setdefault("role:pedidos", set()).add(ws)

    await manager.broadcast_to_roles(["admin", "pedidos"], "ev", {})
    assert ws.send_json.call_count == 1


@pytest.mark.asyncio
async def test_broadcast_a_todos(manager, ws, ws2):
    await manager.connect(ws, "admin", user_id=1)
    await manager.connect(ws2, "pedidos", user_id=2)
    await manager.broadcast("ev", {})
    ws.send_json.assert_called_once_with({"event": "ev", "data": {}})
    ws2.send_json.assert_called_once_with({"event": "ev", "data": {}})


@pytest.mark.asyncio
async def test_room_vacia_no_crash(manager):
    await manager._emit_to_room("role:vacia", "ev", {})


@pytest.mark.asyncio
async def test_socket_caido_durante_broadcast(manager, ws, ws2):
    await manager.connect(ws, "admin", user_id=1)
    await manager.connect(ws2, "admin", user_id=2)
    ws.send_json.side_effect = Exception("connection closed")

    await manager.broadcast_to_role("admin", "ev", {})
    ws2.send_json.assert_called_once_with({"event": "ev", "data": {}})

    for sockets in manager.rooms.values():
        assert ws not in sockets


@pytest.mark.asyncio
async def test_get_active_connections_count(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    count = manager.get_active_connections_count()
    assert isinstance(count, int)
    assert count >= 1


@pytest.mark.asyncio
async def test_get_rooms_info(manager, ws):
    await manager.connect(ws, "admin", user_id=1)
    info = manager.get_rooms_info()
    assert isinstance(info, dict)
    assert "role:admin" in info
    assert isinstance(info["role:admin"], int)
    assert info["role:admin"] >= 1