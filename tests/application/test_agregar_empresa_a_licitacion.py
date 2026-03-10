from uuid import uuid4
from datetime import datetime, date
import pytest

from licit.application.ports.repositories import LicitacionRepository, RepresentacionRepository
from licit.application.licitacion.agregar_empresa_a_licitacion import AgregarEmpresaALicitacion
from licit.domain.terceros.models import RepresentacionEmpresa, TipoRepresentacion, ModoFirmaRepresentacion, Apoderado
from licit.domain.licitacion.models import Licitacion, RolEmpresa

class FakeLicitacionRepository(LicitacionRepository):
    def __init__(self):
        self.licitaciones = {}
        
    def get(self, licitacion_id):
        return self.licitaciones[licitacion_id]
    
    def save(self, licitacion):
        self.licitaciones[licitacion.id] = licitacion

class FakeRepresentacionRepository(RepresentacionRepository):
    def __init__(self):
        self.representaciones = {}
        
    def get(self, representacion_id):
        return self.representaciones[representacion_id]

def test_agregar_empresa_a_licitacion():
    licitacion_repo = FakeLicitacionRepository()
    representacion_repo = FakeRepresentacionRepository()
    
    licit = Licitacion(
        id_org_licit=uuid4(),
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
    )
    licitacion_repo.save(licit)
    
    apoderado = Apoderado(
        dni='12345678A',
        nombre_y_apell='Juan Pérez',
        id=uuid4(),
        )
    
    representacion = RepresentacionEmpresa(
        empresa_id=uuid4(),
        tipo_apoderamiento=TipoRepresentacion.ADMIN_UNICO,
        modo_firma=ModoFirmaRepresentacion.INDIVIDUAL,
        min_firmas_requeridas=1,
        fecha_escritura=date(2024, 1, 1),
        tipo_escritura='escritura',
        notario_escritura='notario',
        protocolo_escritura='protocolo',
        apoderados=[apoderado.id],
        id=uuid4(),
    )
    representacion_repo.representaciones[representacion.id] = representacion
    
    use_case = AgregarEmpresaALicitacion(licitacion_repo, representacion_repo)
    use_case.execute(
        licitacion_id=licit.id,
        empresa_id=representacion.empresa_id,
        representacion_id=representacion.id,
        rol=RolEmpresa.INDIVIDUAL
    )
    
    assert len(licit.empresas_en_licitacion) == 1
    empresa_en_licitacion = licit.empresas_en_licitacion[0]
    assert empresa_en_licitacion.empresa_id == representacion.empresa_id
    assert empresa_en_licitacion.representacion_id == representacion.id
    licit_guardada = licitacion_repo.get(licit.id)
    assert len(licit_guardada.empresas_en_licitacion) == 1
    empresa_en_licitacion_guardada = licit_guardada.empresas_en_licitacion[0]
    assert empresa_en_licitacion_guardada.empresa_id == representacion.empresa_id
    
def test_agregar_empresa_a_licitacion_con_representacion_incorrecta():
    licitacion_repo = FakeLicitacionRepository()
    representacion_repo = FakeRepresentacionRepository()
    
    licit = Licitacion(
        id_org_licit=uuid4(),
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
    )
    licitacion_repo.save(licit)
    
    representacion = RepresentacionEmpresa(
        empresa_id=uuid4(),
        tipo_apoderamiento=TipoRepresentacion.ADMIN_UNICO,
        modo_firma=ModoFirmaRepresentacion.INDIVIDUAL,
        min_firmas_requeridas=1,
        fecha_escritura=date(2024, 1, 1),
        tipo_escritura='escritura',
        notario_escritura='notario',
        protocolo_escritura='protocolo',
        apoderados=[uuid4()],
        id=uuid4(),
    )
    representacion_repo.representaciones[representacion.id] = representacion
    
    use_case = AgregarEmpresaALicitacion(licitacion_repo, representacion_repo)
    
    with pytest.raises(ValueError) as exc:
        use_case.execute(
            licitacion_id=licit.id,
            empresa_id=uuid4(),  # Empresa diferente a la de la representación
            representacion_id=representacion.id,
            rol=RolEmpresa.INDIVIDUAL
        )
    assert str(exc.value) == 'La representación no corresponde a la empresa indicada'