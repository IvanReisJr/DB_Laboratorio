# 🎨 Documentação da Interface Gráfica (CustomTkinter)

Este documento detalha a arquitetura e implementação da interface gráfica (GUI) adotada no projeto, utilizando a biblioteca **CustomTkinter**. Esta estrutura foi projetada para ser moderna, responsiva e thread-safe, pronta para ser reutilizada em outros projetos de automação.

## 🛠️ Tecnologias Utilizadas

- **Library Principal**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
  - *Por que?* Oferece uma aparência moderna (Windows 11 style), suporte nativo a temas Dark/Light e escala de DPI automática.
- **Concorrência**: `threading` (Módulo nativo do Python)
  - *Por que?* Essencial para impedir que a interface congele ("trave") enquanto tarefas pesadas (como automação Selenium ou queries de banco) rodam em background.

## 🏗️ Estrutura da Classe `HSFApp`

A aplicação é encapsulada em uma classe que herda de `ctk.CTk`.

### Modelo Boilerplate

```python
import customtkinter as ctk
import threading

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Configurações da Janela
        self.title("Meu App Moderno")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 2. Estado
        self.executando = False
        
        # 3. Construção da UI
        self._criar_interface()

    def _criar_interface(self):
        # ... widgets ...
        pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
```

## 🧩 Componentes Principais

### 1. Frames Organizadores
Utilizamos `ctk.CTkFrame` para dividir a interface em seções lógicas.
- **Main Frame**: Container principal com padding para "respiro".
- **Status Frame**: Barra superior ou intermediária para feedbacks rápidos.
- **Botões Frame**: Área dedicada aos controles de ação.

### 2. Labels e Títulos
- **Títulos**: Fontes maiores e negrito (`weight="bold"`).
- **Status Label**: Texto dinâmico que muda de cor (Verde para "Parado", Amarelo/Laranja para "Rodando").

### 3. Botões Modernos
Botões com cores semânticas e estados (disabled/normal).

```python
self.btn_acao = ctk.CTkButton(
    self.frame,
    text="▶️ Iniciar",
    command=self.funcao_acao,
    font=ctk.CTkFont(size=16, weight="bold"),
    height=50,
    fg_color="#1f6aa5",     # Azul profissional
    hover_color="#144870",  # Azul mais escuro no hover
    state="normal"
)
```

### 4. Área de Logs (Console Visual)
Um `ctk.CTkTextbox` somente leitura (ou gerenciado via código) que atua como um console embutido.
- **Fonte**: Monospaced (`Consolas`, `Courier`) para alinhamento.
- **Auto-scroll**: Sempre rola para a última linha inserida (`self.log_text.see("end")`).

## 🔄 Padrão de Execução Assíncrona (Threading)

Para evitar o congelamento da GUI ("Não Respondendo"), **nunca** executamos lógica pesada na *main thread*.

### O Padrão "Worker Thread"

1. **Gatilho**: Usuário clica no botão "Executar".
2. **Preparação**:
   - Muda flag `self.executando = True`.
   - Bloqueia botão "Executar".
   - Libera botão "Parar".
   - Atualiza Status Label.
3. **Thread**: Dispara uma nova thread apontando para `_executar_logica`.
4. **Execução**: A lógica roda em background.
5. **Finalização (Finally)**:
   - Reseta flags.
   - Restaura estado dos botões.
   - Atualiza Status Label.

```python
def acao_botao(self):
    if self.executando: return
    
    # Preparação Visual
    self.executando = True
    self.btn_iniciar.configure(state="disabled")
    
    # Lançar Thread
    threading.Thread(target=self._worker, daemon=True).start()

def _worker(self):
    try:
        # TAREFA PESADA AQUI
        processamento_longo()
        self.adicionar_log("Sucesso!")
    except Exception as e:
        self.adicionar_log(f"Erro: {e}")
    finally:
        # Importante: Atualizações de UI devem ser thread-safe
        # No CustomTkinter, muitas vezes funciona direto, mas o ideal é usar .after
        self.after(0, self._resetar_estado)
```

## 📡 Integração Backend -> GUI (Callbacks)

Para que o script de backend (`main.py`) "fale" com a interface sem saber que ela existe, usamos o padrão de **Callback**.

1. **No Backend**: Cria-se uma variável global `_callback` e uma função `set_callback`. No momento do log, se o callback existir, ele é chamado.
2. **Na GUI**: Passamos o método `self.adicionar_log` como callback para o backend.

Isso desacopla o código: o backend continua funcionando sozinho via terminal, mas se tiver uma GUI acoplada, ele manda mensagens para ela.

## 📦 Lista de Widgets Úteis Usados

| Widget | Função | Configuração Chave |
| :--- | :--- | :--- |
| `CTkLabel` | Textos e Status | `text_color`, `font` |
| `CTkButton` | Ações | `fg_color`, `hover_color`, `command` |
| `CTkFrame` | Layout | `pack(fill="both")`, `grid()` |
| `CTkTextbox` | Logs/Console | `state="normal"/"disabled"`, `wrap="word"` |

---

Este padrão é robusto o suficiente para aplicações de automação, dashboards de monitoramento e ferramentas internas.
