from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, date
from collections import Counter
from licit.domain.events import DomainEvent, LoteMarcadoParaPresentar, LoteDesmarcadoParaPresentar,LicitacionAnulada,LicitacionReactivada

# TODOS LOS IMPORTES EXPRESADOS EN CÉNTIMOS DE EURO

@dataclass
class OrganismoLicitacion:
    nombre: str
    id: UUID = field(default_factory=uuid4)    

@dataclass
class Licitacion:
    id_org_licit: UUID
    num_exped: str
    titulo: str
    descripcion: str | None
    fecha_tope_present: datetime
    duracion_contrato: int              # en meses
    prorroga: int                       # en meses
    comentarios: str | None = None
    anulado: bool = False
    lotes: list['Lote'] = field(default_factory=list)
    url_licit: str | None = None 
    _domain_events: list[DomainEvent] = field(init=False, default_factory=list)
    id: UUID = field(default_factory=uuid4)
    
    @property
    def importe_licit(self) -> int:
        """En céntimos de euro"""
        return sum(l.importe_lote for l in self.lotes)
    
    @property
    def importe_a_presentar(self) -> int:
        """En céntimos de euro"""
        return sum(l.importe_lote for l in self.lotes if l.a_presentar)
    
    @property
    def a_presentar(self) -> bool:
        return any(l.a_presentar for l in self.lotes)
    
    @property
    def num_lotes(self) -> int:
        return len(self.lotes)
    
    def __post_init__(self) -> None:
        """
        Si creamos licitación sin lotes, se genera automáticamente lote 1 con 
        importe cero y a_presentar False.
        """
        conteo = Counter(l.num_lote for l in self.lotes)
        duplicados = [n for n, c in conteo.items() if c > 1]
        if duplicados:
            raise KeyError(f'Ojo, hay lotes con número repetido: {", ".join(str(d) for d in duplicados)}')        
        if self.num_lotes == 0:
            self.lotes.append(Lote(1, 0, 'único', 'sin división en lotes', False))
        self.descripcion = (self.descripcion or  "").strip() or None
        self.comentarios = (self.comentarios or "").strip() or None
        self.url_licit = (self.url_licit or "").strip() or None
        if self.url_licit and not self.url_licit.startswith(('http://', 'https://')):
            raise ValueError("url must start with 'http://' or 'https://'")
                            
    def add_lote(self, lote: 'Lote') -> None:
        """
        Añade lote a la licitación. Si el lote viene con a_presentar True,
        genera DomainEvent
        """
        if self.anulado:
            raise ValueError("Licitación anulada: no se permite modificar.")
        if  any(l.num_lote == lote.num_lote for l in self.lotes):
            raise KeyError('Ya existe un lote con este número en la licitación.')
        self.lotes.append(lote)
        if lote.a_presentar:
            self._domain_events.append(
                LoteMarcadoParaPresentar( 
                        licit_id=self.id, 
                        lote_num=lote.num_lote)
                    )   
                    
    def set_presentable(self, num_lote: int, valor: bool) -> None:
        """
        Recibe bool que determina si vamos a presentar oferta por el lote o no
        True: Marca lote como a presentar y genera DomainEvent
        False: Marca lote como a no presentar y genera Domain Event
        """
        if self.anulado:
            raise ValueError("Licitación anulada: no se permite modificar.")
        lote = next((l for l in self.lotes if l.num_lote == num_lote), None)
        if lote is None:
            raise KeyError(f'No existe el lote núm. {num_lote}')
        if not lote.a_presentar and valor:
            self._domain_events.append(
                LoteMarcadoParaPresentar(
                        licit_id=self.id, 
                        lote_num=lote.num_lote)
                    )
        if lote.a_presentar and not valor:
            self._domain_events.append(
                LoteDesmarcadoParaPresentar(
                        licit_id=self.id, 
                        lote_num=lote.num_lote)
                    )
        lote.a_presentar = valor        
    
    def anular(self, motivo: str, fecha: date) -> None:
        if self.anulado:
            return
        self.anulado = True
        self._domain_events.append(LicitacionAnulada(licit_id=self.id))
        if self.comentarios:
            self.comentarios += f'\n-> Motivo anulación: {motivo}, fecha anulación: {fecha.isoformat()}'
        else:
            self.comentarios = f'-> Motivo anulación: {motivo}, fecha anulación: {fecha.isoformat()}'
            
    def reactivar(self, motivo: str, fecha: date) -> None:
        if not self.anulado:
            return
        self.anulado = False
        self._domain_events.append(LicitacionReactivada(licit_id=self.id))
        if self.comentarios:
            self.comentarios += f'\n-> Motivo reactivación: {motivo}, fecha reactivación: {fecha.isoformat()}'
        else:
            self.comentarios = f'-> Motivo reactivación: {motivo}, fecha reactivación: {fecha.isoformat()}'
    
    def pull_events(self) -> list[DomainEvent]:
        eventos = self._domain_events.copy()
        self._domain_events.clear()
        return eventos        
    
@dataclass
class Lote:
    num_lote: int
    importe_lote: int
    nombre_lote: str
    descripcion: str | None
    a_presentar: bool
    
    def __post_init__(self) -> None:
        if self.importe_lote < 0:
            raise ValueError('El importe del lote no puede ser negativo.')
        if self.num_lote < 0:
            raise ValueError('El número de lote no puede ser negativo.')
        self.descripcion = (self.descripcion or  "").strip() or None