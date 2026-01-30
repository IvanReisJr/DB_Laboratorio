from django.shortcuts import render, redirect # Mantenha render e adicione redirect
from datetime import date, timedelta, datetime, timezone
import oracledb # Alterado de cx_Oracle para oracledb
import base64
import os
from striprtf.striprtf import rtf_to_text # Importar a função de conversão
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # Importar Paginator
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings # Para acessar BASE_DIR
from django.apps import apps # Para encontrar o caminho do app
from pathlib import Path # Adicionado para manipulação de caminhos
import os # Adicionado para manipulação de caminhos
from io import BytesIO
from itertools import groupby

"""
#comandos para iniciar o projeto:

Set-ExecutionPolicy Unrestricted -Scope Process

python -m venv venv

cd hsf_plataforma_pep_exames   

.\venv\Scripts\activate

#esse site é inicializado SEM CERTIFICADO:
python manage.py runserver     
python manage.py runserver 0.0.0.0:8000
python manage.py runserver_plus 0.0.0.0:8000

COM CERTIFICADO:
python manage.py runserver_plus --cert-file localhost+3.pem --key-file localhost+3-key.pem 0.0.0.0:8000

Agora você pode acessar sua aplicação no navegador usando HTTPS e o IP da sua máquina ou localhost:

https://localhost:8000/
https://127.0.0.1:8000/
https://192.168.101.44:8000/ (de outras máquinas na rede)


Paciente:
ANITA LUIZA DE PAULA DA SILVA OLIVEIRA
cpf: 11114023701
prontuario: 269569
codigo pessoa fisica: 15626


Vamos analisar função por função:

1) index_view(request):
O que faz? 
É a sua porta de entrada, a tela de login.
Como funciona? 
Se a requisição for um GET (primeiro acesso à página), ela simplesmente 
mostra o template index.html. Se for um POST (o usuário enviou o formulário de login), ela pega o username (prontuário) и password (código da pessoa), chama a função authenticate_cd_pesssoa_fisica para validar as credenciais e, em caso de sucesso, redireciona o usuário para a lista de exames (lista_exames_view). Em caso de falha, exibe uma mensagem de erro na própria página de login.
Observação: O uso do redirect após um POST bem-sucedido é uma excelente prática, conhecida como padrão Post/Redirect/Get (PRG). Isso evita que o formulário seja reenviado caso o usuário atualize a página.

2) authenticate_cd_pesssoa_fisica(username, password):
O que faz? 
Valida as credenciais do usuário diretamente no banco de dados Oracle.
Como funciona? 
Ela abre uma nova conexão com o Oracle, executa uma query SQL para verificar 
se existe um paciente com o prontuário e o código fornecidos, e retorna os dados do usuário ou None.

Boas Práticas: Você está usando queries parametrizadas 
(cursor.execute(sql, params)). Isso é excelente e fundamental, 
pois previne ataques de SQL Injection.

3) fetch_exames_por_pessoa_fisica(...) e fetch_exame_especifico(...):
O que fazem? 
São as funções responsáveis por buscar os dados dos exames no banco. 
Uma busca a lista completa e a outra busca um exame específico (usado para o PDF individual).
Como funcionam? 
Assim como a autenticação, abrem uma conexão, executam uma query complexa 
com vários JOINs para coletar todas as informações e as retornam como uma lista de dicionários.

Ponto Chave: A conversão do campo RESULTADO de RTF para texto puro usando striprtf 
é uma parte crucial da sua lógica de negócio e está bem implementada aqui.

4) lista_exames_view(request, cd_pessoa_fisica):
O que faz? 
Mostra os exames do paciente, mas de uma forma inteligente: agrupados por data de coleta.
Como funciona? 
Ela chama fetch_exames_por_pessoa_fisica, depois usa a função groupby do itertools para 
agrupar os exames pela data. Em seguida, usa o Paginator do Django para exibir esses 
grupos em páginas, o que melhora muito a performance e a usabilidade para pacientes com muitos exames.

5) visualizar_exames_por_data_view(...) e imprimir_exames_por_data_view(...):
O que fazem? 
A primeira mostra uma lista detalhada de todos os exames de um dia específico. 
A segunda pega essa mesma lista e gera um único PDF consolidado.
Como funcionam? 
Ambas utilizam a função auxiliar _get_exames_do_dia para buscar os dados. 
A visualizar renderiza um template HTML, e a imprimir usa a função render_to_pdf para gerar o arquivo.

6) gerar_pdf_exame_view(...):
O que faz? 
Gera um PDF para um único item de exame.
Como funciona? 
Usa fetch_exame_especifico para obter os dados e render_to_pdf para criar o PDF.

"""
def agora():
    momento_atual = datetime.now()
    return momento_atual.strftime("%Y-%m-%d %H:%M:%S")

