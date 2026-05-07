# API de Gestión de Inventario Pro - FastAPI & Clean Architecture 🚀

API RESTful de alto rendimiento diseñada para la gestión integral de productos, categorías e ingredientes. Este proyecto implementa **Patrones de Diseño Enterprise** para garantizar la escalabilidad, la integridad transaccional y un código desacoplado.

## 🌟 Highlights Técnicos

* **Arquitectura por Capas:** Separación clara entre modelos, repositorios, servicios y controladores.
* **Repository Pattern:** Abstracción de la lógica de acceso a datos mediante repositorios genéricos y específicos.
* **Unit of Work (UoW):** Gestión de transacciones atómicas para asegurar la consistencia de la base de datos en operaciones complejas.
* **Relaciones N:M Avanzadas:** Implementación de relaciones Muchos a Muchos con atributos adicionales en las tablas intermedias (ej. ingredientes removibles).
* **Optimización de Consultas:** Estrategias para evitar el problema de N+1 y manejo eficiente de importaciones circulares en SQLModel.

## 🛠️ Tecnologías Utilizadas

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **ORM & Validación:** [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic)
* **Base de Datos:** Soporte para PostgreSQL y SQLite.
* **Lenguaje:** Python 3.10+

## 📁 Estructura del Proyecto

El proyecto sigue una organización modular por dominios (features):

```text
app/
├── core/
│   ├── database.py         # Configuración de DB y Session
│   ├── repository.py       # BaseRepository genérico
│   └── unit_of_work.py     # Clase base para gestión transaccional
├── modules/
│   ├── producto/
│   │   ├── models.py       # Entidad Producto y Tabla Link N:M
│   │   ├── repository.py   # Repositorio especializado
│   │   ├── services.py     # Lógica de negocio
│   │   └── router.py       # Endpoints
│   ├── categoria/
│   │   └── ...             # Estructura homóloga
│   └── ingrediente/        # <--- Nuevo Módulo N:M
│       ├── models.py       # Entidad e IngredienteProductoLink
│       ├── repository.py
│       └── unit_of_work.py
└── main.py                 # Punto de entrada
```

✨ Funcionalidades Principales
1. Gestión de Categorías (CRUD): Creación, listado, actualización total y borrado lógico.

2. Gestión de Productos (CRUD): Control detallado de productos incluyendo precio, stock y stock mínimo.

3. Relación N:M: * Un producto puede pertenecer a múltiples categorías.

    * Una categoría puede agrupar múltiples productos.

    * Endpoints dedicados para asignar y remover categorías de un producto específico.

4. Control de Stock: Endpoint específico de lógica de negocio para evaluar si un producto requiere reposición (alerta de stock bajo).

5. Borrado Lógico: Las entidades no se eliminan físicamente de la base de datos, sino que cambian su estado activo a False para mantener la integridad histórica.

