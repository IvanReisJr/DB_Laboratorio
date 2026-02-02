import time
import logging
from src.bot import DBAutomator

# Configuração de Logger para o Main (para ver tentativas)
logger = logging.getLogger(__name__)

def main():
    MAX_ATTEMPTS = 3
    attempt = 1
    success = False
    
    while attempt <= MAX_ATTEMPTS and not success:
        logger.info(f"=== INICIANDO TENTATIVA {attempt}/{MAX_ATTEMPTS} ===")
        
        try:
            # Instancia um novo bot a cada tentativa para garantir "limpeza" completa
            bot = DBAutomator(headless=False)
            success = bot.run()
            
            if success:
                logger.info(f"=== SUCESSO NA TENTATIVA {attempt} ===")
            else:
                logger.warning(f"=== FALHA NA TENTATIVA {attempt} ===")
                
        except Exception as e:
            logger.critical(f"Erro não tratado no Main: {e}")
            
        if not success:
            if attempt < MAX_ATTEMPTS:
                wait_time = 10
                logger.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                time.sleep(wait_time)
            else:
                logger.error("=== TODAS AS TENTATIVAS FALHARAM. DESISTINDO. ===")
        
        attempt += 1

if __name__ == "__main__":
    main()
