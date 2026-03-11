from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

class FasesLicitacion(str, Enum):
    OFERTA = 'oferta'
    ADJUDICACION = 'adjudicacion'

class ModoFirmaAnexo(str, Enum):
    INDIVIDUAL_EMPRESA = 'individual'
    CONJUNTO_EMPRESAS = 'conjunto'
    UTE_CONSTITUIDA = 'ute'

@dataclass(frozen=True) # Value Object que relaciona una empresa con la escritura que se usará para firmar un anexo concreto, se usa en AnexoPreparado
class FirmaEmpresa:
    empresa_id: UUID
    representacion_id: UUID
    
@dataclass
class AnexoPreparado:
    """
    Representa un anexo concreto que hay que preparar para la licitación.
    """
    licitacion_id: UUID
    codigo: str
    firmas: tuple[FirmaEmpresa, ...]  # tuple por inmutable
    generado: bool = False
        