def _get_pdf_context_assets():
    """
    Função auxiliar para carregar assets em base64 para o contexto do PDF.
    Centraliza a lógica de leitura de arquivos para evitar repetição.
    """
    assets = {}
    
    def get_image_base64_uri(relative_path):
        """Carrega uma imagem de um arquivo estático e retorna como uma string base64 Data URI."""
        # O caminho para os arquivos estáticos do seu app 'pep_exames'
        # BASE_DIR -> hsf_plataforma_pep_exames/
        # Então o caminho completo será: hsf_plataforma_pep_exames/pep_exames/static/pep_exames/images/...
        app_static_dir = os.path.join(settings.BASE_DIR, 'pep_exames', 'static')
        full_path = os.path.join(app_static_dir, relative_path)

        try:
            with open(full_path, "rb") as image_file:
                # Codifica para base64 e depois decodifica para uma string utf-8
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                # Retorna no formato que o HTML <img src="..."> espera
                # Assumindo que a imagem é PNG. Poderíamos tornar isso mais dinâmico.
                return f"data:image/png;base64,{encoded_string}"
        except (FileNotFoundError, IOError) as e:
            print(f"{agora()} - AVISO: Arquivo de asset não encontrado em: {full_path}. Erro: {e}")
            return ""

    # Caminho para a assinatura
    assets['daniela_rizzo_base64'] = get_image_base64_uri('pep_exames/images/rizzo.png')

    # Carrega a imagem do logo do HSF
    assets['logo_hsf_base64'] = get_image_base64_uri('pep_exames/images/hsf_logo.png')
    
    
    return assets

def index_view(request):
    print(f'{agora()} - INICIO index_view(request)')
    context = {
        'titulo_pagina': 'Login - Plataforma PEP Exames',
        'mensagem_login': None, 
        'erro_login': None      
    }

    if request.method == 'POST':
        print(f'{agora()} - index_view: Recebido método POST')
        # Os nomes 'username' e 'password' devem corresponder aos atributos 'name' dos inputs no seu HTML
        username_form = request.POST.get('username')
        password_form = request.POST.get('password')
        
        print(f'{agora()} - index_view: Dados recebidos do formulário:')
        print(f"                 -> username: '{username_form}' (tipo: {type(username_form)})")
        # CUIDADO: Nunca imprima senhas em logs de produção. Para depuração, ok, mas remova depois.
        print(f"                 -> password: '{password_form}' (tipo: {type(password_form)})")

        if username_form and password_form:
            user_data = authenticate_cd_pesssoa_fisica(username_form, password_form)
            if user_data:
                print(f'{agora()} - index_view: Login BEM-SUCEDIDO para {user_data.get("nome")}')
                context['mensagem_login'] = f"Login bem-sucedido! Bem-vindo(a), {user_data.get('nome')} (Código: {user_data.get('codigo')})!"                
                
                # Redireciona para a view da lista de exames, passando o código da pessoa física (que é o 'password' do login)
                cd_pessoa_fisica_login = user_data.get("codigo") # Este é o CD_PESSOA_FISICA
                return redirect('lista_exames', cd_pessoa_fisica=str(cd_pessoa_fisica_login))
            else:
                print(f'{agora()} - index_view: Login FALHOU para o usuário "{username_form}"')
                context['erro_login'] = "Usuário ou senha inválidos. Tente novamente."
        else:
            print(f'{agora()} - index_view: Usuário ou senha não fornecidos no POST.')
            context['erro_login'] = "Por favor, preencha usuário e senha."
            
    print(f'{agora()} - FIM index_view(request)')
    return render(request, 'pep_exames/index.html', context)

