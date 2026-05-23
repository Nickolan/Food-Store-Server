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


def _seed_admin(session: Session) -> None:
    email_admin = "admin@admin.com"
    admin_user = session.exec(
        select(Usuario).where(Usuario.email == email_admin)
    ).first()

    if not admin_user:
        hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
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



def seed_db() -> None:
    print("Iniciando carga de datos (Seed)...")

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_roles(session)
        _seed_estados_pedido(session)
        _seed_formas_pago(session)
        _seed_admin(session)

    print("Seed finalizado con éxito.")


if __name__ == "__main__":
    seed_db()
