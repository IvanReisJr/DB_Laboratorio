import time
import logging
import os
import glob
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from src.config import Config

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DBAutomator:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        logger.info("Inicializando Playwright...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless, args=["--start-maximized"])
        self.context = self.browser.new_context(viewport=None)
        self.page = self.context.new_page()

    def step_1_access_login(self):
        """Passo 1: Acesso ao Portal"""
        logger.info(f"Navegando para: {Config.BASE_URL_LOGIN}")
        self.page.goto(Config.BASE_URL_LOGIN)

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

    def step_5_filters_status(self):
        """Passo 5: Filtro de Status para 'Completo'"""
        logger.info("Selecionando filtro de Status: Completo")
        dropdown_selector = "[id*='StatusDropdown']"
        try:
            self.page.wait_for_selector(dropdown_selector, state="visible")
            self.page.click(dropdown_selector)
            
            # Aguarda a opção aparecer e clica
            # Usando locator com verificação de visibilidade
            option_locator = self.page.locator("div[role='option']:has-text('Completo'), span:has-text('Completo'), div:has-text('Completo')").first
            option_locator.wait_for(state="visible", timeout=5000)
            option_locator.click()
            
            time.sleep(1.0)
            logger.info("Filtro 'Completo' aplicado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao selecionar status 'Completo': {e}")
            self.page.screenshot(path="erro_filtro_status.png")
            raise 

    def step_6_adjust_date_de(self):
        """
        Passo 6: Ajuste atemporal com clique forçado para garantir abertura do calendário.
        """
        logger.info("Iniciando ajuste atemporal do calendário com clique de ativação...")
        try:
            # 1. Cálculo dinâmico (Sysdate)
            today = datetime.now()
            #esterday = today - timedelta(days=2)
            yesterday = today - timedelta(days=5)
            meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            
            label_alvo = f"{meses_pt[yesterday.month - 1]} {yesterday.day}, {yesterday.year}"
            index_mes_alvo = str(yesterday.month - 1)
            
            logger.info(f"Alvo dinâmico: {label_alvo}")

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
            
            # 4. Tenta abrir via Teclado, se não abrir em 2s, clica no ícone do calendário
            self.page.keyboard.press("ArrowDown")
            
            try:
                # Espera curta para verificar se abriu via teclado
                self.page.wait_for_selector(".flatpickr-calendar.open", state="visible", timeout=3000)
            except:
                logger.warning("Calendário não abriu com ArrowDown. Tentando clique no ícone...")
                # Clica no input novamente ou no wrapper para forçar
                input_visivel.click()
                self.page.wait_for_selector(".flatpickr-calendar.open", state="visible", timeout=10000)

            time.sleep(1.0) # Estabilização

            # 5. Sincronização de Ano e Mês (Ctrl + Setas)
            self.page.keyboard.press("Control+ArrowUp") # Garante 2026
            time.sleep(0.5)

            for _ in range(12):
                mes_atual = self.page.evaluate("document.querySelector('.flatpickr-calendar.open .flatpickr-monthDropdown-months').value")
                if mes_atual == index_mes_alvo:
                    break
                self.page.keyboard.press("Control+ArrowRight")
                time.sleep(0.3)

            # 6. Seleção do Dia Anterior
            # Primeiro tenta localizar o elemento exato pelo label calculado
            selector_dia = f".flatpickr-calendar.open span.flatpickr-day[aria-label='{label_alvo}']"
            
            if self.page.is_visible(selector_dia):
                logger.info(f"Elemento encontrado: {label_alvo}. Clicando...")
                self.page.click(selector_dia)
            else:
                logger.warning(f"Label '{label_alvo}' não detectado. Usando navegação por setas (ArrowLeft).")
                self.page.keyboard.press("ArrowLeft")
                time.sleep(0.5)
                self.page.keyboard.press("Enter")
            
            time.sleep(1.0)
            logger.info("Data 'DE' ajustada com sucesso.")

        except Exception as e:
            logger.error(f"Erro ao abrir/ajustar calendário: {e}")
            self.page.screenshot(path="debug_calendario_abertura.png")
            raise

    def step_7_search_and_download(self):
        """Passo 7: Pesquisa e Download do XML"""
        logger.info("Iniciando Passo 7: Pesquisa e Download do XML...")
        
        logger.info("Clicando no botão 'Pesquisar' (#Btn_Pesquisar)...")
        self.page.click("#Btn_Pesquisar")
        
        logger.info("Aguardando carregamento (networkidle)...")
        self.page.wait_for_load_state("networkidle")
        
        logger.info("Aguardando 3 segundos para renderização da grid...")
        time.sleep(3.0) 

        # Tenta localizar o checkbox (pode ser Checkbox3 ou outro ID dinâmico)
        # Checkbox3 costuma ser o "Selecionar Todos" no header da grid
        checkbox_selector = "input[type='checkbox'][id*='Checkbox3']" 
        logger.info(f"Verificando visibilidade do checkbox com seletor: {checkbox_selector}")
        
        try:
            # Força espera pelo checkbox se a tabela carregou
            if self.page.locator("table").count() > 0:
                 self.page.wait_for_selector(checkbox_selector, state="attached", timeout=5000)

            if self.page.is_visible(checkbox_selector):
                logger.info("Checkbox encontrado. Tentando clicar...")
                
                # Tenta clicar no input direto
                try:
                    self.page.click(checkbox_selector, timeout=2000)
                except:
                    # Se falhar (ex: coberto por label), clica via JS ou no pai
                    logger.warning("Clique direto falhou. Tentando via JS...")
                    self.page.evaluate(f"document.querySelector('{checkbox_selector}').click()")
                
                logger.info("Iniciando processo de download (clicando em #BtnResultadoXML)...")
                with self.page.expect_download(timeout=60000) as download_info:
                    self.page.click("[id*='BtnResultadoXML']")
                
                download = download_info.value
                path = os.path.join(os.path.expanduser("~"), "Downloads", download.suggested_filename)
                logger.info(f"Salvando arquivo em: {path}")
                download.save_as(path)
                logger.info(f"Download salvo com sucesso.")
                
                # Validação extra do arquivo
                self.validate_xml_download(os.path.join(os.path.expanduser("~"), "Downloads"))
            else:
                logger.warning("Checkbox não visível. Verifique se a pesquisa retornou resultados.")
                self.page.screenshot(path="debug_step7_sem_registros.png")
                
        except Exception as e:
            logger.warning(f"Erro ao tentar selecionar checkbox: {e}")
            self.page.screenshot(path="erro_selecao_checkbox.png")


    def validate_xml_download(self, directory, timeout=30):
        """Valida se o arquivo XML realmente chegou na pasta."""
        logger.info(f"Validando existência do arquivo em: {directory}...")
        end_time = time.time() + timeout
        while time.time() < end_time:
            files = glob.glob(os.path.join(directory, "*.xml"))
            if files:
                latest_file = max(files, key=os.path.getmtime)
                if (time.time() - os.path.getmtime(latest_file)) < 60:
                    logger.info(f"Arquivo validado com sucesso: {os.path.basename(latest_file)}")
                    return latest_file
            time.sleep(1)
        logger.warning("Aviso: Arquivo não detectado na validação pós-download.")
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
            
            # 5: Filtro de Status (Depois aplica o filtro de status 'Completo')
            self.step_5_filters_status()
            
            # 7: Pesquisa e Download
            self.step_7_search_and_download()
            
        except Exception as e:
            logger.critical(f"Falha na automação: {e}")
        finally:
            logger.info("Processo encerrado.")

if __name__ == "__main__":
    bot = DBAutomator(headless=False)
    bot.run()