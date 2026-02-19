# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.8.0] - 2026-02-19
### Adicionado
- **Resiliência (Decorators)**: Implementação do decorator `@retry_action` em `src/decorators.py` para gerenciar tentativas de execução com backoff exponencial e logging padronizado.
- **Refatoração do Bot**: Aplicação do decorator na seleção de filtros (`step_5_filters_status`) e na exportação de XML (`step_7_search_and_download`), substituindo loops `try/except` manuais por uma abordagem declarativa.
- **Testes**: Adição de testes unitários para o novo decorator em `tests/test_decorators.py`.

## [1.7.0] - 2026-02-03
### Adicionado
- **Integração Tasy**: Implementação do método `fetch_patient_by_prescription` no `TasyClient`, permitindo buscar dados cadastrais do paciente (Nome, CPF, Prontuário) a partir do número da prescrição (extraído do nome do arquivo XML).
- **Queries**: Criação do arquivo `querys/Pessoa_Fisica.sql` para suportar a busca de dados do paciente.
- **Fluxo Principal**: Atualização do `src/separacao.py` para consultar automaticamente o banco de dados durante o processamento do lote, enriquecendo o log com os dados do paciente.
### Corrigido
- **Bot**: Correção de erro de sintaxe JavaScript (`SyntaxError: missing )`) ao tentar clicar no checkbox de seleção de exames. O erro ocorria devido a conflito de aspas no seletor CSS utilizado.
### Alterado
- **Persistência de Arquivos**: O bot agora **COPIA** o XML baixado para a pasta de backup anual (ex: `2026/`) ao invés de movê-lo, garantindo que o arquivo original permaneça na pasta de entrada mensal (ex: `202602/`).
- **Segurança**: Recuperação de credenciais do Portal a partir do histórico para o `.env`.
### Novo
- **Interface Gráfica (GUI)**: Implementação de uma interface moderna (`src/gui.py`) utilizando `customtkinter`. A GUI permite iniciar/parar a automação e visualizar logs em tempo real sem travar a janela (threading).
- **Documentação**: Atualização completa do `README.md` e `Anotacoes.txt` com instruções para uso da GUI e configuração do arquivo `.env`.
### Corrigido
- **GUI**: Adição de correção de `sys.path` em `src/gui.py` para permitir a execução direta do script sem erros de importação (`ModuleNotFoundError`).
### Agendamento e Correção
- **Agendador (Scheduler)**: Implementação de ciclo de execução contínuo em `main.py`, configurado para rodar apenas entre **08:00 e 22:00**, com intervalo de 1 hora entre execuções. Fora do horário comercial, o sistema entra em modo de espera (sleep de 30min).
- **Bot**: Implementação de disparo forçado de eventos (`change`, `input`, `click`) via JavaScript no checkbox de seleção, resolvendo o problema onde o botão de download permanecia desabilitado mesmo após a seleção visual.
- **Filtro**: Ajuste do filtro de data para considerar sempre o dia atual (`HOJE`), removendo o retrocesso de 4 dias utilizado em testes anteriores.

## [1.6.2] - 2026-02-03
### Refatorado
- **TasyClient**: Externalização da query `fetch_single_exam` para o arquivo `querys/Resultado_Exame.sql`, completando a migração de SQL para arquivos externos.

## [1.6.1] - 2026-02-03
### Refatorado
- **TasyClient**: Implementação do método `_load_query` para leitura de arquivos `.sql` externos, removendo queries hardcoded do código Python.
- **Queries**: Externalização da query de busca de exames para `querys/Resultados_Exames.sql`.

## [1.6.0] - 2026-02-03
### Adicionado
- **Integração Oracle Tasy**: Módulo `tasy_client.py` refatorado para suportar conexão Thick Mode com detecção automática de biblioteca (Windows/macOS) através da pasta `utils`.
- **Validação de Banco**: Script `validate_db.py` criado para testar conectividade e execução de queries SQL.
- **Dependências**: Adição de `oracledb` e `striprtf` ao `requirements.txt`.

## [1.3.1] - 2026-02-02
### Adicionado
- Estratégia de seleção de checkbox por ID específico (`#Checkbox3`).
- Correção na validação de arquivos baixados (verificação direta de path).
- Remoção da injeção de Zoom 75% (retorno ao padrão).
- Garantia de inicialização do navegador maximizado (`--start-maximized`).
- Adição de lógica para verificar se a tabela está vazia antes de buscar checkboxes.
- Melhoria na robustez da seleção de checkbox utilizando `.first` e tratamento de erros de API.
- Reversão do filtro de data para 4 dias retroativos (para fins de desenvolvimento).
- **Segurança**: Adição de `*.xml` ao `.gitignore` e remoção de arquivos XML sensíveis do repositório.

- **Segurança**: Adição de `*.xml` ao `.gitignore` e remoção de arquivos XML sensíveis do repositório.

## [1.5.1] - 2026-02-02
### Adicionado
- **Resiliência (Global Retry Live)**: Implementação de um supervisor (`main.py`) que reinicia automaticamente o robô em caso de falhas críticas (timeouts, erros de renderização), com limite de 3 tentativas e fallback seguro.

