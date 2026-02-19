import time
import logging
import os
import glob
import shutil
import ctypes
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from src.config import Config
from src.separacao import separar_lote_xml
from src.decorators import retry_action

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DBAutomator:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def maximize_window(self):
        """Força a maximização da janela usando a API do Windows"""
        try:
            time.sleep(1) # Aguarda a janela aparecer
            user32 = ctypes.windll.user32
            # Tenta encontrar a janela pelo título parcial ou maximiza a janela ativa
            hwnd = user32.GetForegroundWindow()
            user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE = 3
            logger.info("Janela maximizada via Windows API (ctypes).")
        except Exception as e:
            logger.warning(f"Não foi possível maximizar via ctypes: {e}")

    def start(self):
        logger.info("Inicializando Playwright...")
        self.playwright = sync_playwright().start()
        # Adiciona args de tamanho também como fallback
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, 
            args=["--start-maximized", "--window-size=1920,1080"]
        )
        self.context = self.browser.new_context(viewport=None)
        self.page = self.context.new_page()
        
        # Força maximização
        self.maximize_window()

    def step_1_access_login(self):
        """Passo 1: Acesso ao Portal"""
        logger.info(f"Navegando para: {Config.BASE_URL_LOGIN}")
        self.page.goto(Config.BASE_URL_LOGIN)
        # logger.info("Aplicando Zoom de 75%...") - REMOVIDO
        # self.page.evaluate("document.body.style.zoom = '0.75'") - REMOVIDO

    def step_2_first_auth(self):
        """Passo 2: Primeira Autenticação (Serviço Solicitante)"""
        self.page.wait_for_load_state("networkidle")
        input_selector = "input[placeholder*='Solicitante'], input[name*='Solicitante'], input[type='text']"
        self.page.wait_for_selector(input_selector, state="visible")
        self.page.fill(input_selector, Config.SERVICE_CODE)
        self.page.click("button:has-text('Avançar')")

    def step_3_second_auth(self):
        """Passo 3: Segunda Autenticação (CPF e Senha)"""
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_selector("input[type='password']", state="visible")
        # Localiza o CPF via TAB conforme solicitado ou seletor direto
        password_input = self.page.locator("input[type='password']").first
        password_input.click()
        self.page.keyboard.press("Shift+Tab")
        time.sleep(0.5)
        self.page.keyboard.type(Config.CPF)
        self.page.keyboard.press("Tab")
        time.sleep(0.5)
        self.page.keyboard.type(Config.PASSWORD)
        self.page.click("button:has-text('Login'), button:has-text('Entrar')")

    def step_4_navigation(self):
        """Passo 4: Navegação Pós-Login com Tratamento de Elementos Ocultos"""
        logger.info("Aguardando carregamento da Home...")
        try:
            # Aguarda a URL de Home carregar totalmente
            self.page.wait_for_url(Config.BASE_URL_HOME, timeout=60000)
            # logger.info("Reaplicando Zoom de 75% na Home...") - REMOVIDO
            # self.page.evaluate("document.body.style.zoom = '0.75'") - REMOVIDO
            
            id_selector = "[id*='NavItem_MeusPacientes']"
            
            # Tenta esperar o elemento ficar visível (não apenas presente no HTML)
            try:
                self.page.wait_for_selector(id_selector, state="visible", timeout=6000)
                self.page.click(id_selector)
            except:
                logger.warning("Menu lateral não ficou visível. Forçando navegação direta...")
                self.page.goto(Config.BASE_URL_PATIENTS)
            
            self.page.wait_for_load_state("networkidle")
            logger.info("Página de pacientes acessada.")
        except Exception as e:
            logger.error(f"Erro na navegação: {e}")
            self.page.screenshot(path="erro_navegacao_home.png")
            raise

    @retry_action(max_retries=3, delay=2.0, exceptions=Exception)
    def step_5_filters_status(self):
        """Passo 5: Filtro de Status para 'Completo'"""
        logger.info("Selecionando filtro de Status: Completo")
        # ID fornecido pelo usuário: StatusDropdown
        dropdown_selector = "[id*='StatusDropdown']"
        try:
            self.page.wait_for_selector(dropdown_selector, state="visible")
            self.page.click(dropdown_selector)
            
            # Aguarda a opção aparecer e clica
            # Usando classe fornecida pelo usuário: dropdown-status-txt
            logger.info("Aguardando opção 'Completo'...")
            option_selector = ".dropdown-status-txt:has-text('Completo'), div[role='option']:has-text('Completo'), span:has-text('Completo')"
            
            self.page.wait_for_selector(option_selector, state="visible", timeout=5000)
            self.page.click(option_selector)
            
            time.sleep(1.0)
            logger.info("Filtro 'Completo' aplicado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao selecionar status 'Completo': {e}")
            self.page.screenshot(path="erro_filtro_status.png")
            raise 

    def step_6_adjust_date_de(self):
        """
        Passo 6: Ajuste atemporal com clique forçado, ajustado para retroagir 4 dias.
        """
        logger.info("Iniciando ajuste atemporal do calendário (HOJE)...")
        try:
            # 1. Cálculo: Hoje
            today = datetime.now()
            #target_date = today - timedelta(days=4)
            target_date = today
            
            meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            
            label_alvo = f"{meses_pt[target_date.month - 1]} {target_date.day}, {target_date.year}"
            index_mes_alvo = str(target_date.month - 1)
            
            logger.info(f"Alvo dinâmico (4 dias atrás): {label_alvo}")

            # 2. Localização e Ativação
            wrapper_id = "#b8-Datepicker"
            input_id = "Input_SelecioneDataDe"
            
            # Garante que o container está visível
            self.page.wait_for_selector(wrapper_id, state="visible")
            
            # Clique físico no input para garantir foco antes do teclado
            input_visivel = self.page.locator(f"{wrapper_id} input[role='combobox']")
            input_visivel.click() 
            time.sleep(0.5)

            # 3. Limpeza de segurança (API do componente)
            self.page.evaluate("(id) => { const el = document.getElementById(id); if (el && el._flatpickr) el._flatpickr.clear(); }", input_id)
            
            # 4. Tenta abrir via Teclado
            self.page.keyboard.press("ArrowDown")
            try:
                self.page.wait_for_selector(".flatpickr-calendar.open", state="visible", timeout=3000)
            except:
                logger.warning("Calendário não abriu com ArrowDown. Tentando clique no ícone...")
                input_visivel.click()
                self.page.wait_for_selector(".flatpickr-calendar.open", state="visible", timeout=10000)

            time.sleep(1.0) # Estabilização

            # 5. Sincronização de Ano e Mês
            self.page.keyboard.press("Control+ArrowUp") # Garante Ano Atual (assumindo que o calendário abre perto dele)
            time.sleep(0.5)

            # Navega até o mês correto
            for _ in range(12):
                mes_atual = self.page.evaluate("document.querySelector('.flatpickr-calendar.open .flatpickr-monthDropdown-months').value")
                if mes_atual == index_mes_alvo:
                    break
                self.page.keyboard.press("Control+ArrowRight")
                time.sleep(0.3)

            # 6. Seleção do Dia
            selector_dia = f".flatpickr-calendar.open span.flatpickr-day[aria-label='{label_alvo}']"
            
            if self.page.is_visible(selector_dia):
                logger.info(f"Elemento de dia encontrado: {label_alvo}. Clicando...")
                self.page.click(selector_dia)
            else:
                logger.warning(f"Label '{label_alvo}' não detectado. Usando estratégia de 'Enter' no dia focado (Hoje).")
                # Se for hoje, muitas vezes o calendário já foca no dia atual.
                self.page.keyboard.press("Enter")
            
            time.sleep(1.0)
            logger.info("Data 'DE' ajustada para HOJE com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao abrir/ajustar calendário: {e}")
            self.page.screenshot(path="debug_calendario_abertura.png")
            raise

    @retry_action(max_retries=3, delay=2.0, exceptions=Exception)
    def _click_checkbox_with_retry(self):
        """Tenta localizar e clicar no checkbox de exportação com retries."""
        possibles_selectors = [
            "#Checkbox3",
            "xpath=/html/body/div[1]/div/div/div[1]/div[1]/div[3]/div/div/div[2]/div/div[3]/div[1]/div/div[1]/span/input",
            "thead input[type='checkbox']",
            "input[title='Selecionar todos']",
            "table input[type='checkbox']:nth-child(1)",
            "input[id*='Checkbox']",
            ".OSFillParent input[type='checkbox']"
        ]
        
        for selector in possibles_selectors:
            try:
                if self.page.locator(selector).count() > 0 and self.page.is_visible(selector):
                    logger.info(f"Checkbox VISÍVEL encontrado: {selector}")
                    try:
                        self.page.click(selector, timeout=2000)
                    except:
                        self.page.evaluate(f'document.querySelector("{selector.replace("xpath=", "")}").click()')
                    
                    time.sleep(0.5)
                    loc = self.page.locator(selector).first
                    
                    if loc.is_checked():
                        logger.info(f"Checkbox CONFIRMADO como marcado: {selector}")
                        return True
                    else:
                        logger.warning(f"Clicou em {selector} mas status não mudou. Forçando JS...")
                        self.page.evaluate("""el => {
                            el.checked = true;
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('click', { bubbles: true }));
                        }""", loc.element_handle())
                        time.sleep(1.0)
                        if loc.is_checked():
                            logger.info("Checkbox marcado via JS.")
                            return True
            except Exception as e:
                logger.warning(f"Erro ao validar checkbox {selector}: {e}")
                continue
                
        # Se saiu do loop sem return True, falhou
        raise Exception("Não foi possível marcar nenhum checkbox de exportação após tentar todos os seletores.")

    @retry_action(max_retries=3, delay=2.0, exceptions=Exception)
    def _download_xml_with_retry(self):
        """Tenta realizar o download do XML usando múltiplas estratégias."""
        download_info = None
        strategies = [
            ("#BtnResultadoXML", "ID #BtnResultadoXML"),
            (lambda: self.page.get_by_role("button", name="Resultado XML").click(), "Texto 'Resultado XML'"),
            (lambda: self._strategy_menu_action(), "Menu de Ações")
        ]

        errors = []
        for strategy, name in strategies:
            try:
                logger.info(f"Tentando download via: {name}")
                with self.page.expect_download(timeout=10000) as download_info_ctx:
                    if isinstance(strategy, str):
                        self.page.click(strategy)
                    else:
                        strategy()
                download_info = download_info_ctx.value
                logger.info(f"Download iniciado via {name}.")
                break
            except Exception as e:
                logger.warning(f"Falha na estratégia '{name}': {e}")
                errors.append(f"{name}: {e}")

        if not download_info:
            raise Exception(f"Todas as estratégias de download falharam: {'; '.join(errors)}")

        # Processar arquivo
        path = download_info.path()
        logger.info(f"Arquivo baixado temporariamente em: {path}")
        
        subfolder = datetime.now().strftime('%Y%m')
        download_dir = os.path.join(os.getcwd(), subfolder)
        os.makedirs(download_dir, exist_ok=True)
        
        final_name = f"lote_exames_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        final_path = os.path.join(download_dir, final_name)
        download_info.save_as(final_path)
        logger.info(f"Download salvo em: {final_path}")
        
        if not self.validate_xml_download(final_path):
            raise Exception("Arquivo XML baixado é inválido ou vazio.")
            
        return final_path

    def _strategy_menu_action(self):
        """Helper para estratégia de menu (usado no download)."""
        first_row = self.page.locator("table tbody tr").first
        menu_btn = first_row.locator("a:has(.osui-inline-svg)").first
        if menu_btn.is_visible():
            menu_btn.click()
            try:
                self.page.get_by_text("Resultado XML", exact=False).click()
            except:
                self.page.locator("text=XML").click()
        else:
            raise Exception("Botão de menu não visível.")

    def step_7_search_and_download(self):
        """Passo 7: Pesquisa e Download do XML (Refatorado)"""
        logger.info("Iniciando Passo 7: Pesquisa e Download do XML...")
        
        # 1. Clicar em Pesquisar
        logger.info("Clicando no botão 'Pesquisar'...")
        try:
             self.page.click("[id*='Btn_Pesquisar']", timeout=5000)
        except:
             self.page.evaluate("document.querySelector(\"[id*='Btn_Pesquisar']\").click()")

        self.page.wait_for_load_state("networkidle")
        
        # 2. Verificar Resultados
        try:
            self.page.wait_for_selector("table", state="visible", timeout=10000)
            rows = self.page.locator("tbody tr")
            
            # Conta visual de linhas
            count = rows.count()
            
            if count == 0:
                logger.warning("Tabela sem linhas (tbody vazio).")
                return

            # Verifica texto da primeira linha para 'Nenhum registro'
            first_row_text = rows.first.inner_text().lower()
            if "nenhum registro" in first_row_text or "não encontrado" in first_row_text:
                logger.warning(f"Sistema retornou: '{first_row_text}'. Encerrando ciclo sem erros.")
                return

        except Exception as e:
             logger.warning(f"Tabela não encontrada ou estrutura diferente: {e}")
             if self.page.locator("text=Nenhum registro encontrado").is_visible():
                 logger.warning("Mensagem 'Nenhum registro encontrado' detectada fora da tabela.")
                 return
             self.page.screenshot(path="debug_tabela_nao_encontrada.png")
             return

        # 3. Marcar Checkbox (Com Retry)
        self._click_checkbox_with_retry()

        # 4. Download (Com Retry)
        try:
            final_path = self._download_xml_with_retry()
            
            # 5. Pós-processamento (Separação e Backup)
            logger.info("Iniciando separação automática do lote...")
            separar_lote_xml(final_path)
            
            current_year = datetime.now().strftime('%Y')
            backup_dir = os.path.join(os.getcwd(), current_year)
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy2(final_path, os.path.join(backup_dir, os.path.basename(final_path)))
            logger.info("Processo concluído com sucesso.")
            
        except Exception as e:
            logger.error(f"Erro fatal no processo de download/separação: {e}")
            self.page.screenshot(path="erro_download_xml.png")
            raise


    def validate_xml_download(self, file_path, timeout=30):
        """Valida se o arquivo XML foi baixado corretamente e não está vazio."""
        logger.info(f"Validando arquivo baixado: {file_path}...")
        
        if not file_path:
            logger.error("Caminho do arquivo é inválido (None).")
            return False

        end_time = time.time() + timeout
        while time.time() < end_time:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                if size > 0:
                    logger.info(f"Arquivo validado com sucesso ({size} bytes): {os.path.basename(file_path)}")
                    return file_path
                else:
                    logger.warning(f"Arquivo existe mas está vazio: {file_path}")
            time.sleep(1)
        
        logger.warning("Falha na validação: Arquivo não encontrado ou vazio após timeout.")
        return None

    def run(self):
        try:
            self.start()
            # 1 a 3: Login
            self.step_1_access_login()

            self.step_2_first_auth()

            self.step_3_second_auth()

            # 4: Navegação para Pacientes
            self.step_4_navigation()
            
            # 6: Ajuste da Data DE (Primeiro ajusta as datas conforme solicitado)
            self.step_6_adjust_date_de()
            logger.info("Aguardando 5 segundos...")
            time.sleep(5)
            
            # 5: Filtro de Status (Depois aplica o filtro de status 'Completo')
            self.step_5_filters_status()
            logger.info("Aguardando 5 segundos...")
            time.sleep(5)
            
            # 7: Pesquisa e Download
            # 7: Pesquisa e Download
            self.step_7_search_and_download()
            
            return True # Sucesso
            
        except Exception as e:
            logger.critical(f"Falha na automação: {e}")
            return False # Falha
        finally:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("Processo encerrado.")

if __name__ == "__main__":
    bot = DBAutomator(headless=False)
    bot.run()