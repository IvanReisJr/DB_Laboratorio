# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

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
