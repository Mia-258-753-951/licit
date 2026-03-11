from uuid import UUID

from licit.application.services.event_dispatcher import EventDispatcher
from licit.application.ports.repositories import LicitacionRepository

class MarcarLotePresentable:
    def __init__(self, licitacion_repo: LicitacionRepository, dispatcher: EventDispatcher):
        self.licitacion_repo = licitacion_repo
        self.dispatcher = dispatcher
        
    def execute(
        self, 
        licitacion_id: UUID, 
        num_lote: int, 
        a_presentar: bool
        ) -> None:
        licitacion = self.licitacion_repo.get(licitacion_id)
        
        licitacion.set_presentable(num_lote, a_presentar)
        
        self.licitacion_repo.save(licitacion)
        
        eventos = licitacion.pull_events()
        self.dispatcher.dispatch(eventos)
        