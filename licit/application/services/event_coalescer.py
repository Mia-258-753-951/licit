
from licit.domain.licitacion.events import DomainEvent

def coalesce(events: list[DomainEvent]) -> list[DomainEvent]:
    """
    Devuelve la lista de eventos con origen en dominio dejando solo el último evento
    para cada 'event.coalesce_key'. Así nos aseguramos ejecutar solo la última "orden"
    recibida, evitando conflictos.
    """
    last_event_by_key = {}
    result = []
    for event in events:
        key = event.coalesce_key
        
        if key is None:    # los eventos sin clave no se coalescean, pasan a la lista directamente
                            # Los guardamos para no perder información ni tapar bugs
            result.append(event)
            continue
        
        last_event_by_key.pop(key, None)
        last_event_by_key[key] = event
        
    result.extend(last_event_by_key.values())
    return result