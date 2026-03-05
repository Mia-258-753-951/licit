from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass(kw_only=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.now)
    
@dataclass
class LoteMarcadoParaPresentar(DomainEvent):
    licit_id: UUID
    lote_num: int
        
@dataclass
class LoteDesmarcadoParaPresentar(DomainEvent):
    licit_id: UUID
    lote_num: int
    
@dataclass
class LicitacionAnulada(DomainEvent):
    licit_id: UUID

    
@dataclass
class LicitacionReactivada(DomainEvent):
    licit_id: UUID
