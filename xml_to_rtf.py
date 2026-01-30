import os
import sys
import glob
import argparse
import logging
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class RTFConverter:
    """
    Classe responsável por converter texto puro em formato RTF básico.
    """
    
    # Cabeçalho padrão RTF (Windows-1252, Arial)
    RTF_HEADER = (
        r"{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1046"
        r"{\fonttbl{\f0\fnil\fcharset0 Arial;}}"
        r"{\*\generator XMLToRTFConverter 1.0;}"
        r"\viewkind4\uc1\pard\sa200\sl276\slmult1\f0\fs22\lang22 "
    )
    
    RTF_FOOTER = r"\par}"

    @staticmethod
    def escape_text(text):
        """
        Escapa caracteres especiais do RTF e converte quebras de linha.
        """
        if not text:
            return ""
        
        # 1. Escapar caracteres reservados do RTF: \, {, }
        # Nota: A ordem importa. Backslash primeiro.
        text = text.replace('\\', '\\\\')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        
        # 2. Converter quebras de linha para \par (parágrafo) ou \line (quebra de linha simples)
        # Normalizando quebras de linha
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\n', r'\par ' + '\n')
        
        # 3. Tratamento de caracteres não-ASCII para RTF
        # Para garantir compatibilidade total (ASCII-7), convertemos caracteres fora do range ASCII
        # para a notação hex do RTF (\'hh).
        final_text = []
        for char in text:
            code = ord(char)
            if code < 128:
                final_text.append(char)
            else:
                # Tenta codificar em CP1252 (padrão do RTF \ansi)
                try:
                    # Codifica o caractere para obter o byte correspondente em CP1252
                    byte_val = char.encode('cp1252')[0]
                    final_text.append(f"\\'{byte_val:02x}")
                except UnicodeEncodeError:
                    # Fallback para caracteres que não existem em CP1252 (ex: emojis, caracteres complexos)
                    # Usa a notação Unicode do RTF: \uN?
                    # N é o valor decimal signed de 16-bit (short)
                    # O '?' é o caractere de substituição para leitores antigos
                    if code > 32767:
                        code = code - 65536
                    final_text.append(f"\\u{code}?")
        
        return "".join(final_text)

    @classmethod
    def create_file(cls, content, output_path):
        """
        Gera o arquivo RTF final.
        """
        try:
            # Monta o corpo do RTF
            # O escape_text agora garante que tudo seja ASCII seguro
            full_rtf = f"{cls.RTF_HEADER}{cls.escape_text(content)}{cls.RTF_FOOTER}"
            
            # Escreve o arquivo usando encoding ASCII (já que escapamos tudo)
            with open(output_path, 'w', encoding='ascii', errors='replace') as f:
                f.write(full_rtf)
            
            logger.info(f"Arquivo RTF criado com sucesso: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever arquivo RTF: {e}")
            return False

def find_latest_xml(directory="."):
    """
    Busca o arquivo .xml mais recente no diretório especificado.
    """
    # Garante que o diretório existe
    if not os.path.isdir(directory):
        logger.error(f"Diretório de busca não encontrado: {directory}")
        return None

    search_pattern = os.path.join(directory, "*.xml")
    files = glob.glob(search_pattern)
    
    if not files:
        return None
    
    # Retorna o arquivo com maior timestamp de modificação
    latest_file = max(files, key=os.path.getmtime)
    logger.info(f"Arquivo XML mais recente encontrado em '{directory}': {latest_file}")
    return latest_file

def parse_db_diagnosticos_format(root):
    """
    Tenta extrair dados do formato DB Diagnósticos (ct_LoteResultados_v1).
    Retorna uma string formatada ou None.
    """
    # Verifica se estamos na estrutura correta
    if root.tag != 'ct_LoteResultados_v1' and root.find('.//ct_LoteResultados_v1') is None:
        # Tenta achar tags características mesmo se a raiz for diferente
        if root.find('.//ListaResultadoProcedimentos') is None:
            return None

    logger.info("Detectado formato DB Diagnósticos / ct_LoteResultados_v1")
    
    full_text = []
    
    # Itera sobre os resultados
    # Pode haver múltiplos ct_Resultado_v1
    resultados = root.findall('.//ct_Resultado_v1')
    
    for res in resultados:
        # Dados do paciente/atendimento (opcional, mas bom ter no cabeçalho)
        atendimento = res.findtext('NumeroAtendimentoDB') or ""
        if atendimento:
            full_text.append(f"Atendimento DB: {atendimento}")
            full_text.append("-" * 40)
            full_text.append("")

        procedimentos = res.findall('.//ct_ResultadoProcedimentos_v1')
        
        for proc in procedimentos:
            exame = proc.findtext('CodigoExameDB') or "Exame"
            metodologia = proc.findtext('DescricaoMetodologia')
            
            full_text.append(f"EXAME: {exame}")
            if metodologia:
                full_text.append(f"Metodologia: {metodologia}")
            full_text.append("")
            
            # Processa ListaResultadoTexto (Parâmetros)
            params = proc.findall('.//ct_ResultadoTexto_v1')
            for param in params:
                descricao = param.findtext('DescricaoParametrosDB') or ""
                valor = param.findtext('ValorResultado') or ""
                unidade = param.findtext('UnidadeMedida') or ""
                referencia = param.findtext('ValorReferencia') or ""
                
                # Formatação: Descrição ........ Valor Unidade
                line = f"{descricao}: {valor} {unidade}".strip()
                full_text.append(line)
                
                if referencia:
                    full_text.append("Valor de Referência:")
                    full_text.append(referencia)
                
                full_text.append("")
            
            # Observações do procedimento
            obs_list = []
            for i in range(1, 6):
                obs = proc.findtext(f'Observacao{i}')
                if obs:
                    obs_list.append(obs)
            
            if obs_list:
                full_text.append("Observações:")
                full_text.extend(obs_list)
                full_text.append("")
                
            liberador = proc.findtext('NomeLiberadorClinico')
            data_lib = proc.findtext('DataHoraLiberacaoClinica')
            if liberador:
                full_text.append(f"Liberado por: {liberador} em {data_lib}")
            
            full_text.append("=" * 40)
            full_text.append("")

    if not full_text:
        return None
        
    return "\n".join(full_text)

