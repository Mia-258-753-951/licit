from dataclasses import dataclass
from enum import Enum

class FasesLicitacion(str, Enum):
    OFERTA = 'oferta'
    ADJUDICACION = 'adjudicacion'

class ModoFirmaAnexo(str, Enum):
    INDIVIDUAL_EMPRESA = 'individual'
    CONJUNTO_EMPRESAS = 'conjunto'
    UTE_CONSTITUIDA = 'ute'

@dataclass
class TipoAnexo:    # catálogo de anexos
    codigo: str
    nombre: str
    fase: FasesLicitacion
    modo_firma: ModoFirmaAnexo