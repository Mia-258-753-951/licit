
from licit.domain.licitacion.events import LoteMarcadoParaPresentar, LoteDesmarcadoParaPresentar
    

def handle_lote_marcado(event: LoteMarcadoParaPresentar): ...
    

def handle_lote_desmarcado(event: LoteDesmarcadoParaPresentar):...
