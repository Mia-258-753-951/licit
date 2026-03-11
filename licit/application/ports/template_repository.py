from typing import Protocol
from uuid import UUID

from licit.application.anexos.models import AnexoTemplate
from licit.domain.anexos.models import FasesLicitacion

class TemplateRepository(Protocol):
    
    def list_by_fase(
        self,
        licitacion_id: UUID,
        fase: FasesLicitacion,
        ) -> list[AnexoTemplate]:
        ...