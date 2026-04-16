"""
    CLIPPING — Busca notícias recentes sobre temas diversos, usando a NewsAPI.
"""
import os
import requests
import configparser
import traceback
import sys
import webbrowser
import includes_python.persiste_sqlite as db 
from datetime import datetime, timedelta
from includes_python.folder_utils import create_todays_folder
from includes_python.argo_translator import verifica_pacotes_linguagem, translate_en_to_pt

# ── Constants ────────────────────────────────────────────────────────────────

CONFIG_FILE = "config.properties"
DATE_MASK_BR = "%d/%m/%Y %H:%M:%S"  # DD/MM/YYYY HH24:MI:SS
DATE_MASK_BR_MID = "%d/%m/%Y %H:%M"  # DD/MM/YYYY HH24:MI
DATE_MASK_BR_SHORT = "%d/%m/%Y"     # DD/MM/YYYY
DATE_MASK_NEWS = "%Y-%m-%d"         # YYYY-MM-DD
url = 'https://newsapi.org/v2/everything'   # URL da API de notícias (NewsAPI)

# ── Helpers ───────────────────────────────────────────────────────────────────

def now_str() -> str:
    """Return current local timestamp formatted as DD/MM/YYYY HH24:MI:SS."""
    return datetime.now().strftime(DATE_MASK_BR_MID)

# ── Obtem configuracoes a partir do config.properties ──────────────────────
def read_config(path: str) -> configparser.ConfigParser:
    """
    Read config.properties.  configparser requires a [section] header;
    we inject a fake one so plain key=value files are also accepted.
    """
    config = configparser.ConfigParser()
    with open(path, "r", encoding="utf-8") as fh:
        content = "[DEFAULT]\n" + fh.read()
    config.read_string(content)
    return config

def fc_verifica_se_artigo_novo(conn, artigo):
    """
    Verifica se o artigo é novo, ou seja, se ele ainda não foi lido (ou foi lido hoje).
    Atribui no dicionário do artigo a chave 'eh_novo' com valor True ou False, dependendo do resultado da verificação;
    Atribui o id do artigo no dicionário do artigo, caso ele seja inserido no banco de dados.
    """
    # Verificando no db se este artigo eh novo ou nao.
    info_artigo = db.fc_obtem_dados_artigo(conn, artigo)  # Obtem a data de leitura do artigo, se ele já existir no banco de dados.
    print(f"\tinfo_artigo: {info_artigo}\n")
    if info_artigo == None:
        idArtigo = db.fc_insere_artigo(conn, artigo)  # Insere o artigo no banco de dados.
        print(f"\tidArtigo: {idArtigo}\n")
        artigo['id'] = idArtigo  # Armazena o ID do artigo no dicionário do artigo, para futuras referências.
    #Artigos com data de hoje tambem sao considerados como novos. Temos que converter para string e comparar, para evitar problemas de comparacao.
    artigo['eh_novo'] = True if (info_artigo == None or (datetime.now().strftime('%Y-%m-%d') == info_artigo["dt_leitura"].strftime('%Y-%m-%d'))) else False

def fc_traduz_artigo(conn, artigo):
    """
    Traduz o conteúdo do artigo para português e trunca o conteúdo traduzido, se necessário.
    Utiliza o cache de traducoes no banco de dados, para evitar traduzir o mesmo artigo mais de uma vez.
    """
    # Caso o artigo tenha id, ele pode ja existir no cache de traducoes.
    if artigo['id'] != None:
        traducacao_cache = db.fc_obtem_traducao_cache(conn, artigo['id'])  # Obtem as traduções do artigo, se existirem.
        print(f"\ttraducacao_cache: {traducacao_cache}\n")
        if traducacao_cache != None:
            artigo['titulo_traduzido'] = traducacao_cache['titulo_traduzido']
            artigo['descricao_traduzida'] = traducacao_cache['descricao_traduzida']
            artigo['conteudo_traduzido'] = traducacao_cache['conteudo_traduzido']
            return  # Se as traduções já existem no banco de dados, não é necessário traduzi-las novamente. 
        
    # Se chegou aqui, a traducao nao existe no cache, ainda.
    # Efetuando traducoes para português, usando o argostranslate.
    artigo['titulo_traduzido'] = "(Sem Título)" if artigo['titulo'] == None else translate_en_to_pt(artigo['titulo']) 
    artigo['descricao_traduzida'] = "(Sem Descrição)" if artigo['descricao'] == None else translate_en_to_pt(artigo['descricao'])   
    artigo['conteudo_traduzido']  = "(Sem Conteúdo)"
    if artigo['conteudo'] != None:
        # O conteúdo frequentemente tem uma parte truncada, seguida de um link para o artigo completo. Vamos tentar traduzir apenas a parte inicial, para evitar erros de tradução.
        partes = artigo['conteudo_traduzido'].split('…')
        parte_traduzida = translate_en_to_pt(partes[0])  # Traduz apenas a primeira parte
        artigo['conteudo_traduzido'] = parte_traduzida + ('…' + partes[1] if len(partes) > 1 else '')  # Reconstroi o conteúdo com a parte traduzida
    db.fc_insere_traducao_cache(conn, artigo)  # Insere a tradução no cache do banco de dados, para futuras referências.