def parse_xml_content(xml_path):
    """
    Analisa o XML e busca pelo conteúdo do resultado.
    Suporta formato simples (Conteudo/TextoResultado) e formato estruturado DB.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 1. Tenta formato DB Diagnósticos (Estruturado)
        db_content = parse_db_diagnosticos_format(root)
        if db_content:
            return db_content

        # 2. Formato Simples (Fallback)
        target_tags = ['Conteudo', 'TextoResultado', 'Laudo']
        
        # Procura por ListaResultados
        lista_resultados = root.find('.//ListaResultados')
        
        content_element = None
        
        if lista_resultados is not None:
            for tag in target_tags:
                content_element = lista_resultados.find(tag)
                if content_element is not None:
                    logger.info(f"Conteúdo encontrado na tag: ListaResultados/{tag}")
                    break
        
        # Fallback: Se não achou dentro da lista, procura em todo o documento
        if content_element is None:
            logger.warning("Tag não encontrada dentro de ListaResultados. Tentando busca global...")
            for tag in target_tags:
                content_element = root.find(f'.//{tag}')
                if content_element is not None:
                    logger.info(f"Conteúdo encontrado na busca global na tag: {tag}")
                    break
        
        if content_element is not None and content_element.text:
            return content_element.text
        else:
            logger.error("Nenhum conteúdo de texto encontrado nas tags esperadas (Simples ou DB).")
            return None

    except ET.ParseError as e:
        logger.error(f"Erro de sintaxe no XML (Malformado): {e}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao ler XML: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Converte conteúdo de XML laboratorial para RTF.")
    parser.add_argument("file", nargs='?', help="Caminho do arquivo XML específico. Se omitido, busca na pasta de entrada.")
    parser.add_argument("-i", "--input-dir", default=".", help="Diretório para buscar arquivos XML (padrão: atual).")
    parser.add_argument("-o", "--output-dir", help="Diretório para salvar o arquivo RTF (padrão: mesmo do XML).")
    args = parser.parse_args()

    # 1. Determinar arquivo de entrada
    input_path = args.file
    
    # Se arquivo não foi passado explicitamente, busca no diretório de entrada
    if not input_path:
        input_path = find_latest_xml(args.input_dir)
        if not input_path:
            logger.error(f"Nenhum arquivo XML encontrado em '{args.input_dir}' e nenhum caminho fornecido.")
            sys.exit(1)
    
    if not os.path.exists(input_path):
        logger.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    logger.info(f"Processando arquivo: {input_path}")

    # 2. Extrair conteúdo
    content = parse_xml_content(input_path)
    
    if not content:
        logger.warning("Falha ao extrair conteúdo ou conteúdo vazio. Arquivo RTF não será gerado.")
        sys.exit(1)

    # 3. Gerar caminho de saída
    filename = os.path.basename(input_path)
    base_name = os.path.splitext(filename)[0]
    
    if args.output_dir:
        # Se diretório de saída foi especificado
        if not os.path.exists(args.output_dir):
            try:
                os.makedirs(args.output_dir)
                logger.info(f"Diretório de saída criado: {args.output_dir}")
            except OSError as e:
                logger.error(f"Não foi possível criar o diretório de saída: {e}")
                sys.exit(1)
        output_path = os.path.join(args.output_dir, f"{base_name}.rtf")
    else:
        # Padrão: Salva no mesmo diretório do arquivo original
        output_dir = os.path.dirname(input_path)
        output_path = os.path.join(output_dir, f"{base_name}.rtf")

    # 4. Criar RTF
    success = RTFConverter.create_file(content, output_path)
    
    if success:
        logger.info("Conversão concluída com sucesso.")
    else:
        logger.error("Falha na conversão.")
        sys.exit(1)

if __name__ == "__main__":
    main()
