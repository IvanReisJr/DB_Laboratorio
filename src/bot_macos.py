import streamlit as st
import threading
import logging
import time
import queue
import sys
import os
from src.bot import DBAutomator

# Configure logging to capture output seamlessly
class QueueHandler(logging.Handler):
    """Handler that sends log records to a queue."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

# Initialize session state for logs and control
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = queue.Queue()
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'running' not in st.session_state:
    st.session_state.running = False
if 'stop_event' not in st.session_state:
    st.session_state.stop_event = threading.Event()

def run_bot():
    """Function to run the bot in a separate thread."""
    try:
        # Reset logger to capture output
        root_logger = logging.getLogger()
        # Remove existing handlers to avoid duplication if re-run
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Add QueueHandler
        queue_handler = QueueHandler(st.session_state.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        queue_handler.setFormatter(formatter)
        root_logger.addHandler(queue_handler)
        root_logger.setLevel(logging.INFO)

        st.session_state.log_queue.put("🚀 Iniciando automação...")
        
        # Initialize and Run Bot
        bot = DBAutomator(headless=False)
        # Note: Ideally bot should check stop_event internally for graceful shutdown
        success = bot.run()
        
        if success:
            st.session_state.log_queue.put("✅ Automação concluída com sucesso!")
        else:
            st.session_state.log_queue.put("❌ Automação finalizada com erros.")
            
    except Exception as e:
        st.session_state.log_queue.put(f"🔥 Erro fatal: {str(e)}")
    finally:
        st.session_state.running = False
        st.rerun()

# --- Interface Layout ---
st.set_page_config(page_title="DB Laboratório Automator", page_icon="🤖", layout="wide")

st.title("🤖 DB Laboratório Automator (macOS)")
st.markdown("---")

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Controles")
    if not st.session_state.running:
        if st.button("▶️ Iniciar Automação", type="primary", use_container_width=True):
            st.session_state.running = True
            st.session_state.logs = [] # Clear logs on new run
            st.session_state.stop_event.clear()
            threading.Thread(target=run_bot, daemon=True).start()
            st.rerun()
    else:
        st.info("⚠️ Executando...")
        # Streamlit doesn't support easy thread killing, so we disable the button
        if st.button("⏹️ Parar (Indisponível)", disabled=True, use_container_width=True):
            pass

    st.markdown("### Configuração")
    st.caption("Ajustes rápidos podem ser feitos no `.env`.")
    st.code(open(".env").read(), language="bash")

with col2:
    st.subheader("Logs em Tempo Real")
    log_container = st.container(height=500, border=True)
    
    # Process Logs from Queue
    while not st.session_state.log_queue.empty():
        msg = st.session_state.log_queue.get()
        st.session_state.logs.append(msg)
    
    # Render Logs
    if st.session_state.logs:
        log_text = "\n".join(st.session_state.logs)
        log_container.code(log_text, language="log")
    else:
        log_container.info("Aguardando início dos logs...")

    # Auto-refresh if running
    if st.session_state.running:
        time.sleep(1)
        st.rerun()
