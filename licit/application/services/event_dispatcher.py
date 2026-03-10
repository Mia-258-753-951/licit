from typing import Callable

from licit.application.handlers.licitacion_handlers import handle_licitacion_anulada, handle_licitacion_reactivada
from licit.application.handlers.lote_handlers import handle_lote_desmarcado, handle_lote_marcado
from licit.application.services.event_coalescer import coalesce

from licit.domain.licitacion.events import (
    DomainEvent, 
    LoteMarcadoParaPresentar, 
    LoteDesmarcadoParaPresentar,
    LicitacionAnulada,
    LicitacionReactivada,
    )

handlers = {
    LoteMarcadoParaPresentar: handle_lote_marcado,
    LoteDesmarcadoParaPresentar: handle_lote_desmarcado,
    LicitacionAnulada: handle_licitacion_anulada,
    LicitacionReactivada: handle_licitacion_reactivada,
}

class EventDispatcher:
    def __init__(self, handlers: dict[type, Callable]=handlers) -> None:
        self.handlers = handlers
        
    def dispatch(self, events: list[DomainEvent]) -> None:
        result_events = coalesce(events)
        
        for event in result_events:
            if type(event) not in self.handlers:
                raise KeyError(f'No existe handler para este DomainEvent: {type(event)}')
            handler = self.handlers[type(event)]
            handler(event)
        