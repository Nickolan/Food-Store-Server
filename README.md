# 🚀 Sistema de Gestión Integral - FastAPI & Clean Architecture

Bienvenido al repositorio central de nuestra API RESTful de grado Enterprise. Este proyecto está diseñado desde cero para soportar la operativa compleja de un sistema de pedidos, control de inventario y logística de entregas, aplicando de forma estricta **Patrones de Arquitectura Limpia (Clean Architecture)**.

---

## 🏛️ Arquitectura y Patrones de Diseño

El código base se estructura separando responsabilidades de forma quirúrgica, logrando un sistema altamente testeable, escalable y tolerante a cambios técnicos:

* **Clean/Hexagonal Architecture:** Lógica de negocio (Services) totalmente agnóstica de la capa de transporte HTTP (Routers) y de persistencia (Repositories).
* **Repository Pattern Genérico:** Toda interacción con la base de datos pasa por una abstracción de repositorio que previene la fuga de detalles de SQLModel/SQLAlchemy hacia la lógica de la aplicación.
* **Unit of Work (UoW):** Implementación del patrón transaccional por excelencia. Permite agrupar operaciones complejas (ej. *Crear pedido + Reducir stock + Notificar*) garantizando el principio ACID de forma atómica.
* **Diseño Orientado al Dominio (DDD - Lite):** La estructura del código está dividida en dominios lógicos de negocio (`/modules`), asegurando alta cohesión.

---

## 📦 Estructura de Dominios (Módulos)

### 1. 👥 Gestión de Usuarios y Roles (RBAC)
Módulo encargado de la autenticación, seguridad y control de acceso.
* **Seguridad:** Hasheo de contraseñas con `bcrypt` y validaciones robustas.
* **Control de Roles:** Implementación de roles dinámicos mediante una relación muchos-a-muchos (`UsuarioRol`) con expiración temporal (`expires_at`).
* **Soft Deletes:** Borrado lógico (`deleted_at`) preservando la integridad referencial para auditorías.

### 2. 📍 Logística y Direcciones de Entrega
Gestión integral de los destinos de envío.
* **Múltiples direcciones:** Un usuario puede tener múltiples direcciones con alias identificatorios ("Casa", "Trabajo").
* **Geolocalización:** Soporte nativo para coordenadas precisas (`latitud` y `longitud`).
* **Dirección predeterminada:** Uso de flag `es_principal` para optimizar flujos de checkout.

### 3. 🍔 Catálogo de Productos y Categorías
El núcleo del e-commerce.
* **Productos:** Control exhaustivo de precios, visibilidad (`activo`, `disponible`), gestión de stock actual y stock mínimo para alertas tempranas.
* **Categorías Múltiples (N:M):** Un producto puede cruzar diferentes categorías, estableciendo mediante `ProductoCategoriaLink` cuál es su categoría principal.
* **Unidades de Medida:** Integración con entidades de medida estandarizadas (ej. KG, Litros).

### 4. 🧀 Inventario Dinámico (Ingredientes)
Control granular de la composición de los productos.
* **Prevención de Riesgos:** Trazabilidad estricta de componentes mediante el flag `es_alergeno`.
* **Personalización (N:M):** Relación avanzada `IngredienteProductoLink`. Permite indicar la dosis exacta de un ingrediente en un producto y si el cliente tiene la opción de removerlo (`es_removible`).

### 5. 🛒 Sistema de Pedidos y Compras (Módulo 3)
El motor transaccional del negocio.
* **Snapshotting Financiero:** Los detalles del pedido guardan una "fotografía" inmutable de precios y nombres (`nombre_snapshot`, `precio_snapshot`). Garantiza que, si un producto cambia de precio mañana, el historial de facturación de hoy no se altera.
* **Costos y Descuentos:** Manejo nativo de `costo_envio` y `descuento` a nivel cabecera.
* **Personalización en tiempo real:** Los detalles de compra almacenan arreglos de personalización (`personalizacion: ARRAY`) para reflejar las alteraciones del cliente al pedido estándar (ej. sin cebolla).

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Framework Web** | [FastAPI](https://fastapi.tiangolo.com/) | Alto rendimiento, tipado estático, validación nativa y documentación Swagger autogenerada. |
| **ORM & Validaciones**| [SQLModel](https://sqlmodel.tiangolo.com/) | Fusión perfecta entre SQLAlchemy 2.0 y Pydantic. |
| **Base de Datos** | PostgreSQL / PostgreSQL Dialects | Soporte para tipos de datos complejos como `ARRAY`. |
| **Testing** | `pytest` + `pytest-asyncio` | Suite de pruebas asíncronas para validación de servicios y repositorios. |
| **Seguridad** | `passlib` + `python-jose` | Gestión robusta de JWT y hashing seguro de credenciales. |

---

## 🚀 Puesta en Marcha

1. **Clonar repositorio e instalar dependencias:**
   Recomendamos usar un entorno virtual.
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configurar el entorno:**
   Verificar el archivo `.env` o la configuración de conexión a la base de datos PostgreSQL.

3. **Ejecutar el servidor de desarrollo:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Explorar la API:**
   Ingresa a `http://localhost:8000/docs` para visualizar y probar la interfaz Swagger UI autogenerada.
