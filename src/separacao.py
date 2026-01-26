import os
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def separar_lote_xml(caminho_arquivo):
    """
    Realiza o parsing de um XML de lote e separa em arquivos individuais por atendimento.
    """
    if not caminho_arquivo or not os.path.exists(caminho_arquivo):
        logger.error(f"Arquivo não encontrado para separação: {caminho_arquivo}")
        return

    try:
        # Carrega o XML mantendo o encoding original do laboratório
        tree = ET.parse(caminho_arquivo)
        root = tree.getroot()

        # Extrai metadados do cabeçalho para replicar nos novos arquivos
        numero_lote = root.findtext('NumeroLote')
        codigo_apoiado = root.findtext('CodigoApoiado')
        
        # Localiza a lista de resultados
        lista_resultados = root.find('ListaResultados')
        if lista_resultados is None:
            logger.warning("Nenhum resultado encontrado no XML para separação.")
            return

        sysdate = datetime.now().strftime("%Y%m%d%H%M%S")
        count = 0

        # Itera sobre cada registro de atendimento
        for resultado in lista_resultados.findall('ct_Resultado_v1'):
            atendimento = resultado.findtext('NumeroAtendimentoApoiado')
            
            if not atendimento:
                continue

            # Reconstrói a estrutura XML exigida
            novo_root = ET.Element('ct_LoteResultados_v1')
            ET.SubElement(novo_root, 'NumeroLote').text = numero_lote
            ET.SubElement(novo_root, 'CodigoApoiado').text = codigo_apoiado
            nova_lista = ET.SubElement(novo_root, 'ListaResultados')
            
            # Insere o bloco de dados do paciente/atendimento
            nova_lista.append(resultado)

            # Define o nome do arquivo: Atendimento + Sysdate
            nome_saida = f"{atendimento}_{sysdate}.xml"
            caminho_saida = os.path.join(os.path.dirname(caminho_arquivo), nome_saida)
            
            # Grava o arquivo com o cabeçalho ISO-8859-1
            nova_tree = ET.ElementTree(novo_root)
            with open(caminho_saida, "wb") as f:
                f.write(b'<?xml version="1.0" encoding="iso-8859-1"?>\n')
                nova_tree.write(f, encoding="iso-8859-1", xml_declaration=False)
            
            count += 1
            logger.info(f"Gerado: {nome_saida}")

        logger.info(f"Sucesso: {count} arquivos individuais criados.")

    except Exception as e:
        logger.error(f"Falha crítica na separação do XML: {e}")