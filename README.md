# 🚀 Sistema de Gestión Integral — FastAPI & Clean Architecture

Bienvenido al repositorio central de nuestra API RESTful de grado Enterprise. Este proyecto está diseñado desde cero para soportar la operativa compleja de un sistema de pedidos, control de inventario y logística de entregas, aplicando de forma estricta **Patrones de Arquitectura Limpia (Clean Architecture)**.

---

## Equipo y Entregables (Examen)

- **Nombre del equipo:** Equipo BOT
- **Integrantes:**
   - **1:** Nicolas Navarrete
   - **2:** Lautaro Ferreria
   - **3:** Rafael Navarro
   - **4:** Lucas Gordillo
- **Video Parcial 1 Code:** [Video Code Parcial 1](https://www.youtube.com/watch?v=ATKjDeNDJtU)
- **Video Parcial 1 Demo:** [Demo Parcial 1](https://www.youtube.com/watch?v=a2QTgLh3ZZE)   
- **Video Parcial 2:** [Enlace al Video Parcial 2](https://drive.google.com/drive/folders/1n_cFn1rpYdJr5lxDtNeoFVYwZ87M9CdJ?usp=sharing)
- **Video (demostración):** [Enlace al video 3](https://drive.google.com/drive/folders/1oW7RY88o79zgZGz9HX_dnWvFwinoY1Dx)

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
| **ORM & Validaciones** | [SQLModel](https://sqlmodel.tiangolo.com/) | Fusión perfecta entre SQLAlchemy 2.0 y Pydantic. |
| **Base de Datos** | PostgreSQL | Soporte para tipos de datos complejos como `ARRAY`. |
| **Migraciones** | Alembic | Versionado del esquema de base de datos. |
| **Testing** | `pytest` + `pytest-asyncio` | Suite de pruebas asíncronas para validación de servicios y repositorios. |
| **Seguridad** | `passlib` + `python-jose` | Gestión robusta de JWT y hashing seguro de credenciales. |
| **Imágenes** | Cloudinary | Subida y gestión de imágenes de productos. |
| **Pagos** | Mercado Pago SDK | Integración de checkout y webhooks de pago. |

---

## 🖥️ Prerrequisitos (máquina limpia)

Antes de empezar, asegurate de tener instalado:

| Herramienta | Versión mínima | Verificación |
| :--- | :--- | :--- |
| **Python** | 3.11+ | `python --version` |
| **PostgreSQL** | 14+ | `psql --version` |
| **pip** | incluido con Python | `pip --version` |

> **Windows:** PostgreSQL se descarga desde [postgresql.org/download/windows](https://www.postgresql.org/download/windows/). Durante la instalación anotá el usuario (`postgres`) y la contraseña que configurás — las vas a necesitar en el `.env`.

---

## 🚀 Setup paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/Nickolan/Food-Store-Server.git
cd Food-Store-Server
```

### 2. Crear y activar el entorno virtual

```bash
# Crear el venv
python -m venv .venv

# Activar — Linux/macOS
source .venv/bin/activate

# Activar — Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activar — Windows (CMD)
.venv\Scripts\activate.bat
```

> Deberías ver `(.venv)` al inicio del prompt cuando esté activo.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear la base de datos en PostgreSQL

Conectate a PostgreSQL con tu cliente preferido (psql, pgAdmin, DBeaver) y ejecutá:

```sql
CREATE DATABASE db_parcial_python;
```

> Si querés usar otro nombre, acordate de reflejarlo en `DATABASE_URL` del `.env`.

### 5. Configurar las variables de entorno

Copiá el archivo de ejemplo:

```bash
# Linux/macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Abrí `.env` y completá **todos** los campos:

```env
# ─── PostgreSQL ───────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:nikolan@localhost:5432/db_parcial_python 

# ─── JWT ──────────────────────────────────────────────────────────────────────
# Generá una clave segura con:
#   python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=clave-secreta-de-minimo-32-caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Formato JSON array — incluí el origen de tu frontend
CORS_ORIGINS=["http://localhost:5173"]

# ─── Frontend ─────────────────────────────────────────────────────────────────
FRONTEND_URL=http://localhost:5173

# ─── Mercado Pago ─────────────────────────────────────────────────────────────
# Credenciales de prueba: https://www.mercadopago.com.ar/developers/panel/app
MP_ACCESS_TOKEN=TEST-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MP_WEBHOOK_URL=https://tu-dominio-ngrok.ngrok-free.dev

# ─── Cloudinary ───────────────────────────────────────────────────────────────
# Credenciales: https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

> **Nota:** Si solo querés levantar el servidor localmente sin pagos ni imágenes, podés poner valores ficticios para `MP_*` y `CLOUDINARY_*` (ej. `TEST-xxx` y `dummy`). La API arranca igual, solo fallarán los endpoints de pago y subida de imágenes.

### 6. Cargar datos iniciales

Ejecuta el seed para inicializar la base de datos con datos predefinidos:

```bash
python -m app.db.seed
```

### 7. Levantar el servidor

```bash
uvicorn app.main:app --reload
```

El servidor arranca en `http://localhost:8000`.

El flag `--reload` activa el hot-reload: el servidor se reinicia automáticamente cada vez que guardás un archivo Python.

> **Nota:** Si el comando uvicorn no funcion, intenta con `python -m fastapi dev .\app\main.py`

---

## ✅ Verificación

Una vez que el servidor esté corriendo, abrí estas URLs en el navegador:

| URL | Qué muestra |
| :--- | :--- |
| `http://localhost:8000/docs` | **Swagger UI** — documentación interactiva completa |
| `http://localhost:8000/redoc` | ReDoc — documentación alternativa |
| `http://localhost:8000/debug/ws-rooms` | Estado de conexiones WebSocket activas |

Si ves la interfaz de Swagger, el setup está completo. 🎉

---

## 🐛 Problemas frecuentes

### `connection refused` al conectar con PostgreSQL
- Verificá que el servicio de PostgreSQL esté corriendo.
  - Linux: `sudo systemctl status postgresql`
  - Windows: buscá "Servicios" → `postgresql-x64-XX`
- Confirmá que `DATABASE_URL` en el `.env` coincidan con tu instalación local.

### `ModuleNotFoundError`
- Asegurate de haber **activado el entorno virtual** antes de correr `pip install` y `uvicorn`.
- El prompt debe mostrar `(.venv)` al inicio.

### `SECRET_KEY field required` u otros campos requeridos
- El archivo `.env` debe estar en la raíz del directorio `Server/`, al mismo nivel que `alembic.ini` y `requirements.txt`.
- Verificá que no haya espacios alrededor del `=` en las variables (correcto: `SECRET_KEY=valor`, incorrecto: `SECRET_KEY = valor`).

### `alembic: command not found`
- Probá `python -m alembic upgrade head` (Alembic se instala dentro del venv, no globalmente).

### Error de CORS al conectar el frontend
- Asegurate de que la URL de tu frontend esté incluida en `CORS_ORIGINS` del `.env`.
- Formato correcto: `CORS_ORIGINS=["http://localhost:5173"]` (JSON array, con comillas en las URLs).

---

## 🧪 Correr los tests

```bash
pytest -v

pytest -v -k "rate_limit" # Para test de limite de uso
```

Los tests usan SQLite en memoria (configurado en `conftest.py`), por lo que **no necesitás PostgreSQL corriendo** para ejecutarlos.