def authenticate_cd_pesssoa_fisica(username, password):
    print(f'{agora()} - INÍCIO - def authenticate_cd_pesssoa_fisica(username="{username}", password="{password}")') # Cuidado com print de senha

    user_db = os.environ.get("DB_USER", 'TASY')
    password_db = os.environ.get("DB_PASSWORD", 'aloisk')
    dsn = os.environ.get("DB_DSN", "192.168.5.9:1521/TASYPRD")
    connection = None # Inicializa para garantir que o finally não falhe se a conexão não for aberta

    try:
        connection = oracledb.connect(user=user_db, password=password_db, dsn=dsn) # Parâmetros nomeados
        print(f"{agora()} - Conexão estabelecida (authenticate_with_CPF): {connection}")

        with connection.cursor() as cursor:
            sql = """
                SELECT
                    PF.CD_PESSOA_FISICA CODIGO,
                    UPPER(PF.NM_PESSOA_FISICA) NOME,
                    PF.NR_CPF CPF,
                    PF.NR_PRONTUARIO PRONTUARIO
                FROM PESSOA_FISICA PF
                WHERE PF.NR_PRONTUARIO = :USERNAME
                --WHERE PF.CD_PESSOA_FISICA = :CD_PESSOA_FISICA
                AND PF.CD_PESSOA_FISICA = :PASSWORD


            """
            # Os nomes das chaves em 'params' devem corresponder aos placeholders na query SQL (ex: :NM_PESSOA_FISICA)
            params = {
                'PASSWORD': password,
                'USERNAME': username
            }
            print(f"{agora()} - authenticate_cd_pesssoa_fisica: Executando SQL com parâmetros: {params}")
            cursor.execute(sql, params)
            result = cursor.fetchone()
            
            print(f'{agora()} - authenticate_cd_pesssoa_fisica: Resultado da query (cursor.fetchone()): {result}')
            
            if result:
                # Supondo que as colunas são CODIGO e NOME, nessa ordem
                codigo_usuario = result[0]
                nome_usuario = result[1]
                cpf = result[2]
                prontuario = result[3]
                print(f'{agora()} - authenticate_cd_pesssoa_fisica: ')
                print(f'{agora()} - Usuário encontrado!')
                print(f'{agora()} - Código: {codigo_usuario}')
                print(f'{agora()} - Nome: {nome_usuario}')
                print(f'{agora()} - CPF: {cpf}')
                print(f'{agora()} - PRONTUARIO: {prontuario}')
                return {"codigo": codigo_usuario, "nome": nome_usuario}
            else:
                print(f'{agora()} - authenticate_cd_pesssoa_fisica: Nenhum usuário encontrado com as credenciais fornecidas.')
                return None

    except oracledb.DatabaseError as e: # Alterado para oracledb.DatabaseError
            error_obj, = e.args # Para python-oracledb, e.args[0] também pode ser usado
            print(f'{agora()} - authenticate_cd_pesssoa_fisica: oracledb.DatabaseError: {e}')
            print(f'{agora()} - authenticate_cd_pesssoa_fisica: Oracle Error Code: {error_obj.code}')
            print(f'{agora()} - authenticate_cd_pesssoa_fisica: Oracle Error Message: {error_obj.message}')
            return None # Retorna None em caso de erro de banco
    finally:
        if connection:
            connection.close()
            print(f"{agora()} - authenticate_cd_pesssoa_fisica: Conexão fechada!")
    print(f'{agora()} - FIM - def authenticate_cd_pesssoa_fisica')
    return None # Caso algo inesperado aconteça e não entre no if/else do result
        
