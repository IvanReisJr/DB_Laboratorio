# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

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