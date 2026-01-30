import sys
import os
import pytest
from xml_to_rtf import RTFConverter, parse_xml_content

# Adiciona o diretório raiz ao sys.path para importar xml_to_rtf
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_rtf_converter_escape():
    text = "Teste com {chaves} e \\barra"
    escaped = RTFConverter.escape_text(text)
    # \ deve virar \\, { virar \{, } virar \}
    assert "\\\\" in escaped
    assert "\\{" in escaped
    assert "\\}" in escaped

def test_parse_xml_content_db_format(temp_dir, sample_xml_content):
    # Cria um arquivo XML simulando o formato DB
    # Nota: xml_to_rtf espera uma estrutura um pouco diferente da separacao.py (ct_ResultadoProcedimentos_v1)
    # Vamos criar um XML específico para esse teste
    
    xml_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<ct_LoteResultados_v1>
    <ct_Resultado_v1>
        <NumeroAtendimentoDB>12345</NumeroAtendimentoDB>
        <ct_ResultadoProcedimentos_v1>
            <CodigoExameDB>HEMOGRAMA</CodigoExameDB>
            <ct_ResultadoTexto_v1>
                <DescricaoParametrosDB>Hemoglobina</DescricaoParametrosDB>
                <ValorResultado>14.0</ValorResultado>
                <UnidadeMedida>g/dL</UnidadeMedida>
            </ct_ResultadoTexto_v1>
        </ct_ResultadoProcedimentos_v1>
    </ct_Resultado_v1>
</ct_LoteResultados_v1>"""
    
    input_file = temp_dir / "exame.xml"
    with open(input_file, "w", encoding="iso-8859-1") as f:
        f.write(xml_content)
        
    content = parse_xml_content(str(input_file))
    
    assert "Atendimento DB: 12345" in content
    assert "EXAME: HEMOGRAMA" in content
    assert "Hemoglobina: 14.0 g/dL" in content

def test_create_file_rtf(temp_dir):
    output_path = temp_dir / "teste.rtf"
    content = "Conteúdo de Teste"
    success = RTFConverter.create_file(content, str(output_path))
    
    assert success is True
    assert output_path.exists()
    
    with open(output_path, "r", encoding="ascii") as f:
        content_read = f.read()
        assert "Conte\\'fado de Teste" in content_read
        assert r"{\rtf1" in content_read
