"""
Script de inicialización (Seed) de la Base de Datos.
Cumple con el requisito del UML: "Seed obligatorio (app/db/seed.py)".

Carga los roles base del sistema y crea el primer usuario administrador.
Es idempotente (se puede ejecutar múltiples veces sin duplicar datos).
"""

from sqlmodel import Session, select
import bcrypt
from app.core.database import engine
from app.modules.usuario.models import Usuario, Rol, UsuarioRol

# Roles base extraídos estrictamente del UML
ROLES_BASE = [
    {
        "codigo": "ADMIN",
        "nombre": "Administrador",
        "descripcion": "Acceso total sin restricciones"
    },
    {
        "codigo": "STOCK",
        "nombre": "Gestión de Stock",
        "descripcion": "Actualiza stock y disponible"
    },
    {
        "codigo": "PEDIDOS",
        "nombre": "Gestión de Pedidos",
        "descripcion": "Avanza estados CONFIRMADO -> ENTREGADO"
    },
    {
        "codigo": "CLIENT",
        "nombre": "Cliente",
        "descripcion": "Opera solo sus propios datos"
    }
]

from sqlmodel import Session, select, SQLModel  # <-- Agregamos SQLModel acá
import bcrypt
from app.core.database import engine
from app.modules.usuario.models import Usuario, Rol, UsuarioRol

# ... (Lista de ROLES_BASE queda igual) ...

def seed_db():
    print("Iniciando carga de datos (Seed)...")
    
    # Esto le ordena a SQLModel crear cualquier tabla que falte en Postgres antes de continuar
    SQLModel.metadata.create_all(engine) 
    
    with Session(engine) as session:
        # 1. Cargar Roles
        for rol_data in ROLES_BASE:
            rol_existente = session.exec(select(Rol).where(Rol.codigo == rol_data["codigo"])).first()
            if not rol_existente:
                nuevo_rol = Rol(**rol_data)
                session.add(nuevo_rol)
                print(f" [+] Rol creado: {rol_data['codigo']}")
            else:
                print(f" [✓] Rol ya existe: {rol_data['codigo']}")
        
        session.commit() # Guardamos los roles primero para poder asignarlos

        # 2. Crear Usuario Administrador
        email_admin = "admin@admin.com"
        admin_user = session.exec(select(Usuario).where(Usuario.email == email_admin)).first()
        
        if not admin_user:
            password = "admin"
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            admin_user = Usuario(
                nombre="Admin",
                apellido="Principal",
                email=email_admin,
                password_hash=hashed
            )
            session.add(admin_user)
            session.commit() # Guardamos para que se le asigne un ID
            session.refresh(admin_user)
            print(f" [+] Usuario administrador creado: {email_admin}")
        else:
            print(f" [✓] Usuario administrador ya existe: {email_admin}")

        # 3. Asignar rol ADMIN al usuario administrador
        asignacion_existente = session.exec(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == admin_user.id,
                UsuarioRol.rol_codigo == "ADMIN"
            )
        ).first()

        if not asignacion_existente:
            nueva_asignacion = UsuarioRol(
                usuario_id=admin_user.id,
                rol_codigo="ADMIN"
                # asignado_por_id queda en None porque es un proceso del sistema
            )
            session.add(nueva_asignacion)
            session.commit()
            print(" [+] Rol 'ADMIN' asignado al usuario administrador.")
        else:
            print(" [✓] El administrador ya tiene asignado el rol 'ADMIN'.")

    print("Seed finalizado con éxito.")

if __name__ == "__main__":
    seed_db()