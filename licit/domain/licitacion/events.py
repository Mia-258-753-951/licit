from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

@dataclass(kw_only=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.now)
    
    @property
    def coalesce_key(self) -> tuple | None:
        return None  # esto hace que el valor por defecto sea None, salvo implementación en contrario
    
@dataclass(kw_only=True)
class LoteMarcadoParaPresentar(DomainEvent):
    licit_id: UUID
    lote_num: int
    
    @property
    def coalesce_key(self) -> tuple | None:
        return (self.licit_id, self.lote_num)
        
@dataclass(kw_only=True)
class LoteDesmarcadoParaPresentar(DomainEvent):
    licit_id: UUID
    lote_num: int
    
    @property
    def coalesce_key(self) -> tuple | None:
        return (self.licit_id, self.lote_num)
    
@dataclass(kw_only=True)
class LicitacionAnulada(DomainEvent):
    licit_id: UUID
    
    @property
    def coalesce_key(self) -> tuple | None:
        return (self.licit_id,)
    
@dataclass(kw_only=True)
class LicitacionReactivada(DomainEvent):
    licit_id: UUID
    
    @property
    def coalesce_key(self) -> tuple | None:
        return (self.licit_id,)
