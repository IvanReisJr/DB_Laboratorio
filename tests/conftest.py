import pytest
import os
import shutil

@pytest.fixture
def sample_xml_content():
    return """<?xml version="1.0" encoding="ISO-8859-1"?>
<ct_LoteResultados_v1>
    <NumeroLote>12345</NumeroLote>
    <CodigoApoiado>TESTE</CodigoApoiado>
    <ListaResultados>
        <ct_Resultado_v1>
            <NumeroAtendimentoApoiado>ATEND01</NumeroAtendimentoApoiado>
            <DadosPaciente>
                <Nome>Paciente Teste 1</Nome>
            </DadosPaciente>
        </ct_Resultado_v1>
        <ct_Resultado_v1>
            <NumeroAtendimentoApoiado>ATEND02</NumeroAtendimentoApoiado>
            <DadosPaciente>
                <Nome>Paciente Teste 2</Nome>
            </DadosPaciente>
        </ct_Resultado_v1>
    </ListaResultados>
</ct_LoteResultados_v1>"""

@pytest.fixture
def temp_dir(tmp_path):
    """Retorna um diretório temporário para testes de arquivo."""
    d = tmp_path / "xml_test"
    d.mkdir()
    return d
