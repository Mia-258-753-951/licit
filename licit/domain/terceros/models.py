from dataclasses import dataclass, field
from uuid import UUID, uuid4
from enum import Enum
from datetime import date
from collections import Counter

@dataclass
class OrganismoLicitacion:
    nombre: str
    id: UUID = field(default_factory=uuid4)

@dataclass
class Empresa:    
    nombre: str
    cif: str
    direccion: str
    email: str
    telefono: str
    es_ute: bool = False
    id: UUID= field(default_factory=uuid4)

@dataclass
class Apoderado:
    dni: str
    nombre_y_apell: str
    id: UUID= field(default_factory=uuid4)
    
class TipoRepresentacion(str, Enum):
    ADMIN_UNICO = 'Administrador Único'
    ADMIN_SOLIDARIO = 'Administrador Solidario'
    ADMIN_MANCOMUNADO = 'Administrador Mancomunado'
    APOD_SOLIDARIO = 'Apoderado Solidario'
    APOD_MANCOMUNADO = 'Apoderado Mancomunado'
    GERENTE_UTE = 'Gerente de la UTE'

class ModoFirmaRepresentacion(str, Enum):
    INDIVIDUAL = 'individual'
    MANCOMUNADA = 'mancomunada'

@dataclass
class RepresentacionEmpresa:
    "Representa una escritura"
    empresa_id: UUID    
    tipo_apoderamiento: TipoRepresentacion
    modo_firma: ModoFirmaRepresentacion
    min_firmas_requeridas: int
    fecha_escritura: date
    tipo_escritura: str
    notario_escritura: str
    protocolo_escritura: str
    observaciones: str | None = None
    apoderados: list[UUID]=field(default_factory=list)   # lista de id de apoderados en escritura
    id: UUID= field(default_factory=uuid4)
    
    def __post_init__(self) -> None:
        if not self.apoderados:
            raise ValueError('Debe haber al menos un apoderado en la representación')
        conteo = Counter(a for a in self.apoderados)
        duplicados = any(a for a, c in conteo.items() if c > 1)
        if duplicados:
            raise ValueError('No se puede incluir el mismo apoderado más de una vez')
        if self.tipo_apoderamiento == TipoRepresentacion.ADMIN_UNICO and len(self.apoderados) != 1:
            raise ValueError('Si el tipo de apoderamiento es Administrador Único, debe haber exactamente un apoderado.')
        if self.modo_firma == ModoFirmaRepresentacion.INDIVIDUAL and self.min_firmas_requeridas != 1:
            raise ValueError('Si modo de firma es individual, el número de firmas necesario debe ser uno.')
        if self.modo_firma == ModoFirmaRepresentacion.MANCOMUNADA and self.min_firmas_requeridas < 2:
            raise ValueError('Si modo de firma es mancomunado, el número de firmas necesario debe ser dos o más.')        
        if self.min_firmas_requeridas > len(self.apoderados):
            raise ValueError('El número mínimo de firmas no puede ser mayor que el número de apoderados.')
        self.tipo_escritura = self.tipo_escritura.strip()
        if not self.tipo_escritura:
            raise ValueError('El tipo de escritura no puede estar vacío.')  
        self.notario_escritura = self.notario_escritura.strip()
        if not self.notario_escritura:
            raise ValueError('El notario de la escritura no puede estar vacío.')    
        self.protocolo_escritura = self.protocolo_escritura.strip()
        if not self.protocolo_escritura:
            raise ValueError('El protocolo de la escritura no puede estar vacío.')  
        self.observaciones = (self.observaciones or "").strip() or None
            
        
    
    