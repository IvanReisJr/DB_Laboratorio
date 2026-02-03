import oracledb
import os
import re
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from striprtf.striprtf import rtf_to_text

# Configuração de Logger
logger = logging.getLogger(__name__)

class TasyClient:
    """
    Cliente reutilizável para conexão e operações no banco de dados Oracle (Tasy).
    
    Responsabilidade:
        - Gerenciar conexões com o banco de dados.
        - Executar queries parametrizadas de forma segura.
        - Tratar erros específicos do OracleDB.
        - Normalizar dados retornados.
    """

    def __init__(self):
        """
        Inicializa o cliente carregando as configurações das variáveis de ambiente.
        """
        self.user = os.environ.get("DB_USER")
        self.password = os.environ.get("DB_PASSWORD")
        self.dsn = os.environ.get("DB_DSN")

        if not all([self.user, self.password, self.dsn]):
             logger.warning("Credenciais de banco de dados incompletas nas variáveis de ambiente.")

        # Inicialização do Oracle Client (Thick Mode)
        try:
            import platform
            
            # Caminho base (onde está este arquivo tasy_client.py)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            if platform.system() == "Windows":
                lib_dir = os.path.join(base_dir, "instantclient_23_6")
            elif platform.system() == "Darwin": # macOS
                lib_dir = os.path.join(base_dir, "instantclient-basiclite-macos")
            else:
                lib_dir = None
                logger.warning(f"Sistema operacional {platform.system()} não mapeado para Instant Client local.")

            if lib_dir and os.path.exists(lib_dir):
                # Tenta inicializar apenas se ainda não estiver inicializado
                try:
                    oracledb.init_oracle_client(lib_dir=lib_dir)
                    logger.info(f"Oracle Client (Thick Mode) inicializado em: {lib_dir}")
                except oracledb.DatabaseError as e:
                    # Ignora erro se já estiver inicializado
                    if "DPY-1012" not in str(e): # DPY-1012: already initialized
                         logger.warning(f"Aviso ao inicializar Oracle Client: {e}")
            else:
                 if lib_dir:
                    logger.warning(f"Diretório do Oracle Client não encontrado: {lib_dir}")
                    
        except Exception as e:
            logger.error(f"Falha na configuração do Oracle Client: {e}")

    def _get_connection(self):
        """Estabelece e retorna uma conexão com o banco de dados."""
        try:
            connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            logger.debug("Conexão com Oracle estabelecida com sucesso.")
            return connection
        except oracledb.Error as e:
            logger.error(f"Erro ao conectar ao Oracle: {e}")
            raise

    def authenticate_user(self, username: str, password_code: str) -> Optional[Dict[str, Any]]:
        """
        Autentica um usuário (Pessoa Física) baseado no prontuário e código.
        
        Args:
            username: Número do prontuário.
            password_code: Código da pessoa física (CD_PESSOA_FISICA).
            
        Returns:
            Dicionário com dados do usuário se autenticado, None caso contrário.
        """
        sql = """
            SELECT
                PF.CD_PESSOA_FISICA CODIGO,
                UPPER(PF.NM_PESSOA_FISICA) NOME,
                PF.NR_CPF CPF,
                PF.NR_PRONTUARIO PRONTUARIO
            FROM PESSOA_FISICA PF
            WHERE PF.NR_PRONTUARIO = :USERNAME
            AND PF.CD_PESSOA_FISICA = :PASSWORD
        """
        params = {'USERNAME': username, 'PASSWORD': password_code}
        
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    result = cursor.fetchone()
                    
                    if result:
                        logger.info(f"Usuário autenticado: {result[1]} (Código: {result[0]})")
                        return {
                            "codigo": result[0],
                            "nome": result[1],
                            "cpf": result[2],
                            "prontuario": result[3]
                        }
                    else:
                        logger.warning(f"Falha de autenticação para usuário: {username}")
                        return None
        except oracledb.Error as e:
            logger.error(f"Erro na autenticação: {e}")
            return None



    def _load_query(self, filename: str) -> str:
        """
        Lê e retorna o conteúdo de um arquivo SQL da pasta 'querys'.
        
        Args:
            filename: Nome do arquivo (ex: 'Resultados_Exames.sql').
        """
        try:
            # Caminho relativo: sobe um nível de 'utils' para a raiz e entra em 'querys'
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            query_path = os.path.join(base_dir, 'querys', filename)
            
            if not os.path.exists(query_path):
                raise FileNotFoundError(f"Arquivo de query não encontrado: {query_path}")
                
            with open(query_path, 'r', encoding='utf-8') as f:
                sql = f.read()
                
            # Limpeza básica de comentários (opcional, mas recomendada para oracledb)
            sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
            return sql
            
        except Exception as e:
            logger.error(f"Erro ao carregar query '{filename}': {e}")
            raise

    def fetch_exams(self, cd_pessoa_fisica: str) -> List[Dict[str, Any]]:
        """
        Busca todos os exames de um paciente.

        Args:
            cd_pessoa_fisica: Código do paciente.

        Returns:
            Lista de dicionários contendo os dados dos exames.
        """
        # Carrega a query do arquivo externo
        sql = self._load_query("Resultados_Exames.sql")
        
        params = {'CD_PESSOA_FISICA': cd_pessoa_fisica}
        
        return self._execute_query_and_fetch_all(sql, params)

    def fetch_single_exam(self, cd_pessoa_fisica: str, id_exame_item: str, nr_prescricao: str) -> Optional[Dict[str, Any]]:
        """
        Busca um exame específico para geração de PDF.
        """
        sql = """
            SELECT 
                Obter_Desc_Exame(PPROC.NR_SEQ_EXAME) AS EXAME,
                to_char(RL.DT_COLETA,'DD/MM/YYYY HH24:MI') AS DATA_COLETA,
                to_char(RL.DT_ATUALIZACAO,'DD/MM/YYYY HH24:MI') AS DATA_ATUALIZACAO,         
                INITCAP(Obter_Dados_Usuario_Opcao(RL.nm_usuario,'NP')) AS NM_PROFISSIONAL,  
                NVL(INITCAP(CG.DS_CARGO), ' - ') AS CARGO,
                NVL(CPROF.SG_CONSELHO, ' - ') AS DS_CONSELHO,
                NVL(PF_PROF.DS_CODIGO_PROF,' - ') AS DS_PROFISSIONAL,
                PPROC.NR_SEQUENCIA AS ID_EXAME_ITEM,
                RL.NR_PRESCRICAO AS NR_PRESCRICAO,
                PPROC.NR_SEQUENCIA AS NR_SEQUENCIA,
                RL.DS_RESULTADO AS RESULTADO,
                P.NM_PESSOA_FISICA AS NOME_PACIENTE
            FROM pessoa_fisica P 
            INNER JOIN prescr_medica PM ON (PM.CD_PESSOA_FISICA = P.CD_PESSOA_FISICA)
            INNER JOIN prescr_procedimento PPROC ON (PPROC.NR_PRESCRICAO = PM.NR_PRESCRICAO)
            INNER JOIN exame_laboratorio EL ON (EL.NR_SEQ_EXAME = PPROC.NR_SEQ_EXAME)
            INNER JOIN grupo_exame_lab GEL ON (GEL.NR_SEQUENCIA = EL.NR_SEQ_GRUPO)
            INNER JOIN exame_lab_resultado ELR ON (ELR.NR_PRESCRICAO = PM.NR_PRESCRICAO) 
            INNER JOIN exame_lab_result_item ELRI ON (ELR.nr_seq_resultado = ELRI.nr_seq_resultado AND ELRI.NR_SEQ_PRESCR = PPROC.NR_SEQUENCIA)
            INNER JOIN result_laboratorio RL ON (RL.NR_PRESCRICAO = PPROC.NR_PRESCRICAO AND RL.NR_SEQ_PRESCRICAO = PPROC.NR_SEQUENCIA)
            INNER JOIN USUARIO U ON (U.NM_USUARIO = RL.nm_usuario)
            INNER JOIN PESSOA_FISICA PF_PROF ON (U.CD_PESSOA_FISICA = PF_PROF.CD_PESSOA_FISICA)
            LEFT JOIN CARGO CG ON (CG.CD_CARGO = PF_PROF.CD_CARGO)
            LEFT JOIN CONSELHO_PROFISSIONAL CPROF ON (CPROF.NR_SEQUENCIA = PF_PROF.NR_SEQ_CONSELHO)
            WHERE ELRI.NR_SEQ_MATERIAL IS NOT NULL
            AND (RL.ie_formato_texto IS NULL OR RL.ie_formato_texto <> 3)
            AND P.CD_PESSOA_FISICA = :CD_PESSOA_FISICA 
            AND PPROC.NR_SEQUENCIA = :ID_EXAME_ITEM 
            AND RL.NR_PRESCRICAO = :NR_PRESCRICAO 
        """
        params = {
            'CD_PESSOA_FISICA': cd_pessoa_fisica,
            'ID_EXAME_ITEM': id_exame_item,
            'NR_PRESCRICAO': nr_prescricao
        }
        
        results = self._execute_query_and_fetch_all(sql, params)
        return results[0] if results else None

    def _execute_query_and_fetch_all(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Método auxiliar para executar SELECT e retornar lista de dicts."""
        files_list = []
        try:
            with self._get_connection() as connection:
                with connection.cursor() as cursor:
                    logger.debug(f"Executando SQL com parametros: {params}")
                    cursor.execute(sql, params)
                    
                    # Obter nomes das colunas
                    col_names = [row[0] for row in cursor.description]
                    
                    for row in cursor:
                        row_dict = dict(zip(col_names, row))
                        # Conversão automática de RTF
                        self._process_rtf_field(row_dict)
                        files_list.append(row_dict)
                        
            return files_list
        except oracledb.Error as e:
            logger.error(f"Erro ao executar query: {e}")
            return []

    def _process_rtf_field(self, data_dict: Dict[str, Any], field_name: str = 'RESULTADO'):
        """Processa e limpa campos RTF no dicionário de dados."""
        rtf_content = data_dict.get(field_name)
        if rtf_content:
            try:
                data_dict[f'{field_name}_TEXTO_PURO'] = rtf_to_text(rtf_content, errors="ignore")
            except Exception as e:
                logger.error(f"Erro ao converter RTF: {e}")
                data_dict[f'{field_name}_TEXTO_PURO'] = "Erro ao processar conteúdo do exame."
