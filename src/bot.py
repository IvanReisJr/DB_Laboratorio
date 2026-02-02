import time
import logging
import os
import glob
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from src.config import Config
from src.separacao import separar_lote_xml

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
        logger.info("Iniciando ajuste atemporal do calendário (retroagindo 4 dias)...")
        try:
            # 1. Cálculo: Retroage 4 dias
            today = datetime.now()
            target_date = today - timedelta(days=4)
            
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

    def step_7_search_and_download(self):
        """Passo 7: Pesquisa e Download do XML"""
        logger.info("Iniciando Passo 7: Pesquisa e Download do XML...")
        
        # ID fornecido: Btn_Pesquisar
        logger.info("Clicando no botão 'Pesquisar' (#Btn_Pesquisar)...")
        # Força clique JS para garantir
        try:
             self.page.click("[id*='Btn_Pesquisar']", timeout=5000)
        except:
             self.page.evaluate("document.querySelector(\"[id*='Btn_Pesquisar']\").click()")

        logger.info("Aguardando carregamento (networkidle)...")
        self.page.wait_for_load_state("networkidle")
        
        logger.info("Aguardando renderização da tabela de resultados...")
        try:
            self.page.wait_for_selector("table", state="visible", timeout=10000)
            logger.info("Tabela de resultados encontrada.")
            
            # Verificação de Conteúdo da Tabela
            rows = self.page.locator("tbody tr")
            # Aguarda um pouco para garantir que as linhas renderizaram (OutSystems pode renderizar a tabela e depois os dados)
            try:
                self.page.wait_for_selector("tbody tr", timeout=5000)
            except:
                pass # Pode ser que não tenha linhas mesmo
                
            count = rows.count()
            if count == 0:
                # Verifica se há mensagem de "Nenhum registro"
                if self.page.locator("text=Nenhum registro encontrado").is_visible():
                    logger.warning("Sistema retornou: 'Nenhum registro encontrado'. Encerrando passo.")
                    return
                else:
                    logger.warning("Tabela encontrada, mas com 0 linhas. Verifique se o filtro retornou dados.")
                    # Tira screenshot para evidência
                    self.page.screenshot(path="debug_tabela_vazia.png")
                    return # Não há o que baixar
            
            logger.info(f"Encontrados {count} registros na tabela.")
            
        except:
            logger.warning("Nenhuma tabela encontrada. Verificando se há resultados...")
            if self.page.locator("text=Nenhum registro encontrado").is_visible():
                logger.warning("Sistema retornou: 'Nenhum registro encontrado'.")
                return
            else:
                logger.warning("Tabela não apareceu e nenhuma mensagem de erro clara foi detectada.")
                self.page.screenshot(path="debug_tabela_nao_encontrada.png")
                return

        # Tenta localizar o checkbox com múltiplos seletores
        possibles_selectors = [
            "#Checkbox3",                                    # Prioridade máxima
            "xpath=/html/body/div[1]/div/div/div[1]/div[1]/div[3]/div/div/div[2]/div/div[3]/div[1]/div/div[1]/span/input",
            "thead input[type='checkbox']",
            "input[title='Selecionar todos']",
            "table input[type='checkbox']:nth-child(1)",
            "input[id*='Checkbox']",
            ".OSFillParent input[type='checkbox']"
        ]
        
        checkbox_found = False
        used_selector = None
        
        for selector in possibles_selectors:
            # logger.debug(f"Testando seletor: {selector}") # Reduzido para debug para limpar log
            try:
                # Usa verificação rápida sem esperar timeout de 30s se não existir
                if self.page.locator(selector).count() > 0 and self.page.is_visible(selector):
                    logger.info(f"Checkbox VSÍVEL encontrado: {selector}")
                    # Tenta clicar
                    try:
                        self.page.click(selector, timeout=2000)
                    except:
                        self.page.evaluate(f"document.querySelector('{selector.replace('xpath=', '')}').click()")
                    
                    time.sleep(0.5)
                    
                    # Validação
                    loc = self.page.locator(selector).first
                    if loc.is_checked():
                        logger.info(f"Checkbox CONFIRMADO como marcado: {selector}")
                        checkbox_found = True
                        used_selector = selector
                        break
                    else:
                        logger.warning(f"Clicou em {selector} mas status não mudou. Forçando JS...")
                        self.page.evaluate("el => el.checked = true", loc.element_handle())
                        time.sleep(0.5)
                        if loc.is_checked():
                            logger.info("Checkbox marcado via JS.")
                            checkbox_found = True
                            break
            except Exception as e_check:
                logger.warning(f"Erro ao validar checkbox {selector}: {e_check}")
                continue
                
        if checkbox_found:
            logger.info("Checkbox acionado. Iniciando processo de download...")
            # Lógica Robusta de Download
            download_initiated = False
            
            # Tentativa 1: Botão direto por ID (O mais comum)
            if not download_initiated:
                try:
                    logger.info("Tentativa 1: Clicando em #BtnResultadoXML...")
                    with self.page.expect_download(timeout=10000) as download_info:
                        self.page.click("#BtnResultadoXML")
                    download_initiated = True
                    logger.info("Download iniciado via #BtnResultadoXML.")
                except Exception as e:
                    logger.warning(f"Tentativa 1 falhou: {e}")

            # Tentativa 2: Botão por Texto (XML ou Resultado)
            if not download_initiated:
                try:
                    logger.info("Tentativa 2: Buscando botão por texto 'Resultado XML'...")
                    with self.page.expect_download(timeout=10000) as download_info:
                        self.page.get_by_role("button", name="Resultado XML").click()
                    download_initiated = True
                    logger.info("Download iniciado via Texto 'Resultado XML'.")
                except Exception as e:
                    logger.warning(f"Tentativa 2 falhou: {e}")

            # Tentativa 3: Menu de Ações (...)
            if not download_initiated:
                try:
                    logger.info("Tentativa 3: Buscando Menu de Ações (SVG) na primeira linha...")
                    # Localiza a primeira linha e busca o link que contem o SVG (Menu)
                    first_row = self.page.locator("table tbody tr").first
                    menu_btn = first_row.locator("a:has(.osui-inline-svg)").first
                    
                    if menu_btn.is_visible():
                        menu_btn.click()
                        logger.info("Menu aberto. Buscando opção 'XML'...")
                        # Aguarda o menu aparecer e clica em Resultado XML
                        # Tenta buscar por texto exato ou parcial
                        try:
                            with self.page.expect_download(timeout=10000) as download_info:
                                self.page.get_by_text("Resultado XML", exact=False).click()
                        except:
                             # Fallback dentro do menu: procurar qualquer coisa com XML
                             with self.page.expect_download(timeout=10000) as download_info:
                                self.page.locator("text=XML").click()

                        download_initiated = True
                        logger.info("Download iniciado via Menu de Ações.")
                    else:
                        logger.warning("Botão de menu (SVG) não encontrado na primeira linha.")
                except Exception as e:
                    logger.warning(f"Tentativa 3 falhou: {e}")

            if download_initiated:
                # Processamento do Download (Comum a todas as tentativas)
                try:
                    download = download_info.value
                    path = download.path()
                    logger.info(f"Arquivo baixado temporariamente em: {path}")
                    
                    # Nome do arquivo final
                    subfolder = datetime.now().strftime('%Y%m')
                    download_dir = os.path.join(os.getcwd(), subfolder)
                    os.makedirs(download_dir, exist_ok=True)
                    
                    final_name = f"lote_exames_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
                    final_path = os.path.join(download_dir, final_name)
                    
                    # Salva o arquivo
                    download.save_as(final_path)
                    logger.info(f"Download concluído: {final_path}")
                    
                    # Validação
                    if self.validate_xml_download(final_path):
                        logger.info("Arquivo XML validado com sucesso.")
                        
                        # Processamento Adicional: Separação
                        try:
                            logger.info("Iniciando separação automática do lote...")
                            separar_lote_xml(final_path)
                            logger.info("Separação concluída.")
                        except Exception as sep_err:
                            logger.error(f"Erro na separação do lote: {sep_err}")
                            
                    else:
                        logger.error("Falha na validação do arquivo XML.")
                        
                except Exception as dl_err:
                    logger.error(f"Erro ao salvar/processar o download: {dl_err}")
            else:
                logger.error("TODAS as tentativas de download falharam.")
        else:
            logger.warning("Nenhum checkbox de seleção encontrado com os seletores testados.")
            self.page.screenshot(path="debug_step7_checkbox_not_found.png")
            
            # Dump do HTML da tabela para análise se falhar tudo
            try:
                html_content = self.page.content()
                with open("debug_page_source.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("Dump da página salvo em debug_page_source.html para análise.")
            except:
                pass


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
            self.step_7_search_and_download()
            
        except Exception as e:
            logger.critical(f"Falha na automação: {e}")
        finally:
            logger.info("Processo encerrado.")

if __name__ == "__main__":
    bot = DBAutomator(headless=False)
    bot.run()