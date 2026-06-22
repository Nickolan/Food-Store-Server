import pytest
from decimal import Decimal
from fastapi import status
from app.core.security import create_access_token
from app.modules.usuario.models import Usuario
from app.modules.producto.models import Producto
from app.modules.ingrediente.models import Ingrediente, IngredienteProductoLink


def _token(user: Usuario) -> str:
    return create_access_token(data={
        "sub": user.email,
        "id": user.id,
        "roles": [r.codigo for r in user.roles],
    })


@pytest.fixture
def harina(session):
    ing = Ingrediente(nombre="Harina Test", precio=10.0, stock_cantidad=100, activo=True)
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing


@pytest.fixture
def queso(session):
    ing = Ingrediente(nombre="Queso Test", precio=25.0, stock_cantidad=50, activo=True)
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing


@pytest.fixture
def producto_sin_ingredientes(session):
    prod = Producto(
        nombre="Producto Base Test",
        precio_base=200.0,
        stock=10,
        stock_minimo=5,
        activo=True,
        disponible=True,
    )
    session.add(prod)
    session.commit()
    session.refresh(prod)
    return prod


@pytest.fixture
def producto_con_dos_ingredientes(session, producto_sin_ingredientes, harina, queso):
    session.add(IngredienteProductoLink(
        ingrediente_id=harina.id,
        producto_id=producto_sin_ingredientes.id,
        es_removible=False,
        cantidad=2,
    ))
    session.add(IngredienteProductoLink(
        ingrediente_id=queso.id,
        producto_id=producto_sin_ingredientes.id,
        es_removible=False,
        cantidad=1,
    ))
    session.commit()
    return producto_sin_ingredientes


@pytest.fixture
def producto_con_un_ingrediente(session):
    prod = Producto(
        nombre="Producto Simple",
        precio_base=100.0,
        stock=10,
        stock_minimo=5,
        activo=True,
        disponible=True,
    )
    session.add(prod)
    session.commit()
    session.refresh(prod)

    ing = Ingrediente(nombre="Ingrediente Simple", precio=30.0, stock_cantidad=50, activo=True)
    session.add(ing)
    session.commit()
    session.refresh(ing)

    session.add(IngredienteProductoLink(
        ingrediente_id=ing.id, producto_id=prod.id, es_removible=False, cantidad=3,
    ))
    session.commit()
    return prod


