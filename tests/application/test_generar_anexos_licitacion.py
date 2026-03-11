from uuid import uuid4
import pytest
from datetime import datetime
from pathlib import Path

from licit.application.ports.template_repository import TemplateRepository
from licit.application.ports.repositories import LicitacionRepository  
from licit.application.anexos.generar_anexos_licitacion import GenerarAnexosLicitacion
from licit.domain.licitacion.models import Licitacion, EmpresaEnLicitacion, RolEmpresa, Lote
from licit.domain.terceros.models import OrganismoLicitacion
from licit.domain.anexos.models import FasesLicitacion, ModoFirmaAnexo
from licit.application.anexos.models import AnexoTemplate

@pytest.fixture
def licitacion_factory():
    def _crear(lotes=None):
        organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
        
        return Licitacion(
            id_org_licit=organismo_licit.id,
            num_exped='26/1',
            titulo='Licitación 1',
            descripcion='Transporte Escolar',
            fecha_tope_present=datetime(2026, 3, 15, 23, 59),
            duracion_contrato=24,
            prorroga=0,
            lotes = lotes if lotes is not None else [Lote(1, 0, 'Lote 1', descripcion='Lote por defecto', a_presentar=False)],
        )
    return _crear

@pytest.fixture
def empresa_factory():
    def _crear(rol=None):
        return EmpresaEnLicitacion(
            empresa_id=uuid4(),
            representacion_id=uuid4(),
            rol=rol if rol is not None else RolEmpresa.INDIVIDUAL
        )
    return _crear


def test_generar_anexos_licitacion_modo_individual_empresa_con_dos_empresas_devuelve_dos_anexos(licitacion_factory, empresa_factory):    
    empresa1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    licitacion = licitacion_factory()
    
    licitacion.agregar_empresa(empresa1)
    licitacion.agregar_empresa(empresa2)

    template = AnexoTemplate(codigo='ANEXO1', fase=FasesLicitacion.OFERTA, modo_firma=ModoFirmaAnexo.INDIVIDUAL_EMPRESA, template_path=Path('anexos/Anexo1.docx'))
    
    class FakeLicitacionRepository(LicitacionRepository):
        def get(self, licitacion_id):
            return licitacion
        def save(self, licitacion):
            pass
    
    class FakeTemplateRepository(TemplateRepository):
        def list_by_fase(self, licitacion_id, fase):
            return [template]
    
    # Ejecutamos el caso de uso
    generar_anexos = GenerarAnexosLicitacion(FakeLicitacionRepository(), FakeTemplateRepository())
    anexos_preparados = generar_anexos.execute(licitacion_id=licitacion.id, fase=FasesLicitacion.OFERTA)
    
    # Verificamos el resultado
    assert len(anexos_preparados) == 2
    assert anexos_preparados[0].codigo == 'ANEXO1'
    assert anexos_preparados[0].firmas[0].empresa_id == empresa1.empresa_id
    assert anexos_preparados[0].firmas[0].representacion_id == empresa1.representacion_id
    assert anexos_preparados[1].codigo == 'ANEXO1'
    assert anexos_preparados[1].firmas[0].empresa_id == empresa2.empresa_id
    assert anexos_preparados[1].firmas[0].representacion_id == empresa2.representacion_id
    assert anexos_preparados[0].codigo == template.codigo
    
    
def test_generar_anexos_licitacion_modo_conjunto_empresas_con_dos_empresas_devuelve_un_anexo_con_las_dos_empresas(licitacion_factory, empresa_factory):
    empresa1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    licitacion = licitacion_factory()
    
    licitacion.agregar_empresa(empresa1)
    licitacion.agregar_empresa(empresa2)

    template = AnexoTemplate(codigo='ANEXO1', fase=FasesLicitacion.OFERTA, modo_firma=ModoFirmaAnexo.CONJUNTO_EMPRESAS, template_path=Path('anexos/Anexo1.docx'))
    
    class FakeLicitacionRepository(LicitacionRepository):
        def get(self, licitacion_id):
            return licitacion
        def save(self, licitacion):
            pass
    
    class FakeTemplateRepository(TemplateRepository):
        def list_by_fase(self, licitacion_id, fase):
            return [template]
    
    # Ejecutamos el caso de uso
    generar_anexos = GenerarAnexosLicitacion(FakeLicitacionRepository(), FakeTemplateRepository())
    anexos_preparados = generar_anexos.execute(licitacion_id=licitacion.id, fase=FasesLicitacion.OFERTA)
    
    # Verificamos el resultado
    assert len(anexos_preparados) == 1
    assert anexos_preparados[0].codigo == 'ANEXO1'
    assert len(anexos_preparados[0].firmas) == 2
    assert anexos_preparados[0].firmas[0].empresa_id == empresa1.empresa_id
    assert anexos_preparados[0].firmas[0].representacion_id == empresa1.representacion_id
    assert anexos_preparados[0].firmas[1].empresa_id == empresa2.empresa_id
    assert anexos_preparados[0].firmas[1].representacion_id == empresa2.representacion_id
    assert anexos_preparados[0].codigo == template.codigo
    
def test_generar_anexos_licitacion_modo_ute_constituida_devuelve_solo_un_anexo_con_firma_ute(licitacion_factory, empresa_factory):
    empresa1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    licitacion = licitacion_factory()
    
    licitacion.agregar_empresa(empresa1)
    licitacion.agregar_empresa(empresa2)

    template = AnexoTemplate(codigo='ANEXO1', fase=FasesLicitacion.OFERTA, modo_firma=ModoFirmaAnexo.UTE_CONSTITUIDA, template_path=Path('anexos/Anexo1.docx'))
    
    class FakeLicitacionRepository(LicitacionRepository):
        def get(self, licitacion_id):
            return licitacion
        def save(self, licitacion):
            pass
    
    class FakeTemplateRepository(TemplateRepository):
        def list_by_fase(self, licitacion_id, fase):
            return [template]
    
    # Ejecutamos el caso de uso
    generar_anexos = GenerarAnexosLicitacion(FakeLicitacionRepository(), FakeTemplateRepository())
    anexos_preparados = generar_anexos.execute(licitacion_id=licitacion.id, fase=FasesLicitacion.OFERTA)
    
    # Verificamos el resultado
    assert len(anexos_preparados) == 1
    assert anexos_preparados[0].codigo == 'ANEXO1'
    assert len(anexos_preparados[0].firmas) == 1
    assert anexos_preparados[0].firmas[0].empresa_id == empresa2.empresa_id
    assert anexos_preparados[0].firmas[0].representacion_id == empresa2.representacion_id
    assert anexos_preparados[0].codigo == template.codigo
    
def test_generar_anexos_licitacion_sin_empresas_firmantes_devuelve_lista_vacia(licitacion_factory):
    licitacion = licitacion_factory()

    template = AnexoTemplate(codigo='ANEXO1', fase=FasesLicitacion.OFERTA, modo_firma=ModoFirmaAnexo.INDIVIDUAL_EMPRESA, template_path=Path('anexos/Anexo1.docx'))
    
    class FakeLicitacionRepository(LicitacionRepository):
        def get(self, licitacion_id):
            return licitacion
        def save(self, licitacion):
            pass
    
    class FakeTemplateRepository(TemplateRepository):
        def list_by_fase(self, licitacion_id, fase):
            return [template]
    
    # Ejecutamos el caso de uso
    generar_anexos = GenerarAnexosLicitacion(FakeLicitacionRepository(), FakeTemplateRepository())
    anexos_preparados = generar_anexos.execute(licitacion_id=licitacion.id, fase=FasesLicitacion.OFERTA)
    
    # Verificamos el resultado
    assert len(anexos_preparados) == 0