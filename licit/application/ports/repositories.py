from uuid import UUID
from typing import Protocol

from licit.domain.licitacion.models import Licitacion
from licit.domain.terceros.models import RepresentacionEmpresa
from licit.domain.anexos.models import FasesLicitacion

class LicitacionRepository(Protocol):
    
    def get(self, licitacion_id: UUID) -> Licitacion: ...
    
    def save(self, licitacion: Licitacion) -> None: ...
    
class RepresentacionRepository(Protocol):
    
    def get(self, representacion_id: UUID) -> RepresentacionEmpresa: ...
    

