import customtkinter as ctk
import threading
import logging
import time
from tkinter import END
from src.bot import DBAutomator

# Configuração de Log para a GUI
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(END, msg + '\n')
            self.text_widget.see(END)
            self.text_widget.configure(state='disabled')
        self.text_widget.after(0, append)

class HSFApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Configurações da Janela
        self.title("DB Laboratório Automator")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 2. Estado
        self.executando = False
        
        # 3. Construção da UI
        self._criar_interface()

    def _criar_interface(self):
        # Layout Principal (Grid 2x1: Controles em Cima, Logs embaixo)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # -- Frame Superior (Controles e Status) --
        self.top_frame = ctk.CTkFrame(self, corner_radius=10)
        self.top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(
            self.top_frame, 
            text="Automação DB Laboratório", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.lbl_titulo.pack(pady=(20, 10))

        # Status
        self.lbl_status = ctk.CTkLabel(
            self.top_frame, 
            text="Status: Aguardando...", 
            font=ctk.CTkFont(size=14),
            text_color="#AAAAAA"
        )
        self.lbl_status.pack(pady=(0, 20))

        # Botões
        self.btn_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.btn_iniciar = ctk.CTkButton(
            self.btn_frame,
            text="▶️ Iniciar Automação",
            command=self.iniciar_automacao,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=200,
            fg_color="#1f6aa5",     # Azul Profissional
            hover_color="#144870"
        )
        self.btn_iniciar.pack(side="left", padx=10)

        self.btn_parar = ctk.CTkButton(
            self.btn_frame,
            text="⏹️ Parar (Forçar)",
            command=self.parar_automacao,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=200,
            fg_color="#a51f1f",     # Vermelho
            hover_color="#701414",
            state="disabled"
        )
        self.btn_parar.pack(side="left", padx=10)

        # -- Frame Inferior (Logs) --
        self.log_frame = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.lbl_log = ctk.CTkLabel(self.log_frame, text="Console de Logs:", anchor="w")
        self.lbl_log.pack(fill="x", padx=10, pady=(10, 5))

        self.txt_log = ctk.CTkTextbox(
            self.log_frame, 
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled"
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configurar Log Handler
        self._setup_logging()

    def _setup_logging(self):
        # Adiciona um handler que escreve no textbox
        text_handler = TextHandler(self.txt_log)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
        
        # Pega o logger raiz e adiciona
        logger = logging.getLogger()
        logger.addHandler(text_handler)
        logger.setLevel(logging.INFO)

    def iniciar_automacao(self):
        if self.executando: return
        
        self.executando = True
        self.btn_iniciar.configure(state="disabled")
        self.btn_parar.configure(state="normal")
        self.lbl_status.configure(text="Status: 🚀 Executando...", text_color="#00FFAA")
        
        # Thread para não travar a GUI
        threading.Thread(target=self._worker, daemon=True).start()

    def parar_automacao(self):
        # Nota: Parar thread de forma bruta é complexo em Python. 
        # Aqui vamos apenas sinalizar visualmente, mas o ideal seria usar um flag de cancelamento no bot.
        self.lbl_status.configure(text="Status: ⚠️ Tentando parar...", text_color="#FF5500")
        # TODO: Implementar cancellation token no bot
    
    def _worker(self):
        try:
            bot = DBAutomator(headless=False)
            sucesso = bot.run()
            
            if sucesso:
                self.after(0, lambda: self._finalizar("✅ Concluído com Sucesso!", "#00FFAA"))
            else:
                self.after(0, lambda: self._finalizar("❌ Finalizado com Erro.", "#FF5500"))
                
        except Exception as e:
            logging.error(f"Erro fatal na thread: {e}")
            self.after(0, lambda: self._finalizar(f"❌ Erro: {str(e)}", "#FF0000"))

    def _finalizar(self, texto, cor):
        self.executando = False
        self.btn_iniciar.configure(state="normal")
        self.btn_parar.configure(state="disabled")
        self.lbl_status.configure(text=f"Status: {texto}", text_color=cor)

if __name__ == "__main__":
    app = HSFApp()
    app.mainloop()
