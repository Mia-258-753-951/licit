from datetime import datetime, date
import pytest

from licit.domain.licitacion.models import Licitacion, Lote, OrganismoLicitacion


def test_crear_licitacion_sin_lotes_genera_lote_1():
    
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        prorroga=0
    )
    
    assert len(licit.lotes) == 1
    assert licit.lotes[0].num_lote == 1
    assert licit.lotes[0].a_presentar == False
    
def test_licitacion_importe_a_presentar_suma_solo_lotes_presentables_e_importe_licit_suma_total():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
    
    lote2 = Lote(2, 200000, 'Título2', descripcion='descripción2', a_presentar=True)
    
    lote3 = Lote(3, 100000, 'Título3', descripcion='descripción3', a_presentar=True)
    
    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        prorroga=0,
        lotes=[lote1, lote2, lote3],
    )
    
    assert licit.importe_licit == 600000
    assert licit.importe_a_presentar == 300000
    
def test_add_lote_con_num_duplicado_lanza_error():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
    
    lote2 = Lote(1, 200000, 'Título2', descripcion='descripción2', a_presentar=True)
    
    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        prorroga=0,
        lotes=[lote1],
    )
    
    with pytest.raises(KeyError):
        licit.add_lote(lote2)
        
def test_set_presentable_cambia_estado_lote():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)

    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        prorroga=0,
        lotes=[lote1],
    )    
    licit.set_presentable(1, True)
    
    assert licit.lotes[0].a_presentar == True
    
def test_set_presentable_da_error_si_no_existe_lote():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)

    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        prorroga=0,
        lotes=[lote1],
    )
    with pytest.raises(KeyError):    
        licit.set_presentable(2, True)
    
def test_licitacion_anulada_no_permite_set_presentable_ni_add_lote():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
    
    lote2 = Lote(1, 200000, 'Título2', descripcion='descripción2', a_presentar=True)

    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=True,
        prorroga=0,
        lotes=[lote1],
    )
    with pytest.raises(ValueError):    
        licit.set_presentable(1, True)
    
    with pytest.raises(ValueError):    
        licit.add_lote(lote2)

def test_anular_y_reactivar_cambian_estado_y_realizan_comentario():
    organismo_licit = OrganismoLicitacion('Ayuntamiento Almería')
    
    lote1 = Lote(1, 300000, 'Título1', descripcion='descripción1', a_presentar=False)
        
    licit = Licitacion(
        id_org_licit=organismo_licit.id,
        num_exped='26/1',
        titulo='Licitación 1',
        descripcion='Transporte Escolar',
        fecha_tope_present=datetime(2026, 3, 15, 23, 59),
        duracion_contrato=24,
        anulado=False,
        prorroga=0,
        lotes=[lote1],
    )
    
    licit.anular('Recurso a TARCJA', date(2026, 3, 4))
    
    assert licit.anulado == True
    assert licit.comentarios is not None
    
    licit.reactivar('Denegado recurso', date(2026, 3, 15))
    
    assert licit.anulado == False
    assert 'reactivación' in licit.comentarios