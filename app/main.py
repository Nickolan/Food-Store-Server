from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel
from app.core.database import engine
from fastapi.middleware.cors import CORSMiddleware
from app.core.rate_limiter import RateLimitMiddleware  

from app.modules.categoria.models import Categoria 
from app.modules.producto.models import Producto, ProductoCategoriaLink
from app.modules.ingrediente.models import Ingrediente, IngredienteProductoLink
from app.modules.usuario.models import Usuario
from app.modules.direccionEntrega.models import DireccionEntrega

from app.modules.producto.routers import router as producto_router
from app.modules.categoria.routers import router as categoria_router
from app.modules.ingrediente.routers import router as ingrediente_router
from app.modules.usuario.routers import router as usuario_router
from app.modules.direccionEntrega.routers import router as direccion_router
from app.modules.modulo3.Pedido.router import router as pedido_router
from app.modules.modulo3.Pago.router import router as pago_router
from app.modules.unidad_medida.routers import router as unidad_medida_router
from app.modules.estadisticas.router import router as estadisticas_router
from app.modules.imagenes.router import router as uploads_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: crea todas las tablas registradas en SQLModel.metadata.
    Shutdown: espacio para cerrar conexiones, caches, etc.
    """
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="FastAPI + SQLModel — Relaciones 1:1 · 1:N · N:M",
    version="Tesis",
    description=(
        "Proyecto modular que demuestra las tres relaciones principales:\n\n"
        "- **1:N** Categoria → Productos (FK `categoria_id` en Producto, lado N)\n"
        "- **N:M** Producto ↔ Categoria via `ProductoCategoriaLink`\n"
        "- **N:M** Producto ↔ Ingrediente via `IngredienteProductoLink`\n"
        "- **1:N** Usuario → Direcciones de entrega (un usuario puede tener varias)\n"
        "- **N:M** Usuario ↔ Roles (asignación de permisos)\n"
        "- **1:N** UnidadMedida → Productos e Ingredientes (normalización de unidades)\n\n"
        "Cada módulo tiene sus propios modelos, esquemas, servicios y routers, "
    ),
    lifespan=lifespan,
    redirect_slashes=False,
)
app.add_middleware(RateLimitMiddleware, max_attempts=5, window_seconds=900)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(producto_router)
app.include_router(categoria_router)
app.include_router(ingrediente_router)
app.include_router(usuario_router)
app.include_router(direccion_router)
app.include_router(pedido_router)
app.include_router(unidad_medida_router)
app.include_router(pago_router)
app.include_router(estadisticas_router)

app.include_router(uploads_router)
@app.get("/debug/ws-rooms", tags=["debug"])
def ws_rooms():
    from app.core.websocket import manager
    return {
        "total_connections": manager.get_active_connections_count(),
        "rooms": manager.get_rooms_info(),
    }


@app.get("/checkout/success")
async def handle_success():
  return RedirectResponse(url="http://localhost:5173/success")
@app.get("/checkout/failure")
async def handle_failure():
  return RedirectResponse(url="http://localhost:5173/failure")