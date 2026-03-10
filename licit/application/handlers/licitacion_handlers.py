
from licit.domain.licitacion.events import LicitacionAnulada, LicitacionReactivada

def handle_licitacion_anulada(event: LicitacionAnulada): ...
    

def handle_licitacion_reactivada(event: LicitacionReactivada): ...