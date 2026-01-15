class Config:
    BASE_URL_LOGIN = "https://out-prd.diagnosticosdobrasil.com.br/Portal/Login"
    BASE_URL_HOME = "https://out-prd.diagnosticosdobrasil.com.br/Portal/Home"
    BASE_URL_PATIENTS = "https://out-prd.diagnosticosdobrasil.com.br/Portal/MeusPacientes?In_Status=10&chave="
    
    # Credenciais (Em produção, use variáveis de ambiente)
    SERVICE_CODE = "C297419"
    CPF = "01397175796"
    PASSWORD = "Dani0510"
    
    # Timeouts
    TIMEOUT_DEFAULT = 10  # segundos
