import logging
import os
import re
from dotenv import load_dotenv
from utils.tasy_client import TasyClient

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_db_connection():
    try:
        # 1. Carregar Query
        query_path = os.path.join("querys", "Prescricao_medica.sql")
        with open(query_path, 'r', encoding='utf-8') as f:
            sql_query = f.read()

        # Limpeza básica da query
        sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)

        # 2. Inicializar Cliente
        logger.info("Inicializando Cliente Tasy...")
        client = TasyClient()
        
        # 3. Executar Query
        test_id = 6788792
        params = {'NR_PRESCRICAO': test_id}
        
        logger.info(f"Executando query Prescricao_medica.sql para ID: {test_id}...")
        results = client._execute_query_and_fetch_all(sql_query, params)
        
        # 4. Exibir Resultados
        if results:
            logger.info("Query executada com SUCESSO!")
            logger.info(f"Registros encontrados: {len(results)}")
            
            # Exibe o primeiro registro como amostra
            first_row = results[0]
            logger.info("--- Amostra do Primeiro Registro ---")
            for key, value in first_row.items():
                logger.info(f"{key}: {value}")
            logger.info("------------------------------------")
            return True
        else:
            logger.warning("Query executada, mas NENHUM registro foi retornado.")
            return True 
            
    except Exception as e:
        logger.error(f"FALHA na validação do banco de dados: {e}")
        return False

if __name__ == "__main__":
    validate_db_connection()