def fc_trata_nome_autor(artigo):
    """
    O campo Autor pode ser uma lista longa. Tratando nomes de autor longos demais.
    Altera o dictionary original. 
    """
    if(artigo['autor'] != None and len(artigo['autor']) > 70): 
        artigo['autor'] = artigo['autor'][:70] + "..."  # Trunca o nome do autor se for muito longo 
    else: 
        artigo['autor'] = artigo['autor'] if artigo['autor'] != None else "Desconhecido"
    

# -----------------------------------------------
# ── AQUI COMECA o programa de verdade.
# -----------------------------------------------

def main(): 
    print(f"Inicializando... \n")

    # 1. Read Configurations
    cfg = read_config(CONFIG_FILE)
    defaults = cfg["DEFAULT"]

    api_key        = defaults.get("news_api_token", "").strip()
    num_dias_recuo = defaults.get("num_dias_recuo", "").strip()

    print(f"\nProperties obtido. ")
    print(f"\tapi_key: \t\t\t{"(Atribuida)" if api_key != None else "(Nao Atribuida)"}")
    print(f"\tnum_dias_recuo: \t\t{num_dias_recuo}")

    # print(f"\nCriando pasta para hoje... ")
    pastaHoje = create_todays_folder()

    dataInicio = (datetime.now() - timedelta(days=int(num_dias_recuo))) #Datetime
    print(f"\tData de Inicio da busca: \t{dataInicio.strftime(DATE_MASK_BR_SHORT)}")  

    # Aqui sao definidos os assuntos desejados, separados por virgula.  Use aspas para frases exatas, como "One Health"
    assuntos = [
        #{'titulo': 'One Health', 'query': '"World Health Organization"+"One Health"'},
        #{'titulo': 'Artificial Intelligence UAE', 'query': '"Artificial Intelligence"+UAE'},
        #{'titulo': 'Bloqueio de Ormuz', 'query': '+blockade,+Ormuz'},
        #{'titulo': 'Banco Islâmico de Desenvolvimento', 'query': '"Islamic Development Bank"'},
        #{'titulo': 'Terras Raras - Brazil', 'query': '+"Rare Earths"+Brazil'},
        #{'titulo': 'Belt and Road', 'query': '"Belt and Road"'},
        {'titulo': 'Globalização - China', 'query': '+Globalization,+China'},
        #{'titulo': 'ACNUR - Alto Comissariado das Nações Unidas para os Refugiados', 'query': 'ACNUR'},
        #{'titulo': 'ASEAN', 'query': 'ASEAN'},
        #{'titulo': 'Sarampo - Asia', 'query': '+Measles,+Asia'},
        #{'titulo': 'Sarampo - Oriente Médio', 'query': '+Measles,+"Middle East"'},
        #{'titulo': 'Oriente Médio - Saúde', 'query': '+Health,+"Middle East"'},
        #{'titulo': 'ESCWA', 'query': 'ESCWA'},
        #{'titulo': 'ESCAP', 'query': 'ESCAP'},
    ]

    print(f"\tPreparando o tradutor de inglês para português... ")  
    verifica_pacotes_linguagem() # Prepara o tradutor
    conn = db.open_connection() # Abre uma conexão com o banco de dados SQLite, para verificar artigos já existentes e gravar novos artigos.

    # ----------------------------------------------------------
    # Processando cada um dos assuntos definidos;
    # Para cada assunto sera gerado um arquivo Markdown.
    for assunto in assuntos:
        titulo = assunto['titulo']
        query = assunto['query']
        #sources = assunto['sources']  # Fonte opcional para filtrar os artigos, por exemplo: 'China Daily'. Se None, busca em todas as fontes.

        # Aqui ficarao armazenados todos os artigos, do assunto atual.
        # Cada artigo é um dict com as chaves: titulo, descricao, autor, data_publicacao, fonte, url_artigo, url_imagem, content
        artigos = []

        print(f'\n>> Buscando por: "{titulo}"...')

        # 2. Query Parameters
        params = {
            'q': query ,
            #'sortBy': 'publishedAt', # Criterio: mais recente
            'sortBy':'popularity' ,
            'language': 'en',
            'from': dataInicio.strftime(DATE_MASK_NEWS),  # Data no formato '2026-04-07'
            'apiKey': api_key
            #'sources': 'Newser,The Times of India'
        }

        # 3. Request
        response = requests.get(url, params=params)
        data = response.json()
        #print(data) #So para Debug
        print(f"\tQuery: {query}")
        if (data != None and data['status'] == 'error'):
            print(f"\nERRO ao acessar a API de notícias; Tipo de erro: {data['code']}")
            print(f"\nDetalhe do Erro: {data['message']}\n")
            sys.exit(-1) #Saida com erro, para evitar continuar o processamento sem dados validos.

        if (data['totalResults'] > 0):
            print(f"\tQuantidade de Artigos: {data['totalResults']}")
        else:
            print(f"\tNenhum artigo encontrado.")

        # 4. Monta a lista de artigos, traduz os campos necessários, verifica se são novos ou não, e grava no arquivo markdown.
        if data['status'] == 'ok':

            # Criando o arquivo markdown para o assunto atual, dentro da pasta de hoje.
            nome_arquivo = f"{pastaHoje}/{titulo.replace(' ', '_')}.md"
            with open(nome_arquivo, "w", encoding="utf-8") as md_file:
                md_file.write(f"# {titulo}\n\n")
                md_file.write(f"- _Gerado em: {now_str()}_\n")
                md_file.write(f"- _Query: {query}_\n")
                md_file.write(f"- _Total de Artigos: {data['totalResults']}_\n")
                md_file.write("---\n\n")

                for article in data['articles']:

                    artigo_ja_persistido = False  
                    esteArtigo = {'id': None, 'eh_novo': True, 'titulo': article['title'], 'descricao': article['description'], 'autor': article['author'], 'data_publicacao': article['publishedAt'], 'fonte': article['source']['name'], 'url_artigo': article['url'], 'url_imagem': article['urlToImage'], 'conteudo': article['content'], 'dt_publicacao': article['publishedAt']}

                    # Efetuando traducoes para português, usando o argostranslate.
                    esteArtigo['titulo_traduzido'] = "(Sem Título)" if esteArtigo['titulo'] == None else translate_en_to_pt(esteArtigo['titulo']) 
                    esteArtigo['descricao_traduzida'] = "(Sem Descrição)" if esteArtigo['descricao'] == None else translate_en_to_pt(esteArtigo['descricao'])   
                    esteArtigo['conteudo_traduzido']  = "(Sem Conteúdo)"
                    if esteArtigo['conteudo'] != None:
                        # O conteúdo frequentemente tem uma parte truncada, seguida de um link para o artigo completo. Vamos tentar traduzir apenas a parte inicial, para evitar erros de tradução.
                        partes = esteArtigo['conteudo_traduzido'].split('…')
                        parte_traduzida = translate_en_to_pt(partes[0])  # Traduz apenas a primeira parte
                        esteArtigo['conteudo_traduzido'] = parte_traduzida + ('…' + partes[1] if len(partes) > 1 else '')  # Reconstroi o conteúdo com a parte traduzida
                    
                    # Verificando se este artigo eh novo ou nao.
                    #dt_artigo = db.fc_obtem_data_artigo(conn, esteArtigo)  # Obtem a data de leitura do artigo, se ele já existir no banco de dados.
                    info_artigo_bd = db.fc_obtem_dados_artigo(conn, esteArtigo)
                    print(esteArtigo['titulo_traduzido'])
                    print(f"\tinfo_artigo_bd: {info_artigo_bd}\n")
                    print(f"\tTipo do id: {type(info_artigo_bd['id']) if info_artigo_bd else None}\n")

                    artigo_ja_persistido = True if info_artigo_bd != None else False  
                    dt_artigo = info_artigo_bd['dt_leitura'] if artigo_ja_persistido else None
                    print(f"\tData do artigo do BD: {dt_artigo} - Data de leitura no BD: {dt_artigo}\n")
                    print(f"\tartigo_ja_persistido: {artigo_ja_persistido}\n")

                    #Artigos com data de hoje tambem sao considerados como novos. Temos que converter para string e comparar, para evitar problemas de comparacao.
                    esteArtigo['eh_novo'] = True if (dt_artigo == None or (datetime.now().strftime('%Y-%m-%d') == dt_artigo.strftime('%Y-%m-%d'))) else False

                    # Autor pode ser uma lista longa. Tratando nomes longos demais.
                    if(esteArtigo['autor'] != None and len(esteArtigo['autor']) > 70): 
                        esteArtigo['autor'] = esteArtigo['autor'][:70] + "..."  # Trunca o nome do autor se for muito longo 
                    else: 
                        esteArtigo['autor'] = esteArtigo['autor'] if esteArtigo['autor'] != None else "Desconhecido"
                    """
                    fc_verifica_se_artigo_novo(conn, esteArtigo) #Atribui o id do artigo e se ele é novo ou não, no dicionário do artigo.

                    print(f"\nProcessando artigo: {esteArtigo['titulo']} (ID: {esteArtigo['id']}, Novo: {esteArtigo['eh_novo']})\n")
                    if esteArtigo['id'] == None:
                        #Se o artigo não tem id: Inserindo o artigo no BD
                        result_gravacao, id_artigo = db.fc_insere_artigo(conn, esteArtigo)
                        if result_gravacao == 'OK':
                            esteArtigo['id'] = id_artigo  # Armazena o ID do artigo no dicionário do artigo, para futuras referências.
                        else:
                            print(f"\nERRO ao gravar o artigo no banco de dados. Título: {esteArtigo['titulo']}\n")
                            continue  # Pula para o próximo artigo, para evitar processar um artigo sem ID válido.

                    fc_traduz_artigo(conn, esteArtigo) # Traduz o o artigo, usando o argostranslate. Usa cache para otimizar.
                    fc_trata_nome_autor(esteArtigo) # Autor pode ser uma lista longa. Tratando nomes de autor longos demais.
                    """
                    print(f"\testeArtigo['eh_novo']: {esteArtigo['eh_novo']}\n")
                    if artigo_ja_persistido == False:  # Se o artigo ainda não foi persistido no banco de dados, insere o artigo e a tradução no cache.
                        result_insercao, id_artigo = db.fc_insere_artigo(conn, esteArtigo)  # Insere o artigo no banco de dados.
                        if result_insercao == 'OK':
                            esteArtigo['id'] = id_artigo  # Armazena o ID do artigo no dicionário do artigo, para futuras referências.
                            print(f"\nArtigo inserido no banco de dados. Título: {esteArtigo['titulo']} - ID: {esteArtigo['id']}\n")
                            #db.fc_insere_traducao_cache(conn, esteArtigo)  # Insere a tradução no cache do banco de dados, para futuras referências.

                    # armazenando o artigo na lista.
                    artigos.append(esteArtigo)
                # fim do loop de artigos inicial.

                # Re-ordenando os artigos, para que os novos fiquem no topo da lista.
                artigos_ordenados = sorted(artigos, key=lambda x: x['eh_novo'], reverse=True)

                #gravando cada um dos artigos, ja ordenados, no arquivo markdown
                for idx, esteArtigo in enumerate(artigos_ordenados, start=1):
                    md_file.write(f"## {idx}. {esteArtigo['titulo_traduzido']}\n\n")
                    if esteArtigo['eh_novo']:
                        md_file.write("![](../../images/new.png)")  # Exibe um ícone "new" para artigos considerados novos
                    md_file.write(f"**Descrição:** {esteArtigo['descricao_traduzida']}\n\n")
                    if esteArtigo['url_imagem'] != None:
                        md_file.write(f"![]({esteArtigo['url_imagem']})\n\n")


                    md_file.write(f"**Autor(es):** {esteArtigo['autor']}\n\n")  
                    md_file.write(f"**Publicado em:** {datetime.fromisoformat(esteArtigo['data_publicacao']).strftime(DATE_MASK_BR)}\n\n")
                    md_file.write(f"**Fonte:** {esteArtigo['fonte']}\n\n")
                    md_file.write(f"**URL:** {esteArtigo['url_artigo']}\n\n")
                    md_file.write(f"**Conteúdo:** {esteArtigo['conteudo_traduzido']}\n\n")
                    md_file.write("---\n\n")

            md_file.close()

            webbrowser.open(f'file://{os.getcwd()}/{nome_arquivo}')  # Abre o arquivo markdown gerado no navegador padrão


                #print(f"\nArtigo: {esteArtigo}\n\n")
                # 'data_publicacao': datetime.fromisoformat(article['publishedAt']).strftime(DATE_MASK_BR)
                #print(f"\nJSON: {article}\n\n")

            #print(f"\nQuantidade de Artigos: {data['totalResults']}\n")
        else:
            print("Error:", data.get('message'))
        
    conn.close()  # Fecha a conexão com o banco de dados SQLite, após processar todos os assuntos e artigos.
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Simplified stack trace: show only the last frame + exception type/message
        tb = traceback.extract_tb(sys.exc_info()[2])
        last = tb[-1] if tb else None
        exc_type, exc_val, _ = sys.exc_info()
        location = f"{last.filename}:{last.lineno} in {last.name}()" if last else "unknown location"
        print(
            f"[{now_str()}] ERROR — {exc_type.__name__}: {exc_val}\n"
            f"  Location: {location}"
        )
        sys.exit(1)
