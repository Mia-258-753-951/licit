from dataclasses import dataclass
from pathlib import Path

from licit.domain.anexos.models import FasesLicitacion, ModoFirmaAnexo

@dataclass(frozen=True)
class AnexoTemplate:    # representa la plantilla detectada en disco
    codigo: str
    fase: FasesLicitacion
    modo_firma: ModoFirmaAnexo
    template_path: Path