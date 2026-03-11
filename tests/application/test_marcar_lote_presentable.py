
from collections.abc import Callable
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock
import pytest

from licit.application.licitacion.marcar_lote_presentable import MarcarLotePresentable
from licit.application.ports.repositories import LicitacionRepository
from licit.application.services.event_dispatcher import EventDispatcher
from licit.domain.licitacion.events import LoteMarcadoParaPresentar, DomainEvent
from licit.domain.licitacion.models import Licitacion, Lote

class FakeLicitacionRepository(LicitacionRepository):
    def __init__(self):
        self.licitaciones = {}
        
    def get(self, licitacion_id):
        return self.licitaciones[licitacion_id]
    
    def save(self, licitacion):
        self.licitaciones[licitacion.id] = licitacion

class FakeEventDispatcher(EventDispatcher):
    def __init__(self, handlers: dict[type, Callable]) -> None:
        self.handlers = handlers
        
    def dispatch(self, events: list[DomainEvent]) -> None:
        for event in events:
            if type(event) not in self.handlers:
                raise KeyError(f'No existe handler para este DomainEvent: {type(event)}')
            handler = self.handlers[type(event)]
            handler(event)

def test_marcar_lote_presentable():
    mock_handler = Mock()
    handler = {
    LoteMarcadoParaPresentar: mock_handler,
}
    licitacion_repo = FakeLicitacionRepository()
    dispatcher = FakeEventDispatcher(handler)
    
    use_case = MarcarLotePresentable(licitacion_repo, dispatcher)
        
    lote = Lote(
        num_lote=1, 
        descripcion='Lote 1', 
        a_presentar=False,
        importe_lote=100000,
        nombre_lote='Lote 1',)
    
    licit = Licitacion(
        id_org_licit=uuid4(),
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
        lotes = [lote],
    )
    licitacion_repo.save(licit)
    
    use_case.execute(
        licitacion_id=licit.id,
        num_lote=1,
        a_presentar=True,
    )
    
    assert licitacion_repo.get(licit.id).lotes[0].a_presentar == True   
    mock_handler.assert_called_once()
    args, kargs = mock_handler.call_args
    event = args[0]
    assert isinstance(event, LoteMarcadoParaPresentar)
    assert event.lote_num == 1

def test_marcar_lote_presentable_con_lote_inexistente():
    mock_handler = Mock()
    handler = {
    LoteMarcadoParaPresentar: mock_handler,
}
    licitacion_repo = FakeLicitacionRepository()
    dispatcher = FakeEventDispatcher(handler)
    
    use_case = MarcarLotePresentable(licitacion_repo, dispatcher)
    
    lote = Lote(
        num_lote=2, 
        descripcion='Lote 1', 
        a_presentar=False,
        importe_lote=100000,
        nombre_lote='Lote 1',)
    
    licit = Licitacion(
        id_org_licit=uuid4(),
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
        lotes = [lote],
    )
    licitacion_repo.save(licit)
    
    with pytest.raises(KeyError) as exc:
        use_case.execute(
        licitacion_id=licit.id,
        num_lote=1,
        a_presentar=True,
    )
    assert exc.value.args[0] == 'No existe el lote núm. 1'
    mock_handler.assert_not_called()