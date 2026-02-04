from datetime import datetime
import time
import logging
from src.bot import DBAutomator

# Configuração de Logger para o Main (para ver tentativas)
logger = logging.getLogger(__name__)

def main():
    MAX_ATTEMPTS = 3
    logger.info("=== AGENDADOR INICIADO (08h às 22h) ===")
    
    while True:
        now = datetime.now()
        current_hour = now.hour
        
        if 8 <= current_hour <= 22:
            logger.info(f"Hora atual: {current_hour}h. Dentro do horário de execução.")
            
            # === BLOCO DE TENTATIVAS (Lógica Original) ===
            attempt = 1
            success = False
            while attempt <= MAX_ATTEMPTS and not success:
                logger.info(f"--- TENTATIVA {attempt}/{MAX_ATTEMPTS} ---")
                try:
                    bot = DBAutomator(headless=False)
                    success = bot.run()
                    if success:
                        logger.info(f"--- SUCESSO NA TENTATIVA {attempt} ---")
                    else:
                        logger.warning(f"--- FALHA NA TENTATIVA {attempt} ---")
                except Exception as e:
                    logger.critical(f"Erro não tratado: {e}")
                
                if not success:
                    if attempt < MAX_ATTEMPTS:
                        time.sleep(10)
                    else:
                        logger.error("--- TODAS AS TENTATIVAS FALHARAM ---")
                attempt += 1
            # =============================================
            
            # Dorme até a próxima hora cheia
            logger.info("Dormindo 1 hora até a próxima execução...")
            time.sleep(3600)
            
        else:
            logger.info(f"Hora atual: {current_hour}h. Fora do horário (08h-22h). Dormindo...")
            time.sleep(1800) # Dorme 30 min e verifica de novo

if __name__ == "__main__":
    main()
