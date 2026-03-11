from datetime import datetime, date
from pathlib import Path
from uuid import uuid4
import pytest

from licit.domain.anexos.models import FasesLicitacion
from licit.domain.licitacion.models import Licitacion, Lote, EmpresaEnLicitacion, RolEmpresa
from licit.domain.anexos.models import ModoFirmaAnexo, FirmaEmpresa
from licit.application.anexos.models import AnexoTemplate
from licit.domain.terceros.models import OrganismoLicitacion
from licit.domain.licitacion.events import LoteDesmarcadoParaPresentar, LoteMarcadoParaPresentar

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


def test_crear_licitacion_sin_lotes_genera_lote_1(licitacion_factory):    
    licit = licitacion_factory()
    
    assert len(licit.lotes) == 1
    assert licit.lotes[0].num_lote == 1
    assert not licit.lotes[0].a_presentar
    
def test_licitacion_importe_a_presentar_suma_solo_lotes_presentables_e_importe_licit_suma_total(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
    
    lote2 = Lote(2, 200000, 'Título2', descripcion='descripción2', a_presentar=True)
    
    lote3 = Lote(3, 100000, 'Título3', descripcion='descripción3', a_presentar=True)
    
    licit = licitacion_factory(lotes=[lote1, lote2, lote3])
    
    assert licit.importe_licit == 600000
    assert licit.importe_a_presentar == 300000
    
def test_add_lote_con_num_duplicado_lanza_error(licitacion_factory):    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)    
    lote2 = Lote(1, 200000, 'Título2', descripcion='descripción2', a_presentar=True)
    
    licit = licitacion_factory(lotes=[lote1])
    
    with pytest.raises(KeyError):
        licit.add_lote(lote2)
        
def test_set_presentable_cambia_estado_lote(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)

    licit = licitacion_factory(lotes=[lote1])
    licit.set_presentable(1, True)
    
    assert licit.lotes[0].a_presentar
    
def test_set_presentable_da_error_si_no_existe_lote(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)

    licit = licitacion_factory(lotes=[lote1])
    
    with pytest.raises(KeyError):    
        licit.set_presentable(2, True)
    
def test_licitacion_anulada_no_permite_set_presentable_ni_add_lote(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)    
    lote2 = Lote(1, 200000, 'Título2', descripcion='descripción2', a_presentar=True)

    licit = licitacion_factory(lotes=[lote1])
    licit.anular('Recurso a TARCJA', date(2026, 3, 4))
    
    with pytest.raises(ValueError):    
        licit.set_presentable(1, True)
    
    with pytest.raises(ValueError):    
        licit.add_lote(lote2)

