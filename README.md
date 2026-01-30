# Automação DB Diagnósticos

Este projeto é uma automação de web scraping desenvolvida em Python para acessar o portal da Diagnósticos do Brasil, realizar autenticação em duas etapas, navegar até a lista de pacientes, aplicar filtros de data e status, realizar o download do lote de exames em XML e separar automaticamente este lote em arquivos individuais.

## 📋 Estrutura do Projeto

```
DB_Laboratorio/
├── src/
│   ├── __init__.py
│   ├── bot.py       # Lógica principal da automação (Playwright)
│   ├── config.py    # Configurações e credenciais
│   ├── separacao.py # Lógica de processamento e separação de XMLs
│   ├── CHANGELOG.md # Histórico de mudanças e versões
├── main.py          # Ponto de entrada do script
├── requirements.txt # Dependências do projeto
├── .gitignore       # Arquivos ignorados pelo Git
└── README.md        # Documentação
```

## 🚀 Configuração do Ambiente

### 1. Pré-requisitos
- Python 3.8 ou superior instalado.

### 2. Criação do Ambiente Virtual (venv)

Abra o terminal na raiz do projeto (`c:\IvanReis\Sistemas_HSF\DB_Laboratorio`) e execute:

> **Nota:** Utilize apenas uma pasta para o ambiente virtual. O padrão deste projeto é `venv`.

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

### Fluxo de Execução:
1.  **Inicialização**: Abre o navegador Chromium controlado pelo Playwright.
2.  **Login**:
    *   Insere o código de "Serviço Solicitante".
    *   Insere CPF e Senha.
3.  **Navegação**: Acessa a página "Meus Pacientes".
4.  **Ajuste de Filtros**:
    *   **Data Inicial**: Define a data de início (padrão: D-6 dias) usando manipulação de calendário.
    *   **Status**: Seleciona o filtro "Completo".
5.  **Pesquisa e Download**:
    *   Clica em "Pesquisar".
    *   Aguardar a grid carregar e seleciona o checkbox "Todos" (usa estratégia de múltiplos seletores para robustez).
    *   Baixa o arquivo XML do lote.
6.  **Pós-Processamento**:
    *   Valida se o arquivo foi baixado corretamente na pasta `Downloads`.
    *   Executa `separar_lote_xml` para dividir o lote em arquivos individuais por atendimento (codificação `ISO-8859-1`).

## 🧠 Lógica do Sistema

O sistema utiliza **Playwright** para máxima performance e robustez, com as seguintes características:

1.  **Configuração Centralizada (`src/config.py`)**: URLs e credenciais fáceis de alterar.
2.  **Automação Resiliente (`src/bot.py`)**:
    - **Auto-Wait**: Aguarda elementos estarem prontos antes de interagir.
    - **Seletores Robustos**: Utiliza múltiplos seletores (IDs, Classes, atributos ARIA) para encontrar elementos críticos como o checkbox de seleção.
    - **Tratamento de Erros**: Captura screenshots automáticos em caso de falhas (`erro_*.png` e `debug_*.png`) para facilitar o diagnóstico.
    - **Temporizadores**: Intervalos estratégicos para garantir a estabilidade em conexões mais lentas.
3.  **Processamento de Dados (`src/separacao.py`)**:
    - Parser XML dedicado que preserva a estrutura e codificação originais do laboratório.

## 🔄 Histórico e Migração

Este projeto evoluiu de uma solução Selenium para Playwright visando:
- **Maior Velocidade**: Execução sem overhead de WebDriver.
- **Estabilidade**: Menos erros de interatividade.
- **Funcionalidades Avançadas**: Interceptação de download e injeção de JavaScript para contornar limitações de interface.

---
Desenvolvido por Trae AI.