def fetch_exames_por_pessoa_fisica(cd_pessoa_fisica_param): # Esta função busca a lista, não precisa do NR_PRESCRICAO aqui
    print(f'{agora()} - INÍCIO - def fetch_exames_por_pessoa_fisica(cd_pessoa_fisica_param="{cd_pessoa_fisica_param}")')

    user_db = os.environ.get("DB_USER", 'TASY')
    password_db = os.environ.get("DB_PASSWORD", 'aloisk')
    dsn = os.environ.get("DB_DSN", "192.168.5.9:1521/TASYPRD")
    connection = None
    exames = []

    try:
        connection = oracledb.connect(user=user_db, password=password_db, dsn=dsn)
        print(f"{agora()} - fetch_exames_por_pessoa_fisica: Conexão estabelecida.")

        with connection.cursor() as cursor:
            # A query que você forneceu
            sql = """
                    SELECT 
                        Obter_Desc_Exame(PPROC.NR_SEQ_EXAME) AS EXAME,
                        to_char(RL.DT_COLETA,'DD/MM/YYYY HH24:MI') AS DATA_COLETA,
                        to_char(RL.DT_ATUALIZACAO,'DD/MM/YYYY HH24:MI') AS DATA_ATUALIZACAO,         
                        INITCAP(Obter_Dados_Usuario_Opcao(RL.nm_usuario,'NP')) AS NM_PROFISSIONAL,  
                        NVL(INITCAP(CG.DS_CARGO), ' - ') AS CARGO,
                        NVL(CPROF.SG_CONSELHO, ' - ') AS DS_CONSELHO,
                        NVL(PF.DS_CODIGO_PROF,' - ') AS DS_PROFISSIONAL,
                        P.NM_PESSOA_FISICA AS NOME_PACIENTE,
                        PPROC.NR_SEQUENCIA AS ID_EXAME_ITEM, 
                        RL.NR_PRESCRICAO AS NR_PRESCRICAO,
                        PPROC.NR_SEQUENCIA AS NR_SEQUENCIA,
                        RL.DS_RESULTADO AS RESULTADO
                    FROM pessoa_fisica P 
                    INNER JOIN prescr_medica PM ON (PM.CD_PESSOA_FISICA = P.CD_PESSOA_FISICA)
                    INNER JOIN prescr_procedimento PPROC ON (PPROC.NR_PRESCRICAO = PM.NR_PRESCRICAO)
                    INNER JOIN exame_laboratorio EL ON (EL.NR_SEQ_EXAME = PPROC.NR_SEQ_EXAME)
                    INNER JOIN grupo_exame_lab GEL ON (GEL.NR_SEQUENCIA = EL.NR_SEQ_GRUPO)
                    INNER JOIN exame_lab_resultado ELR ON (ELR.NR_PRESCRICAO = PM.NR_PRESCRICAO) 
                    INNER JOIN exame_lab_result_item ELRI ON (ELR.nr_seq_resultado = ELRI.nr_seq_resultado AND ELRI.NR_SEQ_PRESCR = PPROC.NR_SEQUENCIA)
                    INNER JOIN result_laboratorio RL ON (RL.NR_PRESCRICAO = PPROC.NR_PRESCRICAO AND RL.NR_SEQ_PRESCRICAO = PPROC.NR_SEQUENCIA)
                    INNER JOIN USUARIO U ON (U.NM_USUARIO = RL.nm_usuario)
                    INNER JOIN PESSOA_FISICA PF ON (U.CD_PESSOA_FISICA = PF.CD_PESSOA_FISICA)
                    LEFT JOIN CARGO CG ON (CG.CD_CARGO = PF.CD_CARGO)
                    LEFT JOIN CONSELHO_PROFISSIONAL CPROF ON (CPROF.NR_SEQUENCIA = PF.NR_SEQ_CONSELHO)
                    WHERE ELRI.NR_SEQ_MATERIAL IS NOT NULL
                    AND (RL.ie_formato_texto IS NULL OR RL.ie_formato_texto <> 3)
                    AND P.CD_PESSOA_FISICA = :CD_PESSOA_FISICA
                    ORDER BY RL.DT_ATUALIZACAO DESC
                    --FETCH FIRST 10 ROWS ONLY
            """
            params = {'CD_PESSOA_FISICA': cd_pessoa_fisica_param}
            print(f"{agora()} - fetch_exames_por_pessoa_fisica: Executando SQL com parâmetros: {params}")
            
            cursor.execute(sql, params)
            
            # Obter os nomes das colunas para criar dicionários
            colnames = [desc[0] for desc in cursor.description]
            
            for row in cursor:
                exames.append(dict(zip(colnames, row)))
            
            # Converter o campo RESULTADO de RTF para texto simples
            for exame in exames:
                rtf_content = exame.get('RESULTADO')
                if rtf_content:
                    try:
                        # Use a biblioteca rtfparse para extrair texto simples
                        exame['RESULTADO_TEXTO_PURO'] = rtf_to_text(rtf_content, errors="ignore")
                    except Exception as e:
                        print(f"{agora()} - fetch_exames_por_pessoa_fisica: Erro ao parsear RTF: {e}")
                        exame['RESULTADO_TEXTO_PURO'] = "Erro ao carregar resultado." # Mensagem de fallback
            print(f'{agora()} - fetch_exames_por_pessoa_fisica: {len(exames)} exames encontrados.')


    except oracledb.DatabaseError as e: # Alterado para oracledb.DatabaseError
        error_obj, = e.args # Para python-oracledb, e.args[0] também pode ser usado
        print(f'{agora()} - fetch_exames_por_pessoa_fisica: cx_Oracle.DatabaseError: {e}')
        print(f'{agora()} - fetch_exames_por_pessoa_fisica: Oracle Error Code: {getattr(error_obj, "code", "N/A")}') # Usar getattr para segurança ao acessar atributos de erro
        print(f'{agora()} - fetch_exames_por_pessoa_fisica: Oracle Error Message: {error_obj.message}')
    finally:
        if connection:
            connection.close()
            print(f"{agora()} - fetch_exames_por_pessoa_fisica: Conexão fechada!")
    
    print(f'{agora()} - FIM - def fetch_exames_por_pessoa_fisica')
    return exames

