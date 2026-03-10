from uuid import UUID

from licit.domain.licitacion.models import EmpresaEnLicitacion, RolEmpresa
from licit.application.ports.repositories import LicitacionRepository, RepresentacionRepository

class AgregarEmpresaALicitacion:
    def __init__(self, licitacion_repo: LicitacionRepository, representacion_repo: RepresentacionRepository):
        self.licitacion_repo = licitacion_repo
        self.representacion_repo = representacion_repo
        
    def execute(
        self, 
        licitacion_id: UUID, 
        empresa_id: UUID, 
        representacion_id: UUID, 
        rol: RolEmpresa
        ) -> None:
        licitacion = self.licitacion_repo.get(licitacion_id)
        
        representacion = self.representacion_repo.get(representacion_id)
        
        if representacion.empresa_id != empresa_id:
            raise ValueError('La representación no corresponde a la empresa indicada')
        
        empresa_en_licitacion = EmpresaEnLicitacion(
            empresa_id=empresa_id,
            representacion_id=representacion.id,
            rol=rol
        )
        
        licitacion.agregar_empresa(empresa_en_licitacion)
        
        self.licitacion_repo.save(licitacion)

