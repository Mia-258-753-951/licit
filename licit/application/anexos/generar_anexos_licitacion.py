from uuid import UUID

from licit.application.ports.template_repository import TemplateRepository
from licit.application.ports.repositories import LicitacionRepository
from licit.domain.anexos.models import AnexoPreparado, FasesLicitacion, FirmaEmpresa, ModoFirmaAnexo

class GenerarAnexosLicitacion:
    
    def __init__(
        self,
        licitacion_repo: LicitacionRepository,
        template_repo: TemplateRepository,
        ):
        self._licitacion_repo = licitacion_repo
        self._template_repo = template_repo
        
    def execute(self, 
                licitacion_id: UUID,
                fase: FasesLicitacion,
                ) -> list[AnexoPreparado]:
        
        # 1. Obtener la licitación
        licitacion = self._licitacion_repo.get(licitacion_id)
        # 2. Obtener las plantillas de anexos para la fase
        templates = self._template_repo.list_by_fase(licitacion.id, fase)
        # 3. Generar los anexos preparados a partir de las plantillas
        anexos = []
        for template in templates:
            empresas = licitacion.obtener_empresas_firmantes(template.modo_firma)            
            if not empresas:
                continue
            if template.modo_firma == ModoFirmaAnexo.INDIVIDUAL_EMPRESA:
                # Si el modo de firma es indivual, hay que generar un anexo por cada empresa firmante(si son miembros de ute)   
                for empresa in empresas:
                    anexo = AnexoPreparado(
                        licitacion_id=licitacion_id,
                        codigo=template.codigo,  
                        firmas= (
                            FirmaEmpresa(
                                empresa_id=empresa.empresa_id,
                                representacion_id=empresa.representacion_id,
                            ),
                        ),
                    )
                    anexos.append(anexo)
            
            else:
                # si el modo de firma es conjunto o ute constituida, se genera un único anexo con todas las empresas firmantes 
                # (miembros de ute o la ute constituida respectivamente)
                anexo = AnexoPreparado(
                    licitacion_id=licitacion_id,
                    codigo=template.codigo,  # ahora el identificador será el código,
                    firmas=tuple(
                        FirmaEmpresa(
                            empresa_id=e.empresa_id,
                            representacion_id=e.representacion_id,
                        )
                        for e in empresas
                    ),
                )
                anexos.append(anexo)
                
        return anexos