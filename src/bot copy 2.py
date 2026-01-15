import time
import logging
import os
import glob
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from src.config import Config

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DBAutomator:
    def __init__(self, headless=False):
        """
        Inicializa a automação com Playwright.
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        """Inicia o Playwright e o Browser."""
        logger.info("Inicializando Playwright...")
        self.playwright = sync_playwright().start()
        
        logger.info(f"Lançando navegador (Headless: {self.headless})...")
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--start-maximized"]
        )
        
        self.context = self.browser.new_context(viewport=None)
        self.page = self.context.new_page()

    def close(self):
        """Fecha o navegador."""
        if self.headless:
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()

    def step_1_access_login(self):
        """Acessa a página de login."""
        logger.info(f"Navegando para: {Config.BASE_URL_LOGIN}")
        self.page.goto(Config.BASE_URL_LOGIN)

    def step_2_first_auth(self):
        """Etapa 1: Serviço Solicitante."""
        try:
            self.page.wait_for_load_state("networkidle")
            input_selector = "input[placeholder*='Solicitante'], input[type='text']"
            self.page.wait_for_selector(input_selector, state="visible", timeout=15000)
            self.page.fill(input_selector, Config.SERVICE_CODE)
            self.page.click("button:has-text('Avançar')")
        except Exception as e:
            logger.error(f"Erro no Passo 2: {e}")
            raise

    def step_3_second_auth(self):
        """Etapa 2: CPF e Senha."""
        try:
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_selector("input[type='password']", state="visible", timeout=15000)
            password_input = self.page.locator("input[type='password']").first
            password_input.click()
            self.page.keyboard.press("Shift+Tab")
            time.sleep(0.5)
            self.page.keyboard.type(Config.CPF)
            self.page.keyboard.press("Tab")
            time.sleep(0.5)
            self.page.keyboard.type(Config.PASSWORD)
            self.page.click("button:has-text('Login'), button:has-text('Entrar')")
        except Exception as e:
            logger.error(f"Erro no Passo 3: {e}")
            try:
                with open("debug_page_step3.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                if self.page:
                    self.page.screenshot(path="debug_step3.png")
            except Exception as debug_err:
                logger.error(f"Falha ao gerar artefatos de debug do Passo 3: {debug_err}")
            raise

    def step_4_navigation(self):
        """Navegação para a tela de Pacientes."""
        try:
            self.page.wait_for_url(Config.BASE_URL_HOME, timeout=20000)
            id_selector = "[id*='NavItem_MeusPacientes']"
            if self.page.is_visible(id_selector):
                self.page.click(id_selector)
            else:
                self.page.goto(Config.BASE_URL_PATIENTS)
            
            self.page.wait_for_load_state("networkidle")
            logger.info("Página de pacientes carregada.")
        except Exception as e:
            logger.error(f"Erro na navegação: {e}")
            raise

    def step_5_filters(self):
        """Aplica filtro de Status 'Completo'."""
        try:
            dropdown_selector = "[id*='StatusDropdown']"
            self.page.wait_for_selector(dropdown_selector, state="visible")
            self.page.click(dropdown_selector)
            self.page.click("text=Completo")
            logger.info("Filtro Status: Completo aplicado.")
        except Exception as e:
            logger.error(f"Erro nos filtros: {e}")
            raise

    def step_6_select_today_and_xml(self):
        """
        Passo 7: Seleção de Datas (Ontem/Hoje) com suporte a virada de mês.
        """
        logger.info("Iniciando seleção de datas no Flatpickr...")
        try:
            today = datetime.today()
            yesterday = today - timedelta(days=1)
            
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            
            def selecionar_data_no_flatpickr(datepicker_id, data_alvo):
                mes_alvo_nome = meses[data_alvo.month - 1]
                label_alvo = f"{mes_alvo_nome} {data_alvo.day}, {data_alvo.year}"
                
                self.page.click(datepicker_id)
                time.sleep(0.5)

                # Captura o índice do mês atual exibido no calendário aberto
                mes_atual_idx = self.page.locator(".flatpickr-calendar.open .flatpickr-monthDropdown-months").first.input_value()
                
                # Se o mês aberto for diferente do alvo (ex: virada de mês), clica em voltar
                if int(mes_atual_idx) != (data_alvo.month - 1):
                    logger.info(f"Ajustando mês para {mes_alvo_nome}...")
                    self.page.click(".flatpickr-calendar.open .flatpickr-prev-month")
                    time.sleep(0.3)

                selector_dia = f".flatpickr-calendar.open span.flatpickr-day[aria-label='{label_alvo}']"
                self.page.wait_for_selector(selector_dia, state="visible", timeout=3000)
                self.page.click(selector_dia)
                logger.info(f"Data {label_alvo} selecionada.")

            # Seleciona as datas nos wrappers identificados
            selecionar_data_no_flatpickr("#b8-Datepicker", yesterday)
            selecionar_data_no_flatpickr("#b10-Datepicker", today)

            # Atualiza lista
            self.page.click("[id*='Btn_Pesquisar']")
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)

            # Marca Checkbox3 e clica XML
            self.page.click("#Checkbox3")
            self.page.click("[id*='BtnResultadoXML']")
            logger.info("Botão XML clicado.")

            # Validação do Download
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            self.validate_xml_download(download_dir)

        except Exception as e:
            logger.error(f"Erro na geração do XML: {e}")
            self.page.screenshot(path="debug_xml_error.png")
            raise

    def validate_xml_download(self, directory, timeout=30):
        """Monitora a pasta de downloads por novos arquivos XML."""
        logger.info(f"Aguardando arquivo XML em {directory}...")
        end_time = time.time() + timeout
        while time.time() < end_time:
            files = glob.glob(os.path.join(directory, "*.xml"))
            if files:
                latest_file = max(files, key=os.path.getmtime)
                if (time.time() - os.path.getmtime(latest_file)) < 60:
                    logger.info(f"Sucesso! XML baixado: {os.path.basename(latest_file)}")
                    return latest_file
            time.sleep(1)
        logger.warning("Aviso: O download do XML não foi detectado no tempo limite.")
        return None

    def run(self):
        """Execução do ciclo completo."""
        try:
            self.start()
            self.step_1_access_login()
            self.step_2_first_auth()
            self.step_3_second_auth()
            self.step_4_navigation()
            self.step_5_filters()
            self.step_6_select_today_and_xml()
            logger.info("Automação concluída com sucesso!")
        except Exception as e:
            logger.critical(f"Falha crítica: {e}")
        finally:
            # self.close() # Descomente para fechar o browser após o fim
            pass

if __name__ == "__main__":
    bot = DBAutomator(headless=False)
    bot.run()
