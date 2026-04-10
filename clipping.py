"""
    NEWS READER — Busca notícias recentes sobre temas diversos, usando a NewsAPI.
"""
import requests
import configparser
import traceback
import sys
from datetime import datetime, timedelta

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

    dataInicio = (datetime.now() - timedelta(days=int(num_dias_recuo))) #Datetime
    print(f"\tData de Inicio da busca: \t{dataInicio.strftime(DATE_MASK_BR_SHORT)}")  

    # Aqui ficarao armazenados todos os artigos, de todas as buscas.  
    # Cada artigo é um dict com as chaves: titulo, descricao, autor, data_publicacao, fonte, url_artigo, url_imagem, content
    artigos = []

    # Aqui sao definidos os assuntos desejados, separados por virgula.  Use aspas para frases exatas, como "One Health"
    #query = '"One Health","World Health Organization",'  # Use aspas para frases exatas , como: "BRICS Bank","Belt and Road",', ,"Bangladesh","Qatar" , "Iran","India","China"
    # query = ',"Artificial Intelligence",UAE'  # Use aspas para frases exatas , como: "BRICS Bank","Belt and Road",', ,"Bangladesh","Qatar" , "Iran","India","China"
    #query = '"Rare Earths"+Brazil'
    query = '"World Health Organization"+"One Health"'

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
    print(f"\n\tQuery: {query}\n")
    print(f"\tQuantidade de Artigos: {data['totalResults']}\n")

    # 4. Print Results
    if data['status'] == 'ok':
        for idx, article in enumerate(data['articles'], start=1):
            print(f"-- ({idx}) ---------------------------------------------")
            print(f"Titulo: {article['title']}")
            print(f"Descrição: {article['description']}")
            print(f"Publicado em: {datetime.fromisoformat(article['publishedAt']).strftime(DATE_MASK_BR)}\n")
            print(f"Fonte: {article['source']['name']}")
            print(f"imagem: {article['urlToImage']}")
            print(f"URL: {article['url']}\n")

            esteArtigo = {'titulo': article['title'], 'descricao': article['description'], 'autor': article['author'], 'data_publicacao': article['publishedAt'], 'fonte': article['source']['name'], 'url_artigo': article['url'], 'url_imagem': article['urlToImage'], 'conteudo': article['content'], 'dt_publicacao': article['publishedAt']}
            artigos.append(esteArtigo)

            #print(f"\nArtigo: {esteArtigo}\n\n")
            # 'data_publicacao': datetime.fromisoformat(article['publishedAt']).strftime(DATE_MASK_BR)
            #print(f"\nJSON: {article}\n\n")

        print(f"\nQuantidade de Artigos: {data['totalResults']}\n")
    else:
        print("Error:", data.get('message'))

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
