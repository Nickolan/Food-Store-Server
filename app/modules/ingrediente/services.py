from typing import List, Optional, Tuple

from sqlalchemy.orm import selectinload

from fastapi import HTTPException, status

from sqlmodel import Session, select, func

from datetime import datetime



from app.modules.ingrediente.models import Ingrediente, IngredienteProductoLink

from app.modules.producto.models import Producto

from app.modules.ingrediente.schemas import IngredienteProductoAssign, IngredienteRead, IngredienteCreate, IngredienteUpdate, IngredientePaginadoResponse, IngredienteReadFull

from app.modules.ingrediente.unit_of_work import IngredienteUnitOfWork





class IngredienteService:

    """

    Servicio de Ingredientes



    """



    def __init__(self, session: Session) -> None:

        self._session = session



    # Helpers privados



    def _get_or_404(self, uof: IngredienteUnitOfWork, ingrediente_id: int) -> Ingrediente:

        ingrediente = uof.ingredientes.get_by_id(ingrediente_id)

        if not ingrediente:

            raise HTTPException(

                status_code=status.HTTP_404_NOT_FOUND,

                detail=f"Ingrediente con ID {ingrediente_id} no encontrado."

            )

        return ingrediente

   

    def _get_with_productos_or_404(self, uof: IngredienteUnitOfWork, ingrediente_id: int) -> Ingrediente:

        ingrediente = uof.ingredientes.get_with_productos(ingrediente_id)

        if not ingrediente:

            raise HTTPException(

                status_code=status.HTTP_404_NOT_FOUND,

                detail=f"Ingrediente con ID {ingrediente_id} no encontrado."

            )

        return ingrediente

   

    def _get_producto_or_404(self, uof: IngredienteUnitOfWork, producto_id: int) -> Producto:

        producto = uof.productos.get_by_id(producto_id)

        if not producto:

            raise HTTPException(

                status_code=status.HTTP_404_NOT_FOUND,

                detail=f"Producto con ID {producto_id} no encontrado."

            )

        return producto

   

    def _es_removible(self, uof: IngredienteUnitOfWork, ingrediente_id: int, producto_id: int) -> bool:

        link = uof.ingredientes.get_link(ingrediente_id, producto_id)

        return link.es_removible if link else False

   

    def _existe_link(self, uof: IngredienteUnitOfWork, ingrediente_id: int, producto_id: int) -> bool:

        link = uof.ingredientes.get_link(ingrediente_id, producto_id)

        return link is not None

   

    # Casos de uso



    def crear(self, data: IngredienteCreate) -> Ingrediente:

        with IngredienteUnitOfWork(self._session) as uow:

            statement = select(Ingrediente).where(Ingrediente.nombre == data.nombre)

            existente = uow.ingredientes.session.exec(statement).first()



            if existente and existente.activo and data.activo:

                raise HTTPException(

                    status_code=status.HTTP_400_BAD_REQUEST,

                    detail=f"Ya existe un ingrediente activo con el nombre '{data.nombre}'."

                )

            ingrediente = Ingrediente.model_validate(data)

            uow.ingredientes.add(ingrediente)

            result = IngredienteRead.model_validate(ingrediente)

        return result



    def listar(self, offset: int = 0, limit: int = 20) -> IngredientePaginadoResponse:

        with IngredienteUnitOfWork(self._session) as uow:

            ingredientes = uow.ingredientes.get_paginado(offset, limit)

            total = uow.ingredientes.count()

            items = [IngredienteRead.model_validate(ing) for ing in ingredientes]



            result = IngredientePaginadoResponse(

                total=total,

                items=items

            )

        return result

   

    def obtener_por_id(self, ingrediente_id: int) -> IngredienteReadFull:

        with IngredienteUnitOfWork(self._session) as uow:

            ingrediente = self._get_with_productos_or_404(uow, ingrediente_id)

            result = IngredienteReadFull.model_validate(ingrediente)

        return result

   

    def actualizar(self, ingrediente_id: int, data: IngredienteUpdate) -> IngredienteRead:

        with IngredienteUnitOfWork(self._session) as uow:

            ingrediente = self._get_or_404(uow, ingrediente_id)

            update_data = data.model_dump(exclude_unset=True)

            nuevo_nombre = update_data.get("nombre")

            intentando_activar = update_data.get("activo") is True



            # Validamos si:

            # 1. El nombre cambió por uno nuevo.

            # 2. El nombre es el mismo pero se está intentando poner en 'activo: true'.

            if (nuevo_nombre and nuevo_nombre != ingrediente.nombre) or intentando_activar:

           

                nombre_a_chequear = nuevo_nombre or ingrediente.nombre

           

                statement = select(Ingrediente).where(

                    Ingrediente.nombre == nombre_a_chequear,

                    Ingrediente.activo == True,

                    Ingrediente.id != ingrediente_id

                )

                existente = uow.ingredientes.session.exec(statement).first()

                if existente:

                    raise HTTPException(

                        status_code=status.HTTP_400_BAD_REQUEST,

                        detail=f"Operación inválida: Ya existe otro ingrediente activo llamado '{nombre_a_chequear}'."

                    )

            for key, value in update_data.items():

                setattr(ingrediente, key, value)

            ingrediente.updated_at = datetime.now(datetime.UTC)

            uow.ingredientes.add(ingrediente)

            result = IngredienteRead.model_validate(ingrediente)

            return result

   

    def eliminar(self, ingrediente_id: int) -> None:

        with IngredienteUnitOfWork(self._session) as uow:

            ingrediente = self._get_or_404(uow, ingrediente_id)

            uow.ingredientes.delete(ingrediente)

    def desactivar(self, ingrediente_id: int) -> IngredienteRead:

        with IngredienteUnitOfWork(self._session) as uow:

            ingrediente = self._get_or_404(uow, ingrediente_id)

            ingrediente.activo = False

            ingrediente.updated_at = datetime.now(datetime.UTC)

            uow.ingredientes.add(ingrediente)

            result = IngredienteRead.model_validate(ingrediente)

        return result



    def agregar_a_producto(self, ingrediente_id: int, body: IngredienteProductoAssign) -> IngredienteReadFull:

        with IngredienteUnitOfWork(self._session) as uow:

            existe_link = self._existe_link(uof=uow, ingrediente_id=ingrediente_id, producto_id=body.producto_id)

            if existe_link:

                raise HTTPException(

                    status_code=status.HTTP_400_BAD_REQUEST,

                    detail=f"El ingrediente con ID {ingrediente_id} ya está asignado al producto con ID {body.producto_id}."

                )

            ingrediente = self._get_or_404(uow, ingrediente_id)

            self._get_producto_or_404(uow, body.producto_id)

            uow.ingredientes.link_producto(ingrediente_id, body.producto_id, body.es_removible)

            result = IngredienteReadFull.model_validate(ingrediente)

        return result

   

    def remover_de_producto(self, ingrediente_id: int, producto_id: int) -> IngredienteReadFull:

        with IngredienteUnitOfWork(self._session) as uow:

            ingrediente = self._get_or_404(uof=uow, ingrediente_id=ingrediente_id)

            if not self._es_removible(uof=uow, ingrediente_id=ingrediente_id, producto_id=producto_id):

                raise HTTPException(

                    status_code=status.HTTP_400_BAD_REQUEST,

                    detail=f"El ingrediente con ID {ingrediente_id} no es removible del producto con ID {producto_id}."

                )

            self._get_producto_or_404(uof=uow, producto_id=producto_id)

            uow.ingredientes.unlink_producto(ingrediente_id, producto_id)

            result = IngredienteReadFull.model_validate(ingrediente)

        return result