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
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        logger.info("Inicializando Playwright...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=["--start-maximized"]
        )
        self.context = self.browser.new_context(viewport=None)
        self.page = self.context.new_page()

    def close(self):
        if self.headless:
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()

    def step_1_access_login(self):
        logger.info(f"Navegando para: {Config.BASE_URL_LOGIN}")
        self.page.goto(Config.BASE_URL_LOGIN)

    def step_2_first_auth(self):
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
            raise

    def step_4_navigation(self):
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
        Passo 7: Seleção de Datas via preenchimento direto (Bypass readonly).
        Solução definitiva para evitar navegação manual em calendários.
        """
        logger.info("Iniciando seleção de datas via preenchimento direto...")
        try:
            today = datetime.today()
            yesterday = today - timedelta(days=1)
            
            # Datas formatadas para o padrão do sistema (dd/mm/yyyy)
            today_str = today.strftime("%d/%m/%Y")
            yesterday_str = yesterday.strftime("%d/%m/%Y")

            def force_input_date(input_id, date_value):
                # 1. Localiza o input real (visto no HTML das imagens enviadas)
                # Note: Nas imagens, o input date tem aria-hidden="true" e o visível é o readonly
                selector = f"input{input_id}"
                
                # 2. Remove o atributo 'readonly' via JS para permitir escrita
                self.page.evaluate(f"""
                    let el = document.querySelector("{selector}");
                    el.removeAttribute("readonly");
                    el.value = "{date_value}";
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                """)
                
                # 3. Garante o foco e pressiona Enter para o sistema processar a data
                self.page.focus(selector)
                self.page.keyboard.press("Enter")
                logger.info(f"Data {date_value} injetada com sucesso em {input_id}")

            # Preenchimento direto usando os IDs dos inputs das imagens
            force_input_date("#Input_SelecioneDataDe", yesterday_str)
            force_input_date("#Input_SelecioneDataAte", today_str)

            # Atualiza lista
            logger.info("Filtrando resultados...")
            self.page.click("#Btn_Pesquisar")
            self.page.wait_for_load_state("networkidle")
            time.sleep(3) # Tempo para a grid carregar após o filtro

            # Checkbox Geral (Checkbox3)
            self.page.wait_for_selector("#Checkbox3", state="visible")
            self.page.click("#Checkbox3")

            # Botão XML
            logger.info("Clicando no botão XML...")
            self.page.click("[id*='BtnResultadoXML']")
            
            # Validação do Download
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            self.validate_xml_download(download_dir)

        except Exception as e:
            logger.error(f"Erro na geração do XML: {e}")
            self.page.screenshot(path="debug_xml_error.png")
            raise

    def validate_xml_download(self, directory, timeout=30):
        logger.info(f"Aguardando download em: {directory}...")
        end_time = time.time() + timeout
        while time.time() < end_time:
            files = glob.glob(os.path.join(directory, "*.xml"))
            if files:
                latest_file = max(files, key=os.path.getmtime)
                if (time.time() - os.path.getmtime(latest_file)) < 60:
                    logger.info(f"Sucesso! Arquivo XML: {os.path.basename(latest_file)}")
                    return latest_file
            time.sleep(1)
        logger.warning("Download não detectado no prazo.")
        return None

    def run(self):
        try:
            self.start()
            self.step_1_access_login()
            self.step_2_first_auth()
            self.step_3_second_auth()
            self.step_4_navigation()
            self.step_5_filters()
            self.step_6_select_today_and_xml()
        except Exception as e:
            logger.critical(f"Falha: {e}")
        finally:
            # self.close()
            pass

if __name__ == "__main__":
    bot = DBAutomator(headless=False)
    bot.run()