import pytest
from datetime import datetime
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

from app.main import app
from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.modules.usuario.models import Rol, Usuario, UsuarioRol
from app.modules.modulo3.EstadoPedido.model import EstadoPedido
from app.modules.modulo3.Formapago.model import FormaPago
from app.modules.modulo3.Pedido.model import Pedido

SQLiteTypeCompiler.visit_ARRAY = (
    lambda self, element, **kw: self.visit_JSON(element, **kw)
)
SQLiteTypeCompiler.visit_BIGINT = (
    lambda self, element, **kw: self.visit_integer(element, **kw)
)


@pytest.fixture(name="sqlite_engine", scope="function")
def sqlite_engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session", scope="function")
def session_fixture(sqlite_engine):
    with Session(sqlite_engine) as session:
        yield session


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session, sqlite_engine):
    import app.core.database as db_module
    import app.main as main_module

    db_module.engine = sqlite_engine
    main_module.engine = sqlite_engine

    app.middleware_stack = None

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(name="roles_base", scope="function")
def roles_base_fixture(session: Session):
    roles_data = [
        {"codigo": "ADMIN",   "nombre": "Administrador",     "descripcion": "Acceso total"},
        {"codigo": "STOCK",   "nombre": "Gestión de Stock",  "descripcion": "Maneja stock"},
        {"codigo": "PEDIDOS", "nombre": "Gestión de Pedidos","descripcion": "Avanza estados"},
        {"codigo": "CLIENT",  "nombre": "Cliente",           "descripcion": "Sus propios datos"},
    ]
    roles = []
    for data in roles_data:
        rol = Rol(**data)
        session.add(rol)
        roles.append(rol)
    session.commit()
    for r in roles:
        session.refresh(r)
    return roles


@pytest.fixture(name="estados_pedido", scope="function")
def estados_pedido_fixture(session: Session):
    estados_data = [
        ("PENDIENTE",  "Pedido creado",        1, False),
        ("CONFIRMADO", "Pago confirmado",       2, False),
        ("EN_PREP",    "En preparación",        3, False),
        ("EN_CAMINO",  "Despachado",            4, False),
        ("ENTREGADO",  "Entrega confirmada",    5, True),
        ("CANCELADO",  "Pedido cancelado",      6, True),
    ]
    estados = []
    for codigo, desc, orden, terminal in estados_data:
        e = EstadoPedido(codigo=codigo, descripcion=desc, orden=orden, es_terminal=terminal)
        session.add(e)
        estados.append(e)
    session.commit()
    for e in estados:
        session.refresh(e)
    return estados


@pytest.fixture(name="formas_pago", scope="function")
def formas_pago_fixture(session: Session):
    formas_data = [
        ("MERCADOPAGO",   "Mercado Pago",           True),
        ("EFECTIVO",      "Efectivo",               True),
        ("TRANSFERENCIA", "Transferencia bancaria", True),
    ]
    formas = []
    for codigo, desc, habilitado in formas_data:
        f = FormaPago(codigo=codigo, descripcion=desc, habilitado=habilitado)
        session.add(f)
        formas.append(f)
    session.commit()
    for f in formas:
        session.refresh(f)
    return formas


@pytest.fixture(name="admin_user", scope="function")
def admin_user_fixture(session: Session, roles_base):
    user = Usuario(
        nombre="Admin",
        apellido="Test",
        email="admin_test@test.com",
        password_hash=hash_password("adminpass123"),
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    session.add(UsuarioRol(usuario_id=user.id, rol_codigo="ADMIN"))
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="pedidos_user", scope="function")
def pedidos_user_fixture(session: Session, roles_base):
    user = Usuario(
        nombre="Operador",
        apellido="Pedidos",
        email="pedidos_test@test.com",
        password_hash=hash_password("pedidospass123"),
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    session.add(UsuarioRol(usuario_id=user.id, rol_codigo="PEDIDOS"))
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="client_user", scope="function")
def client_user_fixture(session: Session, roles_base):
    user = Usuario(
        nombre="Cliente",
        apellido="Test",
        email="client_test@test.com",
        password_hash=hash_password("clientpass123"),
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    session.add(UsuarioRol(usuario_id=user.id, rol_codigo="CLIENT"))
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="pedido_pendiente", scope="function")
def pedido_pendiente_fixture(session: Session, client_user, formas_pago, estados_pedido):
    pedido = Pedido(
        usuario_id=client_user.id,
        estado_codigo="PENDIENTE",
        forma_pago_codigo="MERCADOPAGO",
        subtotal=0,
        total=0,
        costo_envio=50,
    )
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido


@pytest.fixture(name="pedido_confirmado", scope="function")
def pedido_confirmado_fixture(session: Session, client_user, formas_pago, estados_pedido):
    pedido = Pedido(
        usuario_id=client_user.id,
        estado_codigo="CONFIRMADO",
        forma_pago_codigo="MERCADOPAGO",
        subtotal=0,
        total=0,
        costo_envio=50,
    )
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido


def get_auth_headers(user: Usuario) -> dict:
    token = create_access_token(data={
        "sub": user.email,
        "id": user.id,
        "roles": [r.codigo for r in user.roles],
    })
    return {"access_token": token}