def fetch_exame_especifico(cd_pessoa_fisica_param, id_exame_item_param, nr_prescricao_param):
    print(f'{agora()} - INÍCIO - def fetch_exame_especifico(cd_pessoa_fisica_param="{cd_pessoa_fisica_param}" (tipo: {type(cd_pessoa_fisica_param)}), id_exame_item_param="{id_exame_item_param}" (tipo: {type(id_exame_item_param)}), nr_prescricao_param="{nr_prescricao_param}" (tipo: {type(nr_prescricao_param)}))')

    user_db = os.environ.get("DB_USER", 'TASY')
    password_db = os.environ.get("DB_PASSWORD", 'aloisk')
    dsn = os.environ.get("DB_DSN", "192.168.5.9:1521/TASYPRD")
    connection = None
    exame_data = None

    try:
        connection = oracledb.connect(user=user_db, password=password_db, dsn=dsn)
        print(f"{agora()} - fetch_exame_especifico: Conexão estabelecida.")

        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    Obter_Desc_Exame(PPROC.NR_SEQ_EXAME) AS EXAME,
                    to_char(RL.DT_COLETA,'DD/MM/YYYY HH24:MI') AS DATA_COLETA,
                    to_char(RL.DT_ATUALIZACAO,'DD/MM/YYYY HH24:MI') AS DATA_ATUALIZACAO,         
                    INITCAP(Obter_Dados_Usuario_Opcao(RL.nm_usuario,'NP')) AS NM_PROFISSIONAL,  
                    NVL(INITCAP(CG.DS_CARGO), ' - ') AS CARGO,
                    NVL(CPROF.SG_CONSELHO, ' - ') AS DS_CONSELHO,
                    NVL(PF_PROF.DS_CODIGO_PROF,' - ') AS DS_PROFISSIONAL,
                    PPROC.NR_SEQUENCIA AS ID_EXAME_ITEM,
                    RL.NR_PRESCRICAO AS NR_PRESCRICAO,
                    PPROC.NR_SEQUENCIA AS NR_SEQUENCIA,
                    RL.DS_RESULTADO AS RESULTADO,
                    P.NM_PESSOA_FISICA AS NOME_PACIENTE
                FROM pessoa_fisica P 
                INNER JOIN prescr_medica PM ON (PM.CD_PESSOA_FISICA = P.CD_PESSOA_FISICA)
                INNER JOIN prescr_procedimento PPROC ON (PPROC.NR_PRESCRICAO = PM.NR_PRESCRICAO)
                INNER JOIN exame_laboratorio EL ON (EL.NR_SEQ_EXAME = PPROC.NR_SEQ_EXAME)
                INNER JOIN grupo_exame_lab GEL ON (GEL.NR_SEQUENCIA = EL.NR_SEQ_GRUPO)
                INNER JOIN exame_lab_resultado ELR ON (ELR.NR_PRESCRICAO = PM.NR_PRESCRICAO) 
                INNER JOIN exame_lab_result_item ELRI ON (ELR.nr_seq_resultado = ELRI.nr_seq_resultado AND ELRI.NR_SEQ_PRESCR = PPROC.NR_SEQUENCIA)
                INNER JOIN result_laboratorio RL ON (RL.NR_PRESCRICAO = PPROC.NR_PRESCRICAO AND RL.NR_SEQ_PRESCRICAO = PPROC.NR_SEQUENCIA)
                INNER JOIN USUARIO U ON (U.NM_USUARIO = RL.nm_usuario)
                INNER JOIN PESSOA_FISICA PF_PROF ON (U.CD_PESSOA_FISICA = PF_PROF.CD_PESSOA_FISICA) -- Usamos PF_PROF para o profissional
                LEFT JOIN CARGO CG ON (CG.CD_CARGO = PF_PROF.CD_CARGO)
                LEFT JOIN CONSELHO_PROFISSIONAL CPROF ON (CPROF.NR_SEQUENCIA = PF_PROF.NR_SEQ_CONSELHO)
                WHERE ELRI.NR_SEQ_MATERIAL IS NOT NULL
                AND (RL.ie_formato_texto IS NULL OR RL.ie_formato_texto <> 3)
                AND P.CD_PESSOA_FISICA = :CD_PESSOA_FISICA --TESTE COM: 15626
                AND PPROC.NR_SEQUENCIA = :ID_EXAME_ITEM -- Filtro pelo ID do item do exame -- TESTE COM: 9
                AND RL.NR_PRESCRICAO = :NR_PRESCRICAO -- Filtro pelo NR_PRESCRICAO -- TESTE COM: 5949304
            """
            params = {
                'CD_PESSOA_FISICA': cd_pessoa_fisica_param,
                'ID_EXAME_ITEM': id_exame_item_param,
                'NR_PRESCRICAO': nr_prescricao_param, # Adicionado o novo parâmetro
            }
            print(f"{agora()} - fetch_exame_especifico: Executando SQL com parâmetros (dict): {params}")
            
            cursor.execute(sql, params)
            
            colnames = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            
            if row:
                exame_data = dict(zip(colnames, row))
                rtf_content = exame_data.get('RESULTADO')
                if rtf_content:
                    try:
                        exame_data['RESULTADO_TEXTO_PURO'] = rtf_to_text(rtf_content, errors="ignore")
                    except Exception as e:
                        print(f"{agora()} - fetch_exame_especifico: Erro ao parsear RTF: {e}")
                        exame_data['RESULTADO_TEXTO_PURO'] = "Erro ao carregar resultado."
                else:
                    print(f"{agora()} - fetch_exame_especifico: NENHUM EXAME ENCONTRADO com os parâmetros fornecidos.")
                print(f'{agora()} - fetch_exame_especifico: Exame encontrado: {exame_data.get("EXAME")}')

    except oracledb.DatabaseError as e: # Alterado para oracledb.DatabaseError
        error_obj, = e.args # Para python-oracledb, e.args[0] também pode ser usado
        print(f'{agora()} - fetch_exame_especifico: cx_Oracle.DatabaseError: {e}')
    finally:
        if connection:
            connection.close()
            print(f"{agora()} - fetch_exame_especifico: Conexão fechada!")
    
    print(f'{agora()} - FIM - def fetch_exame_especifico')
    return exame_data

def lista_exames_view(request, cd_pessoa_fisica):
    print(f'{agora()} - INICIO lista_exames_view(request, cd_pessoa_fisica="{cd_pessoa_fisica}" (tipo: {type(cd_pessoa_fisica)}))')
    
    # Buscar os dados dos exames usando a função que criamos
    lista_de_exames_completa = fetch_exames_por_pessoa_fisica(cd_pessoa_fisica)

    ## Configurar paginação
    #paginator = Paginator(lista_de_exames_completa, 10) # 10 exames por página
    #page_number = request.GET.get('page')
    #try:
    #    exames_paginados = paginator.page(page_number)
    #except PageNotAnInteger:
    #    # Se o número da página não for um inteiro, entregar a primeira página.
    #    exames_paginados = paginator.page(1)
    #except EmptyPage:
    #    # Se o número da página estiver fora do intervalo (e.g. 9999), entregar a última página de resultados.
    #    exames_paginados = paginator.page(paginator.num_pages)
    #
    ## Obter o nome do paciente para exibir na página (opcional, mas bom para UX)
    ## Poderíamos buscar novamente ou, idealmente, ter passado da view de login.
    ## Por simplicidade, vamos assumir que o cd_pessoa_fisica é suficiente por agora.
    ## Se você tiver o nome do paciente da etapa de login, pode passá-lo também.
    ## nome_paciente = # Lógica para buscar o nome do paciente se necessário

        # --- Lógica de Agrupamento na View ---
    # 1. Prepara os dados para o agrupamento, extraindo apenas a data (DD/MM/YYYY)
    for exame in lista_de_exames_completa:
        try:
            data_str = exame['DATA_COLETA'].split(' ')[0]
            exame['DATA_COLETA_OBJ'] = datetime.strptime(data_str, '%d/%m/%Y').date()
        except (ValueError, TypeError, AttributeError):
            exame['DATA_COLETA_OBJ'] = date(1900, 1, 1) # Data para exames sem data

    # 2. Ordena a lista pela data para que o groupby funcione corretamente
    lista_de_exames_completa.sort(key=lambda x: x['DATA_COLETA_OBJ'], reverse=True)

    # 3. Agrupa os exames por data
    exames_agrupados_por_data = []
    for data_coleta, grupo in groupby(lista_de_exames_completa, key=lambda x: x['DATA_COLETA_OBJ']):
        lista_exames_do_dia = list(grupo)
        exames_agrupados_por_data.append({
            'data': data_coleta,
            'total_exames': len(lista_exames_do_dia),
            # Poderíamos passar a lista de exames aqui se o "Visualizar" fosse um modal, por exemplo.
            # 'exames': lista_exames_do_dia 
        })

    # Paginação (agora sobre os grupos, não sobre os exames individuais)
    paginator = Paginator(exames_agrupados_por_data, 10) # 10 grupos de datas por página
    page_number = request.GET.get('page')
    grupos_paginados = paginator.get_page(page_number)
    
    context = {
        #'titulo_pagina': 'Meus Exames Realizados',
        #'exames': exames_paginados, # Passar a página atual de exames para o template
        #'cd_pessoa_fisica': cd_pessoa_fisica, # Pode ser útil para exibir na página
        ## 'nome_paciente': nome_do_paciente_aqui # Se você tiver essa informação
        'grupos_de_exames': grupos_paginados, # Passa os grupos paginados para o template
        'cd_pessoa_fisica': cd_pessoa_fisica, # Pode ser útil para exibir na página
        
    }
    
    #print(f'{agora()} - FIM lista_exames_view: Renderizando página {exames_paginados.number} com {len(exames_paginados.object_list)} exames (Total: {paginator.count}).')
    #return render(request, 'pep_exames/lista_exames_realizados.html', context)

    print(f'{agora()} - FIM lista_exames_view: Renderizando página com {len(grupos_paginados)} grupos.')
    # Usaremos um novo template para essa visualização
    return render(request, 'pep_exames/lista_grupos_exames.html', context)

def render_to_pdf(template_src, context_dict={}, filename=None):
    """
    Renderiza um template HTML para um PDF, opcionalmente forçando o download.
    """
    from django.template.loader import get_template
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    # A codificação UTF-8 é crucial para caracteres especiais
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, encoding='UTF-8')
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        # Se um nome de arquivo for fornecido, força o download
        if filename:
            # Adiciona o cabeçalho Content-Disposition
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return None # Retorna None em caso de erro

def _get_exames_do_dia(cd_pessoa_fisica, data_exame_str):
    """Função auxiliar para buscar todos os exames e filtrar por uma data específica."""
    print(f'{agora()} - INÍCIO - def _get_exames_do_dia(cd_pessoa_fisica="{cd_pessoa_fisica}", data_exame_str="{data_exame_str}")')
    lista_completa = fetch_exames_por_pessoa_fisica(cd_pessoa_fisica)
    
    try:
        data_alvo = datetime.strptime(data_exame_str, '%Y-%m-%d').date()
    except ValueError:
        print(f'{agora()} - _get_exames_do_dia: Formato de data inválido: {data_exame_str}')
        return []

    exames_do_dia = [
        exame for exame in lista_completa 
        if exame.get('DATA_COLETA') and datetime.strptime(exame['DATA_COLETA'].split(' ')[0], '%d/%m/%Y').date() == data_alvo
    ]
    print(f'{agora()} - FIM - def _get_exames_do_dia: Encontrados {len(exames_do_dia)} exames para a data {data_alvo}.')
    return exames_do_dia

def visualizar_exames_por_data_view(request, cd_pessoa_fisica, data_exame):
    print(f'{agora()} - INICIO visualizar_exames_por_data_view para cd_pessoa_fisica="{cd_pessoa_fisica}", data="{data_exame}"')
    
    exames_do_dia = _get_exames_do_dia(cd_pessoa_fisica, data_exame)

    if not exames_do_dia:
        return HttpResponse("Nenhum exame encontrado para esta data.", status=404)

    # Formata a data para exibição no template
    data_formatada = datetime.strptime(data_exame, '%Y-%m-%d').strftime('%d/%m/%Y')

    context = {
        'titulo_pagina': f'Exames de {data_formatada}',
        'exames': exames_do_dia,
        'cd_pessoa_fisica': cd_pessoa_fisica,
        'data_exame': data_formatada,
        'nome_paciente': exames_do_dia[0].get('NOME_PACIENTE', 'Paciente')
    }
    
    print(f'{agora()} - FIM visualizar_exames_por_data_view: Renderizando página com {len(exames_do_dia)} exames.')
    return render(request, 'pep_exames/lista_exames_por_data.html', context)

def imprimir_exames_por_data_view(request, cd_pessoa_fisica, data_exame):
    print(f'{agora()} - INICIO imprimir_exames_por_data_view para cd_pessoa_fisica="{cd_pessoa_fisica}", data="{data_exame}"')

    exames_do_dia = _get_exames_do_dia(cd_pessoa_fisica, data_exame)

    if not exames_do_dia:
        return HttpResponse("Nenhum exame encontrado para esta data para gerar o PDF.", status=404)
    
    nome_paciente = exames_do_dia[0].get('NOME_PACIENTE', 'Paciente')
    
    # Limpa o nome do paciente para usar em um nome de arquivo seguro
    nome_paciente_safe = "".join(c for c in nome_paciente if c.isalnum() or c in (' ', '_')).rstrip()
    nome_arquivo_pdf = f"exames_{nome_paciente_safe.replace(' ', '_')}_{data_exame}.pdf"
    
    
    context = {
        'exames_do_dia': exames_do_dia,
        'nome_paciente': nome_paciente,
        'data_exames': datetime.strptime(data_exame, '%Y-%m-%d').strftime('%d/%m/%Y'),
        # Desempacota o dicionário com os assets (assinatura, etc)
        **_get_pdf_context_assets(),
    }

    # --- INÍCIO DA ALTERAÇÃO (Prints para depuração do contexto) ---
    print(f"{agora()} - imprimir_exames_por_data_view: Contexto final enviado para o template:")
    print(f"                 -> nome_paciente: {context.get('nome_paciente')}")
    print(f"                 -> data_exames: {context.get('data_exames')}")
    print(f"                 -> Total de exames no dia: {len(context.get('exames_do_dia', []))}")
    print(f"                 -> Logo HSF carregado: {'Sim' if context.get('logo_hsf_base64') else 'Não'}")
    print(f"                 -> Assinatura carregada: {'Sim' if context.get('daniela_rizzo_base64') else 'Não'}")
    # --- FIM DA ALTERAÇÃO ---

    print(f"{agora()} - imprimir_exames_por_data_view: Renderizando PDF com {len(exames_do_dia)} exames para o arquivo '{nome_arquivo_pdf}'.")
    
    pdf = render_to_pdf('pep_exames/exames_agrupados_pdf_template.html', context, filename=nome_arquivo_pdf)
    
    if pdf:
        return pdf
    return HttpResponse("Ocorreu um erro ao gerar o PDF.", status=500)


def gerar_pdf_exame_view(request, cd_pessoa_fisica, id_exame_item, nr_prescricao):
    print(f'{agora()} - INICIO gerar_pdf_exame_view para cd_pessoa_fisica="{cd_pessoa_fisica}", id_exame_item="{id_exame_item}", nr_prescricao="{nr_prescricao}"')

    exame = fetch_exame_especifico(cd_pessoa_fisica, id_exame_item, nr_prescricao)

    print(f'{agora()} - gerar_pdf_exame_view: Exame encontrado: {exame.get("EXAME")}')

    if not exame:
        return HttpResponse("Exame não encontrado.", status=404)
    
    context = {
        'exame': exame,
        # A mágica acontece aqui!
        **_get_pdf_context_assets(), 
    }
    pdf = render_to_pdf('pep_exames/exame_pdf_template.html', context)
    print(f'{agora()} - FIM gerar_pdf_exame_view')
    return HttpResponse(pdf, content_type='application/pdf')


