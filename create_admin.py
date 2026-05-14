from sqlmodel import Session
import bcrypt
from app.core.database import engine
from app.modules.usuario.models import Usuario

def create_admin():
    with Session(engine) as session:
        # Check if exists
        existing = session.query(Usuario).filter(Usuario.email == "admin@admin.com").first()
        if existing:
            print("El administrador ya existe.")
            return
        
        password = "admin"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        admin = Usuario(
            nombre="Admin",
            apellido="Principal",
            email="admin@admin.com",
            password_hash=hashed
        )
        session.add(admin)
        session.commit()
        print("Usuario administrador creado exitosamente. Email: admin@admin.com / Password: admin")

if __name__ == "__main__":
    create_admin()