class TestCalcularMargenService:
    def test_calcular_costo_total_con_dos_ingredientes(self, session, producto_con_dos_ingredientes, harina, queso):
        from app.modules.producto.services import ProductoService
        from app.modules.producto.unit_of_work import ProductoUnitOfWork
        svc = ProductoService(session)
        with ProductoUnitOfWork(session) as uow:
            costo = svc._calcular_costo_ingredientes(uow, producto_con_dos_ingredientes.id)
        assert costo == 45.0  # (10 * 2) + (25 * 1)

    def test_calcular_costo_total_con_un_ingrediente(self, session, producto_con_un_ingrediente):
        from app.modules.producto.services import ProductoService
        from app.modules.producto.unit_of_work import ProductoUnitOfWork
        svc = ProductoService(session)
        with ProductoUnitOfWork(session) as uow:
            costo = svc._calcular_costo_ingredientes(uow, producto_con_un_ingrediente.id)
        assert costo == 90.0  # 30 * 3

    def test_calcular_costo_sin_ingredientes(self, session, producto_sin_ingredientes):
        from app.modules.producto.services import ProductoService
        from app.modules.producto.unit_of_work import ProductoUnitOfWork
        svc = ProductoService(session)
        with ProductoUnitOfWork(session) as uow:
            costo = svc._calcular_costo_ingredientes(uow, producto_sin_ingredientes.id)
        assert costo == 0.0

    def test_margen_return_type(self, session, producto_con_dos_ingredientes):
        from app.modules.producto.services import ProductoService
        from app.modules.producto.schemas import ProductoMargenResponse
        svc = ProductoService(session)
        margen = svc.calcular_margen(producto_con_dos_ingredientes.id)
        assert isinstance(margen, ProductoMargenResponse)

    def test_margen_con_dos_ingredientes(self, session, producto_con_dos_ingredientes):
        from app.modules.producto.services import ProductoService
        svc = ProductoService(session)
        margen = svc.calcular_margen(producto_con_dos_ingredientes.id)
        assert margen.precio_venta == 200.0
        assert margen.costo_total == 45.0
        assert margen.margen_absoluto == 155.0
        assert margen.margen_porcentual == 77.5

    def test_margen_con_un_ingrediente(self, session, producto_con_un_ingrediente):
        from app.modules.producto.services import ProductoService
        svc = ProductoService(session)
        margen = svc.calcular_margen(producto_con_un_ingrediente.id)
        assert margen.precio_venta == 100.0
        assert margen.costo_total == 90.0
        assert margen.margen_absoluto == 10.0
        assert margen.margen_porcentual == 10.0

    def test_margen_sin_ingredientes(self, session, producto_sin_ingredientes):
        from app.modules.producto.services import ProductoService
        svc = ProductoService(session)
        margen = svc.calcular_margen(producto_sin_ingredientes.id)
        assert margen.costo_total == 0.0
        assert margen.margen_absoluto == producto_sin_ingredientes.precio_base
        assert margen.margen_porcentual == 100.0

    def test_margen_con_precio_cero(self, session):
        prod = Producto(
            nombre="Gratis",
            precio_base=0,
            stock=10,
            stock_minimo=5,
            activo=True,
            disponible=True,
        )
        session.add(prod)
        session.commit()
        session.refresh(prod)
        from app.modules.producto.services import ProductoService
        svc = ProductoService(session)
        margen = svc.calcular_margen(prod.id)
        assert margen.precio_venta == 0
        assert margen.costo_total == 0
        assert margen.margen_absoluto == 0
        assert margen.margen_porcentual is None

    def test_margen_negativo(self, session):
        prod = Producto(
            nombre="Malo",
            precio_base=50.0,
            stock=10, stock_minimo=5,
            activo=True, disponible=True,
        )
        session.add(prod)
        session.commit()
        session.refresh(prod)
        ing = Ingrediente(nombre="Caro", precio=100.0, stock_cantidad=10, activo=True)
        session.add(ing)
        session.commit()
        session.refresh(ing)
        session.add(IngredienteProductoLink(
            ingrediente_id=ing.id, producto_id=prod.id, es_removible=False, cantidad=1,
        ))
        session.commit()
        from app.modules.producto.services import ProductoService
        svc = ProductoService(session)
        margen = svc.calcular_margen(prod.id)
        assert margen.margen_absoluto == -50.0
        assert margen.margen_porcentual == -100.0


class TestMargenEndpoint:
    def test_margen_endpoint_retorna_datos_correctos(self, client, admin_user, producto_con_dos_ingredientes):
        response = client.get(
            f"/api/v6/productos/{producto_con_dos_ingredientes.id}/margen",
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["producto_id"] == producto_con_dos_ingredientes.id
        assert data["precio_venta"] == 200.0
        assert data["costo_total"] == 45.0
        assert data["margen_absoluto"] == 155.0
        assert data["margen_porcentual"] == 77.5

    def test_margen_endpoint_sin_ingredientes(self, client, admin_user, producto_sin_ingredientes):
        response = client.get(
            f"/api/v6/productos/{producto_sin_ingredientes.id}/margen",
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["costo_total"] == 0.0
        assert data["margen_absoluto"] == 200.0
        assert data["margen_porcentual"] == 100.0

    def test_margen_endpoint_404(self, client, admin_user):
        response = client.get(
            "/api/v6/productos/99999/margen",
            cookies={"access_token": _token(admin_user)},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_margen_endpoint_401_sin_token(self, client, producto_con_dos_ingredientes):
        response = client.get(
            f"/api/v6/productos/{producto_con_dos_ingredientes.id}/margen",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_margen_endpoint_403_si_no_es_admin(self, client, client_user, producto_con_dos_ingredientes):
        response = client.get(
            f"/api/v6/productos/{producto_con_dos_ingredientes.id}/margen",
            cookies={"access_token": _token(client_user)},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN