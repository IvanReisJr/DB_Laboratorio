# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

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