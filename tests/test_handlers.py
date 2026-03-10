
from datetime import datetime, date
from unittest.mock import Mock, call
import pytest

from licit.domain.licitacion.models import Licitacion, Lote
from licit.domain.terceros.models import OrganismoLicitacion
from licit.domain.licitacion.events import (
    LoteDesmarcadoParaPresentar, 
    LoteMarcadoParaPresentar,
    LicitacionAnulada,
    DomainEvent,
)
from licit.application.services.event_dispatcher import EventDispatcher

def test_dispatch_solo_llama_ultimo_event_de_cada_key():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
        
    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
        lotes=[lote1],
    )
    
    licit.set_presentable(1, True)
    licit.set_presentable(1, False)
    
    events = licit.pull_events()
    handler = Mock()
    handler1 = Mock()
    
    handlers = {
        LoteMarcadoParaPresentar: handler,
        LoteDesmarcadoParaPresentar: handler1,
    }    
    dispatcher = EventDispatcher(handlers)
    
    dispatcher.dispatch(events)
    
    handler1.assert_called_once_with(events[1])
    handler.assert_not_called()
    
def test_dispatch_respeta_el_orden_coalesce_de_los_events_en_la_ejecucion():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
        
    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
        lotes=[lote1],
    )
    
    licit.set_presentable(1, True)
    licit.anular('suspendida', date(2026, 3, 1))
    
    events = licit.pull_events()
    
    manager = Mock()
    handler = manager.lote_handler
    handler1 = manager.anulacion_handler
    
    handlers = {
        LoteMarcadoParaPresentar: handler,
        LicitacionAnulada: handler1,
    }    
    dispatcher = EventDispatcher(handlers)    
    dispatcher.dispatch(events)
    
    expected_calls = [
        call.lote_handler(events[0]),
        call.anulacion_handler(events[1]),
    ]
    
    manager.assert_has_calls(expected_calls, any_order=False)
    
def test_dispatch_da_error_si_no_existe_handler_para_evento():    
    EventoPrueba = DomainEvent
    events = [EventoPrueba()]
    
    handler = Mock()
    
    handlers = {LicitacionAnulada: handler}
    
    dispatcher = EventDispatcher(handlers)
    
    with pytest.raises(KeyError):
        dispatcher.dispatch(events)
    
    
    

    
    