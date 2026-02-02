import os
import xml.etree.ElementTree as ET
from datetime import datetime
import logging

import json
from src.cleaner import save_exam_txt

logger = logging.getLogger(__name__)

HISTORY_FILE = "processed_exams.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_history(history):
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(list(history), f)
    except Exception as e:
        logger.error(f"Erro ao salvar histórico: {e}")

def separar_lote_xml(caminho_arquivo):
    """
    Realiza o parsing de um XML de lote e separa em arquivos individuais por atendimento.
    Evita reprocessar atendimentos já salvos no histórico.
    """
    if not caminho_arquivo or not os.path.exists(caminho_arquivo):
        logger.error(f"Arquivo não encontrado para separação: {caminho_arquivo}")
        return

    try:
        # Carrega histórico de duplicatas
        processed_ids = load_history()
        logger.info(f"Histórico carregado com {len(processed_ids)} atendimentos processados.")

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
        new_items = False

        # Itera sobre cada registro de atendimento
        for resultado in lista_resultados.findall('ct_Resultado_v1'):
            atendimento = resultado.findtext('NumeroAtendimentoApoiado')
            
            if not atendimento:
                continue

            # Verificação de Duplicidade
            if atendimento in processed_ids:
                logger.info(f"Ignorando duplicado: {atendimento}")
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
            
            # Atualiza memória e flag
            processed_ids.add(atendimento)
            count += 1
            new_items = True
            logger.info(f"Gerado: {nome_saida}")
            
            # Geração do Arquivo TXT Limpo (Backup Anual)
            try:
                current_year = datetime.now().strftime('%Y')
                clean_dir = os.path.join(os.getcwd(), current_year)
                save_exam_txt(resultado, clean_dir)
            except Exception as clean_err:
                logger.error(f"Erro ao gerar TXT limpo para {atendimento}: {clean_err}")

        if new_items:
            save_history(processed_ids)
            logger.info("Histórico atualizado.")

        logger.info(f"Sucesso: {count} novos arquivos individuais criados.")

    except Exception as e:
        logger.error(f"Falha crítica na separação do XML: {e}")