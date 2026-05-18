from sqlmodel import Field, SQLModel
class EstadoPedidoBase(SQLModel):
    codigo: str = Field(primary_key=True, max_length=20)
    descripcion: str = Field(max_length=80, nullable=False)
    orden:int = Field(nullable=False)
    es_terminal:bool = Field(nullable=False)
class EstadoPedido(EstadoPedidoBase, table=True):
    pass