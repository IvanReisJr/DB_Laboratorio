import os
import re
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def clean_text(text):
    """Remove caracteres indesejados e espaços extras."""
    if not text:
        return ""
    # Remove caracteres de controle e espaços duplicados
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def save_exam_txt(exam_element, output_dir):
    """
    Extrai dados limpos de um elemento XML de exame e salva em TXT.
    
    Args:
        exam_element (xml.etree.ElementTree.Element): Elemento 'ct_Resultado_v1' ou similar com dados do atendimento.
        output_dir (str): Diretório onde o arquivo TXT será salvo.
    """
    try:
        # 1. Identificar Chave Única (NumeroAtendimentoApoiado)
        atendimento_node = exam_element.find('.//NumeroAtendimentoApoiado')
        if atendimento_node is None:
             atendimento_node = exam_element.find('.//NumeroAtendimentoDB') # Fallback
        
        atendimento_id = atendimento_node.text if atendimento_node is not None else "SEM_ID"
        
        lines = []
        lines.append(f"ATENDIMENTO: {atendimento_id}")
        lines.append("=" * 40)
        lines.append("")

        # 2. Extração de Resultados
        # Itera sobre ListaResultadoProcedimentos -> ct_ResultadoProcedimentos_v1
        # Nota: O elemento passado (exam_element) já é um 'ct_Resultado_v1' ou container similar
        
        found_exams = False
        
        # Busca recursiva a partir do elemento do exame
        procedures = exam_element.findall('.//ct_ResultadoProcedimentos_v1')
        
        for proc in procedures:
            found_exams = True
            codigo = clean_text(proc.findtext('CodigoExameDB'))
            # Se não tiver CodigoExameDB, tenta CodigoProcedimento
            if not codigo:
                codigo = clean_text(proc.findtext('CodigoProcedimento'))
                
            metodologia = clean_text(proc.findtext('DescricaoMetodologia'))
            
            lines.append(f"EXAME: {codigo}")
            lines.append(f"METODOLOGIA: {metodologia}")
            lines.append("-" * 20)
            
            # Parâmetros
            params = proc.findall('.//ct_ResultadoTexto_v1')
            for param in params:
                desc = clean_text(param.findtext('DescricaoParametrosDB'))
                res = clean_text(param.findtext('ValorResultado'))
                unid = clean_text(param.findtext('UnidadeMedida'))
                ref = clean_text(param.findtext('ValorReferencia'))
                
                lines.append(f"{desc}: {res} {unid}")
                if ref:
                    lines.append(f"Referência: {ref}")
            
            lines.append("")
            lines.append("=" * 40)
            lines.append("")

        if not found_exams:
            logger.warning(f"Nenhum procedimento encontrado para atendimento {atendimento_id} ao gerar TXT.")
            return

        # 3. Salvar Arquivo
        filename = f"{atendimento_id}.txt"
        filepath = os.path.join(output_dir, filename)
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        logger.info(f"Arquivo TXT limpo gerado: {filepath}")

    except Exception as e:
        logger.error(f"Erro ao gerar TXT limpo para atendimento: {e}")
