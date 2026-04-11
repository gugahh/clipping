"""
    CLIPPING — Busca notícias recentes sobre temas diversos, usando a NewsAPI.
"""
import os
import requests
import configparser
import traceback
import sys
import webbrowser
from datetime import datetime, timedelta
from includes_python.folder_utils import create_todays_folder
from includes_python.argo_translator import verifica_pacotes_linguagem, translate_en_to_pt

# ── Constants ────────────────────────────────────────────────────────────────

CONFIG_FILE = "config.properties"
DATE_MASK_BR = "%d/%m/%Y %H:%M:%S"  # DD/MM/YYYY HH24:MI:SS
DATE_MASK_BR_SHORT = "%d/%m/%Y"     # DD/MM/YYYY
DATE_MASK_NEWS = "%Y-%m-%d"         # YYYY-MM-DD
url = 'https://newsapi.org/v2/everything'   # URL da API de notícias (NewsAPI)

# ── Helpers ───────────────────────────────────────────────────────────────────

def now_str() -> str:
    """Return current local timestamp formatted as DD/MM/YYYY HH24:MI:SS."""
    return datetime.now().strftime(DATE_MASK_BR)

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
        {'titulo': 'One Health', 'query': '"World Health Organization"+"One Health"'},
        {'titulo': 'Artificial Intelligence UAE', 'query': '"Artificial Intelligence"+UAE'},
        #{'titulo': 'BRICS Bank', 'query': '"BRICS Bank"'},
        {'titulo': 'Rare Earths - Brazil', 'query': '+"Rare Earths"+Brazil'},
        {'titulo': 'Belt and Road', 'query': '"Belt and Road"'},
        #{'titulo': 'Bangladesh', 'query': '"Bangladesh"'},
    ]

    print(f"\tPreparando o tradutor de inglês para português... ")  
    verifica_pacotes_linguagem()

    #query = '"One Health","World Health Organization",'  # Use aspas para frases exatas , como: "BRICS Bank","Belt and Road",', ,"Bangladesh","Qatar" , "Iran","India","China"
    # query = ',"Artificial Intelligence",UAE'  # Use aspas para frases exatas , como: "BRICS Bank","Belt and Road",', ,"Bangladesh","Qatar" , "Iran","India","China"
    #query = '"Rare Earths"+Brazil'
    #query = '"World Health Organization"+"One Health"'

    # Processando cada um dos assuntos definidos;
    # Para cada assunto sera gerado um arquivo Markdown.
    for assunto in assuntos:
        titulo = assunto['titulo']
        query = assunto['query']

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
        }

        # 3. Request
        response = requests.get(url, params=params)
        data = response.json()
        #print(data)
        print(f"\tQuery: {query}")
        if (data['totalResults'] > 0):
            print(f"\tQuantidade de Artigos: {data['totalResults']}")
        else:
            print(f"\tNenhum artigo encontrado.")

        # 4. Print Results
        if data['status'] == 'ok':

            # Criando o arquivo markdown para o assunto atual, dentro da pasta de hoje.
            nome_arquivo = f"{pastaHoje}/{titulo.replace(' ', '_')}.md"
            with open(nome_arquivo, "w", encoding="utf-8") as md_file:
                md_file.write(f"# {titulo}\n\n")
                md_file.write(f"_Gerado em: {now_str()}_\n\n")
                md_file.write(f"_Query: {query}_\n\n")
                md_file.write(f"_Total de Artigos: {data['totalResults']}_\n\n")
                md_file.write("---\n\n")

                for idx, article in enumerate(data['articles'], start=1):

                    esteArtigo = {'titulo': article['title'], 'descricao': article['description'], 'autor': article['author'], 'data_publicacao': article['publishedAt'], 'fonte': article['source']['name'], 'url_artigo': article['url'], 'url_imagem': article['urlToImage'], 'conteudo': article['content'], 'dt_publicacao': article['publishedAt']}

                    # Efetuando traducoes para português, usando o argostranslate.
                    esteArtigo['titulo_traduzido'] = "(Sem Título)" if esteArtigo['titulo'] == None else translate_en_to_pt(esteArtigo['titulo']) 
                    esteArtigo['descricao_traduzida'] = "(Sem Descrição)" if esteArtigo['descricao'] == None else translate_en_to_pt(esteArtigo['descricao'])   
                    esteArtigo['conteudo_traduzido']  = "(Sem Conteúdo)"
                    if esteArtigo['conteudo'] != None:
                        # O conteúdo frequentemente tem uma parte truncada, seguida de um link para o artigo completo. Vamos tentar traduzir apenas a parte inicial, para evitar erros de tradução.
                        partes = esteArtigo['conteudo_traduzido'].split('…')
                        parte_traduzida = translate_en_to_pt(partes[0])  # Traduz apenas a primeira parte
                        esteArtigo['conteudo_traduzido'] = parte_traduzida + ('…' + partes[1] if len(partes) > 1 else '')  # Reconstroi o conteúdo com a parte traduzida

                    #gravando cada um dos artigos no arquivo markdown, 
                    md_file.write(f"## {idx}. {esteArtigo['titulo_traduzido']}\n\n")
                    md_file.write(f"**Descrição:** {esteArtigo['descricao_traduzida']}\n\n")
                    if esteArtigo['url_imagem'] != None:
                        md_file.write(f"![]({esteArtigo['url_imagem']})\n\n")

                    # Autor pode ser uma lista longa. Tratando nomes longos demais.
                    if(esteArtigo['autor'] != None and len(esteArtigo['autor']) > 70): 
                        esteArtigo['autor'] = esteArtigo['autor'][:70] + "..."  # Trunca o nome do autor se for muito longo 
                    else: 
                        esteArtigo['autor'] = esteArtigo['autor'] if esteArtigo['autor'] != None else "Desconecido"

                    md_file.write(f"**Autor(es):** {esteArtigo['autor']}\n\n")  
                    md_file.write(f"**Publicado em:** {datetime.fromisoformat(esteArtigo['data_publicacao']).strftime(DATE_MASK_BR)}\n\n")
                    md_file.write(f"**Fonte:** {esteArtigo['fonte']}\n\n")
                    md_file.write(f"**URL:** {esteArtigo['url_artigo']}\n\n")
                    md_file.write(f"**Conteúdo:** {esteArtigo['conteudo_traduzido']}\n\n")
                    md_file.write("---\n\n")

                    # armazenando em uma lista de artigos, para uso futuro.
                    artigos.append(esteArtigo)
            md_file.close()
            webbrowser.open(f'file://{os.getcwd()}/{nome_arquivo}')  # Abre o arquivo markdown gerado no navegador padrão


                #print(f"\nArtigo: {esteArtigo}\n\n")
                # 'data_publicacao': datetime.fromisoformat(article['publishedAt']).strftime(DATE_MASK_BR)
                #print(f"\nJSON: {article}\n\n")

            #print(f"\nQuantidade de Artigos: {data['totalResults']}\n")
        else:
            print("Error:", data.get('message'))
        
    print("\n")

    #print(f"\nArtigos:")
    #print(artigos)

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