def test_anular_y_reactivar_cambian_estado_y_realizan_comentario(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
        
    licit = licitacion_factory(lotes=[lote1])    
    licit.anular('Recurso a TARCJA', date(2026, 3, 4))
    
    assert licit.anulado
    assert licit.comentarios is not None
    
    licit.reactivar('Denegado recurso', date(2026, 3, 15))
    
    assert not licit.anulado
    assert 'reactivación' in licit.comentarios
    
def test_set_presentable_false_a_true_añade_evento_lote_marcado(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.set_presentable(1, True)
    events = licit.pull_events()
    
    assert len(events) == 1
    assert isinstance(events[0], LoteMarcadoParaPresentar)
    
def test_set_presentable_true_a_false_añade_evento_lote_desmarcado(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
        
    licit = licitacion_factory(lotes=[lote1])

    licit.set_presentable(1, False)
    events = licit.pull_events()

    assert len(events) == 1
    assert isinstance(events[0], LoteDesmarcadoParaPresentar)
    
def test_pull_events_devuelve_lista_de_eventos_y_vacia_original(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
        
    licit = licitacion_factory(lotes=[lote1])
        
    licit.set_presentable(1, True)
    events = licit.pull_events()
    
    assert len(events) == 1
    assert not licit._domain_events
    
def test_agregar_empresa_duplicada_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)

    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    
    with pytest.raises(KeyError):
        licit.agregar_empresa(empresa_en_licitacion1)

def test_agregar_empresa_agrega_empresa_en_licitacion_con_rol_correcto(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    
    assert licit.empresas_en_licitacion[0] == empresa_en_licitacion1
    assert licit.empresas_en_licitacion[0].rol == RolEmpresa.INDIVIDUAL
            
def test_quitar_empresa_quita_empresa_en_licitacion(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
        
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    
    assert licit.empresas_en_licitacion[0] == empresa_en_licitacion1
    
    licit.quitar_empresa(empresa_en_licitacion1.empresa_id)
    
    assert licit.empresas_en_licitacion == []

def test_quitar_empresa_ute_miembro_con_ute_constituida_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)    
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    
    with pytest.raises(ValueError):
        licit.quitar_empresa(empresa_en_licitacion1.empresa_id)

def test_agregar_empresa_ute_constituida_sin_miembros_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
        
    licit = licitacion_factory(lotes=[lote1])
        
    with pytest.raises(ValueError):
        licit.agregar_empresa(empresa_en_licitacion2)

def test_agregar_empresa_ute_miembro_con_ute_constituida_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    empresa_en_licitacion3 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
        
    with pytest.raises(ValueError):
        licit.agregar_empresa(empresa_en_licitacion3)


def test_agregar_empresa_ute_constituida_si_ya_hay_ute_constituida_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    empresa_en_licitacion3 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion3)
    licit.agregar_empresa(empresa_en_licitacion1)
        
    with pytest.raises(ValueError):
        licit.agregar_empresa(empresa_en_licitacion2)

def test_agregar_empresa_individual_si_hay_ute_miembro_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
        
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 =empresa_factory(rol=RolEmpresa.INDIVIDUAL)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
            
    with pytest.raises(ValueError):
        licit.agregar_empresa(empresa_en_licitacion2)

def test_agregar_empresa_miembro_ute_si_hay_empresa_individual_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
            
    with pytest.raises(ValueError):
        licit.agregar_empresa(empresa_en_licitacion2)
    

def test_agregar_o_quitar_empresa_a_licitacion_anulada_lanza_error(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    
    licit = licitacion_factory(lotes=[lote1])
    
    licit.anular('Recurso a TARCJA', date(2026, 3, 4))
    
    with pytest.raises(ValueError):
        licit.agregar_empresa(empresa_en_licitacion1)
        
    licit.reactivar('Denegado recurso', date(2026, 3, 15))
    licit.agregar_empresa(empresa_en_licitacion1)
    
    licit.anular('Recurso a TARCJA', date(2026, 3, 4))
    
    with pytest.raises(ValueError):
        licit.quitar_empresa(empresa_en_licitacion1.empresa_id)

def test_obtener_empresas_firmantes_segun_modo_firma_anexo(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion3 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    licit.agregar_empresa(empresa_en_licitacion3)
    
    anexo = AnexoTemplate(
        codigo='AnexoI',
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.CONJUNTO_EMPRESAS,
        template_path=Path('anexos/AnexoI.docx')
    )
    empresas_firmantes = licit.obtener_empresas_firmantes(anexo.modo_firma)
    
    assert len(empresas_firmantes) == 2
    assert empresa_en_licitacion1 in empresas_firmantes
    assert empresa_en_licitacion2 in empresas_firmantes
    assert empresa_en_licitacion3 not in empresas_firmantes

def test_obtener_ute_constituida_devuelve_empresa_ute_si_hay_none_si_no(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion3 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    licit.agregar_empresa(empresa_en_licitacion3)
    
    empresa_ute = licit.obtener_ute_constituida()
    
    assert empresa_ute == empresa_en_licitacion3
    
    licit.quitar_empresa(empresa_en_licitacion3.empresa_id)
    
    assert licit.obtener_ute_constituida() is None

def test_obtener_miembros_ute_devuelve_lista_de_miembros_si_hay_lista_vacia_si_no(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)    
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion3 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
        
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    licit.agregar_empresa(empresa_en_licitacion3)
    
    assert licit.obtener_miembros_ute() == [empresa_en_licitacion1, empresa_en_licitacion2]
    
    licit.quitar_empresa(empresa_en_licitacion3.empresa_id)
    licit.quitar_empresa(empresa_en_licitacion1.empresa_id)
    licit.quitar_empresa(empresa_en_licitacion2.empresa_id)
    
    assert licit.obtener_miembros_ute() == []

def test_obtener_empresas_firmantes_devuelve_ute_si_hay_ute_constituida_y_lanza_error_si_no_hay_ute(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)    
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    
    licit = licitacion_factory(lotes=[lote1])
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    
    anexo = AnexoTemplate(
        codigo='AnexoI',
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.UTE_CONSTITUIDA,
        template_path=Path('anexos/AnexoI.docx')
    )
    
    assert licit.obtener_empresas_firmantes(anexo.modo_firma) == [empresa_en_licitacion2]
    
    licit.quitar_empresa(empresa_en_licitacion2.empresa_id)
    
    with pytest.raises(ValueError):
        licit.obtener_empresas_firmantes(anexo)

def test_obtener_empresas_firmantes_devuelve_lista_vacía_si_no_hay_empresas_firmantes_para_anexo(licitacion_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    licit = licitacion_factory(lotes=[lote1])
    
    anexo = AnexoTemplate(
        codigo='AnexoI',
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.CONJUNTO_EMPRESAS,
        template_path=Path('anexos/AnexoI.docx')
    )
    assert licit.obtener_empresas_firmantes(anexo.modo_firma) == []
    
def test_obtener_empresas_firmantes_con_modo_firma_individual_devuelve_todas_las_empresas_menos_ute_constituida(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    lote2 = Lote(2, 200000, 'Título2', descripcion='descripción2', a_presentar=True)
    
    licit = licitacion_factory(lotes=[lote1])
    licit1 = licitacion_factory(lotes=[lote2])

    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion3 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    empresa_en_licitacion4 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    empresa_en_licitacion5 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
        
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    licit.agregar_empresa(empresa_en_licitacion3)
    
    anexo = AnexoTemplate(
        codigo='AnexoI',
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.INDIVIDUAL_EMPRESA,
        template_path=Path('anexos/AnexoI.docx')
    )
    
    assert licit.obtener_empresas_firmantes(anexo.modo_firma) == [empresa_en_licitacion1, empresa_en_licitacion2]
    
    licit1.agregar_empresa(empresa_en_licitacion4)
    licit1.agregar_empresa(empresa_en_licitacion5)
    
    assert licit1.obtener_empresas_firmantes(anexo.modo_firma) == [empresa_en_licitacion4, empresa_en_licitacion5]
    
def test_generar_anexos_devuelve_lista_de_anexos_con_empresas_firmantes_y_representaciones(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    licit = licitacion_factory(lotes=[lote1])
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.UTE_CONSTITUIDA)
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    
    anexo = AnexoTemplate(
        codigo='AnexoI',
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.UTE_CONSTITUIDA,
        template_path=Path('anexos/AnexoI.docx')
    )
    
    anexo_preparado = licit.generar_anexos([anexo])
    
    assert len(anexo_preparado) == 1
    assert len(anexo_preparado[0].firmas) == 1
    assert anexo_preparado[0].codigo == anexo.codigo
    assert anexo_preparado[0].licitacion_id == licit.id
    assert anexo_preparado[0].firmas[0] == FirmaEmpresa(empresa_en_licitacion2.empresa_id, empresa_en_licitacion2.representacion_id)

def test_generar_anexos_devuelve_lista_vacia_si_no_empresas_firmantes(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=True)
    
    licit = licitacion_factory(lotes=[lote1])
    
    empresa_en_licitacion1 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    empresa_en_licitacion2 = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    
    licit.agregar_empresa(empresa_en_licitacion1)
    licit.agregar_empresa(empresa_en_licitacion2)
    
    anexo = AnexoTemplate(
        codigo='AnexoI',
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.CONJUNTO_EMPRESAS,
        template_path=Path('anexos/AnexoI.docx')
    )
    
    anexo_preparado = licit.generar_anexos([anexo])
    
    assert anexo_preparado == []
    
def test_generar_anexos_varios_tipos_anexo(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, "Título1", descripcion="desc", a_presentar=True)
    licit = licitacion_factory(lotes=[lote1])

    empresa = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    licit.agregar_empresa(empresa)

    anexo1 = AnexoTemplate(
        codigo="A1",
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.INDIVIDUAL_EMPRESA,
        template_path=Path('anexos/Anexo1.docx')
    )

    anexo2 = AnexoTemplate(
        codigo="A2",
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.INDIVIDUAL_EMPRESA,
        template_path=Path('anexos/Anexo2.docx')
    )

    anexos = licit.generar_anexos([anexo1, anexo2])

    assert len(anexos) == 2
    assert {a.codigo for a in anexos} == {anexo1.codigo, anexo2.codigo}
    
def test_generar_anexos_varias_empresas_firmantes(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, "Título1", descripcion="desc", a_presentar=True)
    licit = licitacion_factory(lotes=[lote1])

    empresa1 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    empresa2 = empresa_factory(rol=RolEmpresa.UTE_MIEMBRO)
    licit.agregar_empresa(empresa1)
    licit.agregar_empresa(empresa2)

    anexo = AnexoTemplate(
        codigo="A1",
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.CONJUNTO_EMPRESAS,
        template_path=Path('anexos/Anexo1.docx')
    )

    anexos = licit.generar_anexos([anexo])

    assert len(anexos) == 1
    assert len(anexos[0].firmas) == 2
    assert FirmaEmpresa(empresa1.empresa_id, empresa1.representacion_id) in anexos[0].firmas
    assert FirmaEmpresa(empresa2.empresa_id, empresa2.representacion_id) in anexos[0].firmas
    
def test_generar_anexos_conserva_empresa_y_representacion_correcta(licitacion_factory, empresa_factory):
    lote1 = Lote(1, 300000, "Título1", descripcion="desc", a_presentar=True)
    licit = licitacion_factory(lotes=[lote1])

    empresa = empresa_factory(rol=RolEmpresa.INDIVIDUAL)
    licit.agregar_empresa(empresa)

    anexo = AnexoTemplate(
        codigo="A1",
        fase=FasesLicitacion.OFERTA,
        modo_firma=ModoFirmaAnexo.INDIVIDUAL_EMPRESA,
        template_path=Path('anexos/Anexo1.docx')
    )

    anexos = licit.generar_anexos([anexo])

    assert len(anexos) == 1
    assert len(anexos[0].firmas) == 1
    assert anexos[0].firmas[0].empresa_id == empresa.empresa_id
    assert anexos[0].firmas[0].representacion_id == empresa.representacion_id