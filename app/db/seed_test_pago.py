import os
from sqlalchemy import text
from app.core.database import engine

def run_seed_test_pago():
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Obtener usuario
            res = conn.execute(text("SELECT id, email FROM usuario WHERE email='admin@admin.com' LIMIT 1")).fetchone()
            if not res:
                print("No admin user found")
                return
            usuario_id = res[0]
            usuario_email = res[1]

            # 2. Insert direccion
            dir_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM \"direccionEntrega\"")).scalar()
            conn.execute(text("""
                INSERT INTO "direccionEntrega" (id, usuario_id, linea1, ciudad, codigo_postal, es_principal, created_at, updated_at) 
                VALUES (:id, :uid, 'Av. Siempre Viva 742', 'Springfield', '1234', false, NOW(), NOW())
            """), {"id": dir_id, "uid": usuario_id})

            # 3. Insert categoria
            cat_id = conn.execute(text("SELECT id FROM categoria WHERE nombre = 'Hamb Test' LIMIT 1")).scalar()
            if not cat_id:
                cat_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM categoria")).scalar()
                conn.execute(text("""
                    INSERT INTO categoria (id, nombre, descripcion, activo, created_at, updated_at) 
                    VALUES (:id, 'Hamb Test', 'test', true, NOW(), NOW())
                """), {"id": cat_id})

            # 4. Insert producto
            prod_id = conn.execute(text("SELECT id FROM producto WHERE nombre = 'Hamb MP' LIMIT 1")).scalar()
            if not prod_id:
                prod_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM producto")).scalar()
                # NO incluye unidad_venta_id para evitar el error
                conn.execute(text("""
                    INSERT INTO producto (id, nombre, descripcion, precio_base, stock, stock_minimo, activo, disponible, created_at, updated_at) 
                    VALUES (:id, 'Hamb MP', 'Hamb', 1500.00, 100, 10, true, true, NOW(), NOW())
                """), {"id": prod_id})

                # Link prod-cat
                conn.execute(text("""
                    INSERT INTO producto_categoria_link (producto_id, categoria_id, es_principal, created_at)
                    VALUES (:pid, :cid, true, NOW())
                """), {"pid": prod_id, "cid": cat_id})

            # 5. Insert pedido
            ped_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) + 1 FROM pedido")).scalar()
            conn.execute(text("""
                INSERT INTO pedido (id, usuario_id, direccion_id, estado_codigo, forma_pago_codigo, subtotal, descuento, costo_envio, total, created_at, updated_at)
                VALUES (:id, :uid, :did, 'PENDIENTE', 'MERCADOPAGO', 1500.00, 0, 50, 1550.00, NOW(), NOW())
            """), {"id": ped_id, "uid": usuario_id, "did": dir_id})

            # 6. Insert detalle
            conn.execute(text("""
                INSERT INTO detallepedido (pedido_id, producto_id, cantidad, nombre_snapshot, precio_snapshot, subtotal_snap, created_at)
                VALUES (:ped_id, :prod_id, 1, 'Hamb MP', 1500.00, 1500.00, NOW())
            """), {"ped_id": ped_id, "prod_id": prod_id})

            trans.commit()

            print(f"=== PRUEBA LISTA ===")
            print(f"Pedido creado con ID: {ped_id}")
            print(f"Usuario: {usuario_email}")
            print(f"Monto Total: $1550.00")
        except Exception as e:
            trans.rollback()
            print("Error:", e)

if __name__ == "__main__":
    run_seed_test_pago()
