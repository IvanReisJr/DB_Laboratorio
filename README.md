# Automação DB Diagnósticos

Este projeto é uma automação de web scraping desenvolvida em Python para acessar o portal da Diagnósticos do Brasil, realizar autenticação em duas etapas e navegar até a lista de pacientes com filtros aplicados.

## 📋 Estrutura do Projeto

```
DB_Laboratorio/
├── src/
│   ├── __init__.py
│   ├── bot.py       # Lógica principal da automação (Playwright)
│   ├── config.py    # Configurações e credenciais
├── main.py          # Ponto de entrada do script
├── CHANGELOG.md     # Histórico de mudanças e versões
├── requirements.txt # Dependências do projeto
├── .gitignore       # Arquivos ignorados pelo Git
└── README.md        # Documentação
```

## 🚀 Configuração do Ambiente

### 1. Pré-requisitos
- Python 3.8 ou superior instalado.

### 2. Criação do Ambiente Virtual (venv)

Abra o terminal na raiz do projeto (`c:\IvanReis\Sistemas_HSF\DB_Laboratorio`) e execute:

> **Nota:** Utilize apenas uma pasta para o ambiente virtual. O padrão deste projeto é `venv`. Caso existam pastas como `.ven` ou `ven` duplicadas, remova-as para manter a organização.

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalação das Dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
playwright install chromium
```

Isso instalará:
- `playwright`: Biblioteca moderna de automação.
- `chromium`: Navegador necessário para execução.

## 🏃 Como Executar

Para rodar a automação:

```bash
python main.py
```

O script irá:
1. Abrir o navegador Chromium (controlado pelo Playwright).
2. Acessar a página de login.
3. Inserir o "Serviço Solicitante" e avançar.
4. Inserir CPF, pressionar TAB e inserir a Senha.
5. Fazer login e navegar para "Meus Pacientes".
6. Aplicar o filtro "completo".

## 🧠 Lógica do Sistema

O sistema utiliza **Playwright** para máxima performance e robustez:

1.  **Configuração Centralizada (`src/config.py`)**: URLs e credenciais.
2.  **Lógica Modular (`src/bot.py`)**:
    - **Auto-Wait**: O Playwright aguarda automaticamente os elementos estarem prontos antes de interagir, eliminando a necessidade de `sleeps` manuais na maioria dos casos.
    - **Seletores Robustos**: Utiliza seletores por texto, placeholder e atributos para localizar elementos de forma resiliente.
    - **Simulação de Teclado**: Simula pressionamento real de teclas (TAB) e digitação.

## 🔄 Migração Selenium -> Playwright

Este projeto foi migrado de Selenium para Playwright para garantir:
- **Maior Velocidade**: Execução mais rápida sem overhead de WebDriver.
- **Melhor Estabilidade**: Menos erros de "Element not interactive" ou "Stale element reference".
- **Facilidade de Manutenção**: Código mais limpo e legível.

---
Desenvolvido por Trae AI.
