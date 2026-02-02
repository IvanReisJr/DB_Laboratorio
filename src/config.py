import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    BASE_URL_LOGIN = "https://out-prd.diagnosticosdobrasil.com.br/Portal/Login"
    BASE_URL_HOME = "https://out-prd.diagnosticosdobrasil.com.br/Portal/Home"
    BASE_URL_PATIENTS = "https://out-prd.diagnosticosdobrasil.com.br/Portal/MeusPacientes?In_Status=10&chave="
    
    # Credenciais obtidas de variáveis de ambiente
    SERVICE_CODE = os.getenv("DB_SERVICE_CODE")
    CPF = os.getenv("DB_CPF")
    PASSWORD = os.getenv("DB_PASSWORD")
    
    # Validação simples para alertar se faltar algo
    if not all([SERVICE_CODE, CPF, PASSWORD]):
        raise ValueError("ERRO CRÍTICO: Credenciais não encontradas no arquivo .env")
    
    # Timeouts
    TIMEOUT_DEFAULT = 10  # segundos
