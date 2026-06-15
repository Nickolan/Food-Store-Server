"""
Script de inicialización (Seed) de la Base de Datos.
Cumple con el requisito del UML: "Seed obligatorio (app/db/seed.py)".

Carga los datos base del sistema: roles, estados de pedido, formas de pago
y el usuario administrador inicial.
Es idempotente (se puede ejecutar múltiples veces sin duplicar datos).
"""

import bcrypt
from sqlmodel import Session, SQLModel, select

from app.core.database import engine
from app.modules.direccionEntrega.models import DireccionEntrega
from app.modules.modulo3.EstadoPedido.model import EstadoPedido
from app.modules.modulo3.Formapago.model import FormaPago
from app.modules.usuario.models import Rol, Usuario, UsuarioRol
from app.modules.unidad_medida.models import UnidadMedida
from app.modules.producto.models import Producto
from app.modules.ingrediente.models import Ingrediente
from app.modules.categoria.models import Categoria


ROLES_BASE = [
    {
        "codigo": "ADMIN",
        "nombre": "Administrador",
        "descripcion": "Acceso total sin restricciones",
    },
    {
        "codigo": "STOCK",
        "nombre": "Gestión de Stock",
        "descripcion": "Actualiza stock y disponible",
    },
    {
        "codigo": "PEDIDOS",
        "nombre": "Gestión de Pedidos",
        "descripcion": "Avanza estados CONFIRMADO -> ENTREGADO",
    },
    {
        "codigo": "CLIENT",
        "nombre": "Cliente",
        "descripcion": "Opera solo sus propios datos",
    },
]

ESTADOS_PEDIDO = [
    ("PENDIENTE",    "Pedido creado, pago pendiente",  1, False),
    ("CONFIRMADO",   "Pago procesado y confirmado",    2, False),
    ("EN_PREP",      "En preparación en cocina",       3, False),
    ("EN_CAMINO",    "Despachado al cliente",           4, False),
    ("ENTREGADO",    "Entrega confirmada",              5, True),
    ("CANCELADO",    "Pedido cancelado",                6, True),
]

FORMAS_PAGO = [
    ("MERCADOPAGO",   "Mercado Pago",           True),
    ("EFECTIVO",      "Efectivo",               True),
    ("TRANSFERENCIA", "Transferencia bancaria", True),
]

UNIDADES_MEDIDA = [
    {"nombre": "kilogramo", "simbolo": "kg", "tipo": "masa"},
    {"nombre": "gramo", "simbolo": "g", "tipo": "masa"},
    {"nombre": "litro", "simbolo": "L", "tipo": "volumen"},
    {"nombre": "mililitro", "simbolo": "mL", "tipo": "volumen"},
    {"nombre": "pieza", "simbolo": "u", "tipo": "unidad"},
    {"nombre": "porciones", "simbolo": "porciones", "tipo": "contable"}
]



def _seed_roles(session: Session) -> None:
    for data in ROLES_BASE:
        existe = session.exec(select(Rol).where(Rol.codigo == data["codigo"])).first()
        if not existe:
            session.add(Rol(**data))
            print(f" [+] Rol creado: {data['codigo']}")
        else:
            print(f" [✓] Rol ya existe: {data['codigo']}")
    session.commit()


def _seed_estados_pedido(session: Session) -> None:
    for codigo, descripcion, orden, es_terminal in ESTADOS_PEDIDO:
        existe = session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == codigo)
        ).first()
        if not existe:
            session.add(
                EstadoPedido(
                    codigo=codigo,
                    descripcion=descripcion,
                    orden=orden,
                    es_terminal=es_terminal,
                )
            )
            print(f" [+] EstadoPedido creado: {codigo}")
        else:
            print(f" [✓] EstadoPedido ya existe: {codigo}")
    session.commit()


def _seed_formas_pago(session: Session) -> None:
    for codigo, descripcion, habilitado in FORMAS_PAGO:
        existe = session.exec(
            select(FormaPago).where(FormaPago.codigo == codigo)
        ).first()
        if not existe:
            session.add(
                FormaPago(
                    codigo=codigo,
                    descripcion=descripcion,
                    habilitado=habilitado,
                )
            )
            print(f" [+] FormaPago creada: {codigo}")
        else:
            print(f" [✓] FormaPago ya existe: {codigo}")
    session.commit()


def _seed_unidades_medida(session: Session) -> None:
    for data in UNIDADES_MEDIDA:
        existe = session.exec(select(UnidadMedida).where(UnidadMedida.simbolo == data["simbolo"])).first()
        if not existe:
            session.add(UnidadMedida(**data))
            print(f" [+] UnidadMedida creada: {data['simbolo']}")
        else:
            print(f" [✓] UnidadMedida ya existe: {data['simbolo']}")
    session.commit()


