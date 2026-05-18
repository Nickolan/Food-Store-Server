from datetime import datetime
from typing import Generic, Optional, TypeVar, Type, Sequence
from sqlmodel import Session, SQLModel, select

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    
    def __init__(self, session: Session, model: Type[ModelT]) -> None:
        
        self.session = session
        self.model = model

    def get_by_id(self, record_id: int) -> ModelT | None:
        
        return self.session.get(self.model, record_id)

    def get_all(self, offset: int = 0, limit: int = 20) -> Sequence[ModelT]:
       
        return self.session.exec(
            select(self.model).offset(offset).limit(limit)
        ).all()

    def add(self, instance: ModelT) -> ModelT:
        print("Ejecutando Add")
        self.session.add(instance)
        self.session.flush()  # obtiene el ID sin hacer commit
        self.session.refresh(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        
        self.session.delete(instance)
        self.session.flush()
    
    def borrado_logico(self, record_id: int) -> ModelT | None:
        resultado = self.get_by_id(record_id)
        if resultado:
            if hasattr(resultado, "activo"):
                resultado.activo = False
            if hasattr(resultado, "deleted_at"):
                resultado.deleted_at = datetime.now()
            
            self.session.add(resultado)
            self.session.flush()   
            self.session.refresh(resultado)
        return resultado