## [1.5.0] - 2026-02-02
### Adicionado
- **Extração de Dados Limpos**: Implementação do módulo `cleaner.py` que converte os dados brutos do XML (exame, metodologia e resultados) para arquivos TXT simplificados, facilitando a leitura e auditoria.
- **Automação**: Geração automática de TXTs na pasta anual (ex: `2026/`) durante o processo de separação de lotes.

## [1.4.2] - 2026-02-02
### Segurança
- **Hardening de Credenciais**: Substituição de credenciais hardcoded em `config.py` pelo uso seguro de variáveis de ambiente (`.env`), utilizando a biblioteca `python-dotenv`.

## [1.4.1] - 2026-02-02
### Corrigido
- **Interface**: Implementação de maximização forçada da janela do navegador utilizando chamadas diretas à API do Windows (`ctypes`), resolvendo inconsistências onde o argumento `--start-maximized` falhava.

## [1.4.0] - 2026-02-02
### Adicionado
- **Deduplicação Inteligente**: Sistema que evita o download/processamento duplicado de exames já existentes, utilizando um histórico local (`processed_exams.json`).
- **Organização de Backups**: Movimentação automática do arquivo XML "Pai" (Lote) para uma pasta anual (ex: `2026/`) após o processamento, mantendo a pasta de mês limpa.
- **Robustez de UI**: Melhoria na interação com checkboxes via JavaScript, disparando eventos (`change`, `input`, `click`) para garantir habilitação de botões dependentes.

## [1.3.0] - 2026-02-02

### Adicionado
- **Zoom de Interface**: Injeção automática de JavaScript para definir o zoom da página em 75% (`document.body.style.zoom = '0.75'`), mitigando erros de resolução.
- **Logging em Arquivo**: Configuração para salvar todos os logs da execução no arquivo `log.txt` na raiz do projeto.


## [1.2.0] - 2026-01-30

### Adicionado
- **Testes Unitários**: Criação de suíte de testes com `pytest` para validar `separacao.py` e `xml_to_rtf.py`.
- **Diagnóstico**: Relatório detalhado dos pontos de atenção do projeto (`diagnosis.md`).
- **Dependências**: Adição de `pytest` ao ambiente de desenvolvimento.
- **Documentação**: Criação do arquivo `Anotacoes.txt` com guia de execução detalhado e atualização do `task.md`.
- **Estrutura**: Centralização e reconstrução do histórico no arquivo `CHANGELOG.md` na raiz do projeto.

### Corrigido
- **Conversão RTF**: Correção na codificação de caracteres especiais no módulo `xml_to_rtf.py` para garantir compatibilidade com `iso-8859-1`/`cp1252`.

## [1.1.0] - 2026-01-26

### Adicionado
- **Integração de Separação de XML**: Chamada automática para `separar_lote_xml` logo após a validação do download no passo 7.
- **Temporizadores**: Adicionados intervalos de 5 segundos entre os passos principais para estabilidade.
- **Robustez no Passo 7**:
  - Verificação explícita da visibilidade da tabela de resultados.
  - Tratamento para mensagem "Nenhum registro encontrado".
  - Estratégia de múltiplos seletores para encontrar o checkbox "Selecionar Todos" (priorizando `Checkbox3`).
- **Logs Detalhados**: Melhoria nos logs para diagnóstico de falhas no clique do checkbox e validação de download.

### Corrigido
- **Importação de Módulo**: Correção do path de importação `from src.separacao` em `bot.py`.
- **Seletores do Portal**: Atualização dos seletores para corresponder aos IDs e classes reais (`StatusDropdown`, `.dropdown-status-txt`, `Btn_Pesquisar`, `Checkbox3`, `BtnResultadoXML`).
- **Erro de Sintaxe JS**: Correção de aspas conflitantes na execução de JavaScript para clique forçado.
- **Ordem de Execução**: Inversão dos passos para executar o ajuste de data antes do filtro de status.

## [1.0.0] - 2024-01-17

### Adicionado
- **Validação de Download**: Função `validate_xml_download` para confirmar a integridade do arquivo baixado.
- **Injeção de JS**: Método `force_input_date` para preencher datas diretamente, contornando campos `readonly`.
- **Gitignore**: Arquivo para ignorar ambientes virtuais e logs.

### Alterado
- **Core**: Unificação da lógica dos arquivos `bot copy X.py` em um único `src/bot.py`.
- **Seleção de Data**: Substituição da simulação de teclado (que causava bug do ano 2026) pela manipulação direta do DOM via JavaScript.
- **Lógica de "Ontem"**: Correção do cálculo de `timedelta` de 2 dias para 1 dia.

### Removido
- Arquivos duplicados de backup (`bot copy.py`, etc) devem ser excluídos manualmente para limpeza.
- Dependência de navegação manual no calendário Flatpickr.

## [0.1.0] - 2024-01-15 (Histórico Git)

### Inicial
- **Criação do Sistema**: Commit inicial do projeto.
- **Estrutura Básica**: Implementação inicial com Playwright (`src/bot.py`).
