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
            args=["--start-maximized"]  # Tenta maximizar (funciona melhor com viewport definido)
        )
        
        # Cria contexto e página
        # O viewport None permite que a janela use o tamanho total disponível
        self.context = self.browser.new_context(viewport=None)
        self.page = self.context.new_page()

    def close(self):
        """Fecha o navegador e encerra a sessão."""
        # Só fecha automaticamente em modo headless; em modo visual deixa aberto para inspeção
        if self.headless:
            if self.context:
                self.context.close()
            if self.browser:
                logger.info("Encerrando navegador.")
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

    def step_1_access_login(self):
        """Acessa a página de login."""
        logger.info(f"Navegando para: {Config.BASE_URL_LOGIN}")
        self.page.goto(Config.BASE_URL_LOGIN)

    def step_2_first_auth(self):
        """
        Primeira etapa de autenticação: Serviço Solicitante.
        """
        logger.info("Iniciando Etapa 1: Serviço Solicitante")
        try:
            # Aguarda a rede ficar ociosa para garantir que o React carregou (página SPA)
            logger.info("Aguardando carregamento da aplicação (Network Idle)...")
            self.page.wait_for_load_state("networkidle")
            
            # Tenta encontrar input - Estratégia Genérica para OutSystems/React
            # Muitas vezes o input tem um ID dinâmico, mas labels ou placeholders costumam ser estáveis.
            # Se placeholder falhar, tentamos pegar o primeiro input visível da tela de login.
            logger.info("Buscando campo de Serviço Solicitante...")
            
            # Seletor combinando várias possibilidades
            input_selector = "input[placeholder*='Solicitante'], input[name*='Solicitante'], input[type='text']"
            
            # Espera explícita pelo seletor estar visível na tela
            self.page.wait_for_selector(input_selector, state="visible", timeout=15000)
            
            # Se houver mais de um, precisamos ser mais específicos. 
            # Vamos tentar preencher o primeiro input de texto encontrado se o placeholder específico falhar.
            if self.page.is_visible("input[placeholder*='Solicitante']"):
                self.page.fill("input[placeholder*='Solicitante']", Config.SERVICE_CODE)
            else:
                 # Fallback: Preenche o primeiro input de texto visível na página
                 logger.warning("Placeholder específico não encontrado. Tentando primeiro input visível.")
                 self.page.fill("input[type='text']", Config.SERVICE_CODE)

            logger.info(f"Código de serviço inserido: {Config.SERVICE_CODE}")

            # Botão Avançar
            logger.info("Buscando botão Avançar...")
            self.page.click("button:has-text('Avançar'), input[value='Avançar'], div[role='button']:has-text('Avançar')")
            logger.info("Botão 'Avançar' clicado.")
            
        except Exception as e:
            logger.error(f"Erro na primeira autenticação: {e}")
            # Debug: Salvar HTML para análise
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            logger.info("HTML da página salvo em debug_page.html para análise.")
            raise

    def step_3_second_auth(self):
        """
        Segunda etapa de autenticação: CPF e Senha.
        """
        logger.info("Iniciando Etapa 2: CPF e Senha")
        try:
            # Aguarda a transição de tela
            # Às vezes o clique no "Avançar" dispara uma requisição AJAX que altera o DOM.
            logger.info("Aguardando carregamento da etapa 2...")
            self.page.wait_for_load_state("networkidle")
            
            # Tenta localizar campo CPF
            # Estratégia: O campo CPF geralmente aparece após o Avançar.
            # Se não tiver placeholder, vamos tentar pelo tipo tel/text ou pela ordem (segundo input, se o primeiro for hidden ou disabled)
            logger.info("Buscando campo CPF...")
            
            cpf_selector = "input[placeholder*='CPF'], input[name*='CPF'], input[name*='Usuario'], input[type='tel']"
            
            try:
                self.page.wait_for_selector(cpf_selector, state="visible", timeout=10000)
                self.page.fill(cpf_selector, Config.CPF)
            except:
                logger.warning("Seletor específico de CPF falhou. Tentando encontrar o primeiro input visível e habilitado.")
                # Tenta pegar o primeiro input visível que não seja o que já preenchemos (se ainda estiver lá)
                # Ou limpa e preenche o input ativo
                visible_inputs = self.page.locator("input:visible:not([disabled])")
                count = visible_inputs.count()
                if count > 0:
                     # Assume que é o primeiro input disponível nesta nova etapa
                     visible_inputs.first.fill(Config.CPF)
                else:
                    raise Exception("Nenhum input visível encontrado para CPF.")
            
            logger.info("CPF inserido.")

            # Simular TAB conforme solicitado
            logger.info("Simulando tecla TAB...")
            self.page.keyboard.press("Tab")
            
            # Pequena pausa para garantir UI update
            time.sleep(0.5)

            # Inserir Senha
            logger.info("Inserindo Senha...")
            # Verifica se o foco foi para um campo de senha
            focused_type = self.page.evaluate("document.activeElement.type")
            
            if focused_type == "password":
                logger.info("Campo de senha detectado via foco (TAB).")
                self.page.keyboard.type(Config.PASSWORD)
            else:
                logger.warning(f"TAB focou elemento tipo '{focused_type}'. Buscando campo password explicitamente.")
                # Tenta preencher campo password explicitamente
                if self.page.is_visible("input[type='password']"):
                    self.page.fill("input[type='password']", Config.PASSWORD)
                else:
                    # Caso extremo: o campo senha pode ser um input text mascarado (raro, mas acontece)
                    # Ou talvez precise de mais um TAB?
                    logger.info("Campo password não encontrado. Tentando mais um TAB...")
                    self.page.keyboard.press("Tab")
                    self.page.keyboard.type(Config.PASSWORD)

            logger.info("Senha inserida.")

            # Botão Login
            logger.info("Clicando em Login...")
            # Tenta vários seletores de botão de login
            self.page.click("button:has-text('Login'), button:has-text('Entrar'), input[value='Entrar'], div[role='button']:has-text('Entrar')")
            logger.info("Botão 'Fazer Login' clicado.")

        except Exception as e:
            logger.error(f"Erro na segunda autenticação: {e}")
            # Debug: Salvar HTML para análise
            with open("debug_page_step2.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            logger.info("HTML da página salvo em debug_page_step2.html para análise.")
            raise

    def step_4_navigation(self):
        """
        Navegação Pós-Login.
        """
        logger.info("Aguardando carregamento da Home...")
        try:
            # Aguarda URL mudar para Home e rede estabilizar
            self.page.wait_for_url(Config.BASE_URL_HOME, timeout=20000)
            self.page.wait_for_load_state("networkidle")
            logger.info("Home carregada com sucesso.")

            # Tenta clicar no botão "Meus pacientes" usando o ID sugerido
            # Usamos match parcial (*=) para garantir que funcione mesmo se o prefixo bX- mudar.
            # ID alvo: b7-LK_MeusPacientes
            logger.info("Tentando clicar em 'Meus pacientes' pelo ID...")
            
            # Seletor: qualquer elemento cujo ID termine com 'LK_MeusPacientes' ou contenha 'MeusPacientes'
            id_selector = "[id*='LK_MeusPacientes'], [id*='NavItem_MeusPacientes']"
            
            if self.page.is_visible(id_selector):
                self.page.click(id_selector)
                logger.info("Clique realizado com sucesso via ID.")
            else:
                logger.warning("Botão não visível (menu fechado?). Navegando diretamente pela URL.")
                # Fallback: Navegação Direta via URL
                target_url = Config.BASE_URL_PATIENTS
                logger.info(f"Navegando diretamente para: {target_url}")
                self.page.goto(target_url)
            
            # Aguardar redirecionamento/carregamento da página de pacientes
            logger.info("Aguardando página de pacientes...")
            self.page.wait_for_url("**/Portal/MeusPacientes**", timeout=20000)
            self.page.wait_for_load_state("networkidle")
            logger.info("Página de pacientes carregada.")

        except Exception as e:
            logger.error(f"Erro na navegação pós-login: {e}")
            # Debug: Salvar HTML para análise
            with open("debug_page_step4.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            raise

    def step_5_filters(self):
        """
        Aplicação de Filtros.
        """
        logger.info("Aplicando filtros...")
        try:
            # Dropdown Customizado (informação fornecida pelo usuário)
            # ID: StatusDropdown
            # Opção alvo: Texto "Completo" (provavelmente class="dropdown-status-txt")
            
            logger.info("Buscando Dropdown de Status...")
            
            # Seletor do dropdown (container ou botão que abre)
            dropdown_selector = "[id*='StatusDropdown']"
            
            # Clicar para expandir
            if self.page.is_visible(dropdown_selector):
                logger.info("Clicando no dropdown para expandir...")
                self.page.click(dropdown_selector)
            else:
                # Fallback: tenta achar por texto se o ID falhar
                logger.info("ID exato não visível, tentando encontrar label 'Status'...")
                self.page.click("text=Status")

            # Aguarda as opções aparecerem
            # A opção tem o texto "Completo". Pode ser um <li>, <div> ou <span>.
            logger.info("Selecionando opção 'Completo'...")
            
            # Seletor genérico para o item da lista
            option_selector = "text=Completo"
            
            # Espera a opção estar visível
            self.page.wait_for_selector(option_selector, state="visible", timeout=5000)
            self.page.click(option_selector)

            logger.info("Filtro 'Completo' selecionado.")

            # Passo 6: clicar no botão Pesquisar (id="Btn_Pesquisar")
            logger.info("Clicando no botão Pesquisar...")
            search_button_selector = "[id='Btn_Pesquisar'], [id*='Btn_Pesquisar']"
            self.page.wait_for_selector(search_button_selector, state="visible", timeout=5000)
            self.page.click(search_button_selector)
            logger.info("Botão Pesquisar clicado.")

        except Exception as e:
            logger.error(f"Erro ao aplicar filtros: {e}")
            # Debug
            with open("debug_page_step5.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            raise

    def step_6_select_today_and_xml(self):
        """
        Passo 7: Selecionar intervalo de datas (ontem até hoje) e clicar em XML.
        """
        logger.info("Iniciando seleção de intervalo de datas (Ontem/Hoje) com preenchimento via teclado...")
        try:
            today = datetime.today()
            yesterday = today - timedelta(days=1)
            today_str = today.strftime("%d/%m/%Y")
            yesterday_str = yesterday.strftime("%d/%m/%Y")
            logger.info(f"Intervalo alvo: De {yesterday_str} até {today_str}")

            def set_calendar_date(selector, value):
                self.page.wait_for_selector(selector, state="visible", timeout=10000)
                el = self.page.locator(selector).first
                el.click()
                self.page.keyboard.press("ArrowDown")
                self.page.keyboard.press("Control+A")
                self.page.keyboard.type(value)
                self.page.keyboard.press("Enter")

            logger.info("Definindo data 'De' (b8-Datepicker) para ontem...")
            set_calendar_date("#b8-Datepicker", yesterday_str)

            logger.info("Definindo data 'Até' (b10-Datepicker) para hoje...")
            set_calendar_date("#b10-Datepicker", today_str)

            # Clicar em Pesquisar para atualizar a lista com as novas datas
            logger.info("Clicando no botão Pesquisar para atualizar lista...")
            search_button_selector = "[id='Btn_Pesquisar'], [id*='Btn_Pesquisar']"
            self.page.wait_for_selector(search_button_selector, state="visible", timeout=10000)
            self.page.click(search_button_selector)
            
            logger.info("Aguardando atualização da lista...")
            self.page.wait_for_load_state("networkidle")
            # Aguarda um pouco mais para garantir renderização da grid
            time.sleep(3)

            checkbox_selector = "[id='Checkbox3'], [id*='Checkbox3']"
            logger.info("Marcando Checkbox3...")
            self.page.wait_for_selector(checkbox_selector, state="visible", timeout=10000)
            self.page.click(checkbox_selector)
            logger.info("Checkbox3 marcado.")

            logger.info("Clicando no botão XML...")
            xml_button_selector = "[id='BtnResultadoXML'], [id*='BtnResultadoXML']"
            self.page.wait_for_selector(xml_button_selector, state="visible", timeout=10000)
            self.page.click(xml_button_selector)
            logger.info("Botão XML clicado.")

            # Validação do Download
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            self.validate_xml_download(download_dir)

        except Exception as e:
            logger.error(f"Erro na seleção de registro e XML: {e}")
            # Debug: Salvar HTML para análise
            with open("debug_page_step6.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
            raise

    def validate_xml_download(self, directory, timeout=30):
        """
        Monitora o diretório e retorna o caminho do arquivo XML se ele for baixado.
        """
        logger.info(f"Aguardando download do XML em: {directory}...")
        
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            # Lista arquivos .xml
            files = glob.glob(os.path.join(directory, "*.xml"))
            
            if files:
                # Pega o mais recente
                latest_file = max(files, key=os.path.getmtime)
                
                # Verifica se foi modificado nos últimos 60 segundos
                if (time.time() - os.path.getmtime(latest_file)) < 60:
                    logger.info(f"Sucesso! Arquivo XML detectado: {latest_file}")
                    return latest_file
            
            time.sleep(1)
        
        logger.error("Timeout: O arquivo XML não foi detectado após o clique.")
        return None

    def run(self):
        """Executa o fluxo completo."""
        try:
            self.start()
            self.step_1_access_login()
            self.step_2_first_auth()
            self.step_3_second_auth()
            self.step_4_navigation()
            self.step_5_filters()
            self.step_6_select_today_and_xml()
        except Exception as e:
            logger.critical(f"O fluxo foi interrompido devido a um erro: {e}")
            # Tira screenshot do erro
            if self.page:
                self.page.screenshot(path="error_screenshot.png")
                logger.info("Screenshot de erro salvo como error_screenshot.png")
