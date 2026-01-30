import os
import pytest
from src.separacao import separar_lote_xml
import xml.etree.ElementTree as ET

def test_separar_lote_xml_cria_arquivos(temp_dir, sample_xml_content):
    # Cria o arquivo XML de entrada
    input_file = temp_dir / "lote.xml"
    with open(input_file, "w", encoding="iso-8859-1") as f:
        f.write(sample_xml_content)
    
    # Executa a função
    separar_lote_xml(str(input_file))
    
    # Verifica se os arquivos foram criados
    # O padrão é {atendimento}_{sysdate}.xml. Como sysdate varia, checamos por prefixo.
    files = os.listdir(temp_dir)
    generated_files = [f for f in files if "ATEND01" in f or "ATEND02" in f]
    
    assert len(generated_files) == 2, f"Deveria ter criado 2 arquivos, criou: {generated_files}"
    
    # Verifica conteúdo de um dos arquivos
    file_atend01 = [f for f in generated_files if "ATEND01" in f][0]
    tree = ET.parse(temp_dir / file_atend01)
    root = tree.getroot()
    
    assert root.tag == "ct_LoteResultados_v1"
    assert root.findtext("NumeroLote") == "12345"
    assert root.findtext(".//NumeroAtendimentoApoiado") == "ATEND01"

def test_separar_lote_xml_arquivo_inexistente(caplog):
    separar_lote_xml("arquivo_que_nao_existe.xml")
    assert "Arquivo não encontrado para separação" in caplog.text