def _seed_admin(session: Session) -> None:
    email_admin = "admin@foodstore.com"
    admin_user = session.exec(
        select(Usuario).where(Usuario.email == email_admin)
    ).first()

    if not admin_user:
        hashed = bcrypt.hashpw(b"Admin1234!", bcrypt.gensalt()).decode()
        admin_user = Usuario(
            nombre="Admin",
            apellido="Principal",
            email=email_admin,
            password_hash=hashed,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        print(f" [+] Usuario administrador creado: {email_admin}")
    else:
        print(f" [✓] Usuario administrador ya existe: {email_admin}")

    asignacion = session.exec(
        select(UsuarioRol).where(
            UsuarioRol.usuario_id == admin_user.id,
            UsuarioRol.rol_codigo == "ADMIN",
        )
    ).first()

    if not asignacion:
        session.add(UsuarioRol(usuario_id=admin_user.id, rol_codigo="ADMIN"))
        session.commit()
        print(" [+] Rol 'ADMIN' asignado al usuario administrador.")
    else:
        print(" [✓] El administrador ya tiene asignado el rol 'ADMIN'.")

def _seed_user_pedidos(session: Session) -> None:
    email_admin = "pedidos@foodstore.com"
    admin_user = session.exec(
        select(Usuario).where(Usuario.email == email_admin)
    ).first()

    if not admin_user:
        hashed = bcrypt.hashpw(b"Pedidos1234!", bcrypt.gensalt()).decode()
        admin_user = Usuario(
            nombre="Pedidos",
            apellido="Principal",
            email=email_admin,
            password_hash=hashed,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        print(f" [+] Usuario pedidos creado: {email_admin}")
    else:
        print(f" [✓] Usuario pedidos ya existe: {email_admin}")

    asignacion = session.exec(
        select(UsuarioRol).where(
            UsuarioRol.usuario_id == admin_user.id,
            UsuarioRol.rol_codigo == "PEDIDOS",
        )
    ).first()

    if not asignacion:
        session.add(UsuarioRol(usuario_id=admin_user.id, rol_codigo="PEDIDOS"))
        session.commit()
        print(" [+] Rol 'PEDIDOS' asignado al usuario pedidos.")
    else:
        print(" [✓] El usuario pedidos ya tiene asignado el rol 'PEDIDOS'.")

def _seed_user_stock(session: Session) -> None:
    email_admin = "stock@foodstore.com"
    admin_user = session.exec(
        select(Usuario).where(Usuario.email == email_admin)
    ).first()

    if not admin_user:
        hashed = bcrypt.hashpw(b"Stock1234!", bcrypt.gensalt()).decode()
        admin_user = Usuario(
            nombre="Stock",
            apellido="Principal",
            email=email_admin,
            password_hash=hashed,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        print(f" [+] Usuario stock creado: {email_admin}")
    else:
        print(f" [✓] Usuario stock ya existe: {email_admin}")

    asignacion = session.exec(
        select(UsuarioRol).where(
            UsuarioRol.usuario_id == admin_user.id,
            UsuarioRol.rol_codigo == "STOCK",
        )
    ).first()

    if not asignacion:
        session.add(UsuarioRol(usuario_id=admin_user.id, rol_codigo="STOCK"))
        session.commit()
        print(" [+] Rol 'STOCK' asignado al usuario stock.")
    else:
        print(" [✓] El usuario stock ya tiene asignado el rol 'STOCK'.")

def _seed_user_client(session: Session) -> None:
    email_admin = "client@foodstore.com"
    admin_user = session.exec(
        select(Usuario).where(Usuario.email == email_admin)
    ).first()

    if not admin_user:
        hashed = bcrypt.hashpw(b"Client1234!", bcrypt.gensalt()).decode()
        admin_user = Usuario(
            nombre="Client",
            apellido="Principal",
            email=email_admin,
            password_hash=hashed,
        )
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        print(f" [+] Usuario client creado: {email_admin}")
    else:
        print(f" [✓] Usuario client ya existe: {email_admin}")

    asignacion = session.exec(
        select(UsuarioRol).where(
            UsuarioRol.usuario_id == admin_user.id,
            UsuarioRol.rol_codigo == "CLIENT",
        )
    ).first()

    if not asignacion:
        session.add(UsuarioRol(usuario_id=admin_user.id, rol_codigo="CLIENT"))
        session.commit()
        print(" [+] Rol 'CLIENT' asignado al usuario client.")
    else:
        print(" [✓] El usuario client ya tiene asignado el rol 'CLIENT'.")



def seed_db() -> None:
    print("Iniciando carga de datos (Seed)...")

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_roles(session)
        _seed_estados_pedido(session)
        _seed_formas_pago(session)
        _seed_unidades_medida(session)
        _seed_admin(session)
        _seed_user_pedidos(session)
        _seed_user_stock(session)
        _seed_user_client(session)
    print("Seed finalizado con éxito.")


if __name__ == "__main__":
    seed_db()
