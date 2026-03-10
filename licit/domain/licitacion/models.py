from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, date
from collections import Counter
from enum import Enum

from licit.domain.licitacion.events import (
    DomainEvent, 
    LoteMarcadoParaPresentar, 
    LoteDesmarcadoParaPresentar,
    LicitacionAnulada,
    LicitacionReactivada,
)
from licit.domain.anexos.models import TipoAnexo, ModoFirmaAnexo

# TODOS LOS IMPORTES EXPRESADOS EN CÉNTIMOS DE EURO


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
        self.nombre_lote = self.nombre_lote.strip()
        if not self.nombre_lote:
            raise ValueError('El nombre del lote no puede estar vacío.')
        
class RolEmpresa(str, Enum):
    INDIVIDUAL = 'individual'
    UTE_MIEMBRO = 'miembro_ute'   # de UTE sin constituir - para primera fase
    UTE_CONSTITUIDA = 'ute_constituida'
    
@dataclass
class EmpresaEnLicitacion:
    empresa_id: UUID
    representacion_id: UUID
    rol: RolEmpresa
    
    def __post_init__(self) -> None:
        if not isinstance(self.empresa_id, UUID):
            raise ValueError('empresa_id debe ser un UUID')
        if not isinstance(self.representacion_id, UUID):
            raise ValueError('representacion_id debe ser un UUID')
        
        
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
    empresas_en_licitacion: list['EmpresaEnLicitacion'] = field(default_factory=list)
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
        conteo_lotes = Counter(l.num_lote for l in self.lotes)
        duplicados_lotes = [n for n, c in conteo_lotes.items() if c > 1]
        if duplicados_lotes:
            raise ValueError(f'Ojo, hay lotes con número repetido: {", ".join(str(d) for d in duplicados_lotes)}')
        conteo_empresas = Counter(e.empresa_id for e in self.empresas_en_licitacion)
        duplicados_empresas = [eid for eid, c in conteo_empresas.items() if c > 1]
        if duplicados_empresas:
            raise ValueError(f'Ojo, hay empresas repetidas en la licitación: {", ".join(str(e) for e in duplicados_empresas)}')       
        if self.num_lotes == 0:
            self.lotes.append(Lote(1, 0, 'único', 'sin división en lotes', False))
        self.descripcion = (self.descripcion or  "").strip() or None
        self.comentarios = (self.comentarios or "").strip() or None
        self.url_licit = (self.url_licit or "").strip() or None
        if self.url_licit and not self.url_licit.startswith(('http://', 'https://')):
            raise ValueError("url must start with 'http://' or 'https://'")
        
    def _get_lote(self, num_lote: int) -> Lote:
        lote = next((l for l in self.lotes if l.num_lote == num_lote), None)
        if lote is None:
            raise KeyError(f'No existe el lote núm. {num_lote}')
        return lote
    
    def _existe_empresa_en_licitacion(self, empresa_id: UUID) -> bool:
        return any(e.empresa_id == empresa_id for e in self.empresas_en_licitacion)
    
    def _hay_ute_constituida(self) -> bool:
        return any(e.rol == RolEmpresa.UTE_CONSTITUIDA for e in self.empresas_en_licitacion)
    
    def _hay_miembros_ute(self) -> bool:
        return any(e.rol == RolEmpresa.UTE_MIEMBRO for e in self.empresas_en_licitacion)
    
    def _hay_empresa_individual(self) -> bool:
        return any(e.rol == RolEmpresa.INDIVIDUAL for e in self.empresas_en_licitacion)
    
    def _validar_alta_empresa_en_licitacion(self, empresa_en_licitacion: EmpresaEnLicitacion) -> None:
        if self.anulado:
            raise ValueError("Licitación anulada: no se permite modificar.")
        if self._existe_empresa_en_licitacion(empresa_en_licitacion.empresa_id):
            raise KeyError('Ya existe esta empresa en la licitación.')
        
                            
    def add_lote(self, lote: Lote) -> None:
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
        lote = self._get_lote(num_lote)
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
            
    def agregar_empresa(self, empresa_en_licitacion: 'EmpresaEnLicitacion') -> None:
        self._validar_alta_empresa_en_licitacion(empresa_en_licitacion)
        
        if empresa_en_licitacion.rol == RolEmpresa.INDIVIDUAL and self._hay_miembros_ute():
            raise ValueError(
                'No se puede agregar una empresa individual si ya hay miembros de UTE en la licitación.'
                )        
        elif empresa_en_licitacion.rol == RolEmpresa.UTE_MIEMBRO:
            if self._hay_empresa_individual():
                raise ValueError(
                    'No se puede agregar miembros de UTE si ya hay empresas individuales en la licitación.'
                    )
            if self._hay_ute_constituida():
                raise ValueError(
                    'No se puede agregar un miembro UTE si ya existe la UTE constituida.'
                    )
        elif empresa_en_licitacion.rol == RolEmpresa.UTE_CONSTITUIDA:
            if not self._hay_miembros_ute():
                raise ValueError(
                    'No se puede agregar una empresa UTE constituida si no hay empresas miembro de UTE en la licitación.'
                    )
            if self._hay_ute_constituida():
                raise ValueError(
                    'Ya hay una UTE constituida en la licitación.'
                    )
        self.empresas_en_licitacion.append(empresa_en_licitacion)
        
    def quitar_empresa(self, empresa_id: UUID) -> None:
        if self.anulado:
            raise ValueError("Licitación anulada: no se permite modificar.")
        empresa = next((e for e in self.empresas_en_licitacion if e.empresa_id == empresa_id), None)
        if empresa is None:
            raise KeyError('No existe esta empresa en la licitación.')
        if empresa.rol == RolEmpresa.UTE_MIEMBRO and any(e.rol == RolEmpresa.UTE_CONSTITUIDA for e in self.empresas_en_licitacion):
            raise ValueError('No se puede quitar una empresa miembro de UTE si ya hay una UTE constituida en la licitación.')
        self.empresas_en_licitacion.remove(empresa)
        
    def obtener_ute_constituida(self) -> EmpresaEnLicitacion | None:
        return next((e for e in self.empresas_en_licitacion if e.rol == RolEmpresa.UTE_CONSTITUIDA), None)
    
    def obtener_miembros_ute(self) -> list[EmpresaEnLicitacion]:
        return [e for e in self.empresas_en_licitacion if e.rol == RolEmpresa.UTE_MIEMBRO]
    
    def obtener_empresas_firmantes(self, tipo_anexo: TipoAnexo) -> list[EmpresaEnLicitacion]:
        """
        Devuelve lista de empresas que deberían firmar un anexo de este tipo, según el modo de firma del anexo.
        * INDIVIDUAL_EMPRESA: Devuelve empresas individuales o miembros de UTE (son aquellos anexos que lo firman las empresas individualmente)
        * CONJUNTO_EMPRESAS: Devuelve solo empresas miembro de UTE (si las hay)
        * UTE_CONSTITUIDA: Devuelve la empresa UTE constituida (si la hay)"""
        
        if tipo_anexo.modo_firma == ModoFirmaAnexo.INDIVIDUAL_EMPRESA:
            return [e for e in self.empresas_en_licitacion if e.rol in (RolEmpresa.INDIVIDUAL, RolEmpresa.UTE_MIEMBRO)]
        elif tipo_anexo.modo_firma == ModoFirmaAnexo.CONJUNTO_EMPRESAS:
            return [e for e in self.empresas_en_licitacion if e.rol == RolEmpresa.UTE_MIEMBRO]
        elif tipo_anexo.modo_firma == ModoFirmaAnexo.UTE_CONSTITUIDA:
            ute = self.obtener_ute_constituida()
            if ute is None:
                raise ValueError('No hay UTE constituida en la licitación, no se pueden obtener empresas firmantes para este modo de firma.')
            return [ute]
        else:
            raise ValueError('Modo de firma del anexo no reconocido.')
    
    
    def pull_events(self) -> list[DomainEvent]:
        eventos = self._domain_events.copy()
        self._domain_events.clear()
        return eventos        
    

    
        