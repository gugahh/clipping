from datetime import date
import sqlite3
import traceback

# Caminho para o seu banco de dados SQLite.
# Se o arquivo não existir, ele será criado automaticamente na primeira execução.
DB_FILE = "SQLite/clipping_db.db"

def open_connection():
    """
    Abre uma conexão com o banco de dados SQLite.
    Retorna a conexão aberta.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Exception as e:
        print("ERRO ao abrir conexão com o banco de dados:", str(e))
        raise "Erro abrindo conexão com o banco de dados: " + str(e)
    
def close_connection(conn):
    """
    Fecha a conexão com o banco de dados SQLite.
    """
    try:
        if conn:
            conn.close()
    except Exception as e:
        print("ERRO ao fechar conexão com o banco de dados:", str(e))
        raise "Erro fechando conexão com o banco de dados: " + str(e)

def fc_obtem_data_artigo(conn, artigo):  
    """
    Obtem a data de leitura do artigo com base na URL do artigo.
    Retorna a data de leitura do artigo ou None se o artigo não for encontrado. 
    O criterio da busca e a URL do artigo, que deve ser única.
    Para fins de otimizacao, so vamos buscar nos ultimos 30 dias.
    """
    try:
        with conn:
            cursor = conn.execute(
                """
                    SELECT ARTI_DT_LEITURA
                    FROM ARTIGO
                    where ARTI_URL = ?
                    and ARTI_DT_LEITURA >= date('now', '-30 days')
                """,
                (
                    [artigo["url_artigo"]]
                )
            )
            resultado = cursor.fetchone()
            return date.fromisoformat(resultado[0]) if resultado else None
    except Exception as e:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        print("ERRO ao obter Artigo ja existente:")
        print(erro_completo)
        return None 

def fc_insere_artigo(conn, artigo):
    """
    Persiste um artigo na tabela ARTIGO.

    Parâmetros:
        artigo (dict): Dicionário no formato:
            {
                "titulo": string,       # -> ARTI_DS_TITULO
                "url_artigo": string    # -> ARTI_URL
                "fonte": string         # -> ARTI_DS_FONTE
            }
    """
    #_criar_tabelas()  # Garante que as tabelas existem (removido)

    try:
        with conn:
            # 1. Insere o artigo
            conn.execute("INSERT INTO ARTIGO (ARTI_DS_TITULO, ARTI_URL, ARTI_DS_FONTE,ARTI_DT_LEITURA) VALUES (?, ?, ?, ?)",
                (
                    artigo["titulo"],
                    artigo["url_artigo"],
                    artigo["fonte"],
                    date.today().strftime('%Y-%m-%d')
                )
            )
            conn.commit()
            return "OK"
    except sqlite3.IntegrityError as e:
        # Erro de integridade (ex: URL já existe)
        print(f"ERRO de integridade ao gravar Artigo ({artigo.get('titulo', 'N/A')}): {str(e)}")
        return f"ERRO de integridade: {str(e)}"

    except Exception as e:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        mensagem_erro = f"ERRO {erro_completo}"
        print(f"ERRO ao gravar Artigo ({artigo.get('titulo', 'N/A')}):")
        print(erro_completo)
        return mensagem_erro
    
def fc_exclui_artigo(conn, artigo):
    """
    Exclui um artigo da tabela ARTIGO com base na URL do artigo.
    Parâmetros:
        - artigo (dict): Dicionário contendo a URL do artigo a ser excluído
   """
    try:
        with conn:
            conn.execute("DELETE FROM ARTIGO WHERE ARTI_URL = ?", (artigo["url_artigo"],))
            conn.commit()
            return "OK"
    except Exception as e:
        print(f"ERRO ao excluir Artigo ({artigo.get('titulo', 'N/A')}): {str(e)}")
        return f"ERRO ao excluir Artigo: {str(e)}"
    
def fc_insere_traducao_cache(conn, artigo):
    """
    Persiste um artigo na tabela TRADUCAO_CACHE.

    Parâmetros:
        artigo (dict): Dicionário no formato:
            {
                "id_artigo": numeric,       # -> TRAC_ARTI_DK
                "titulo_traduzido": string    # -> TRAC_TRAD_DS_TITULO
                "descricao_traduzida": string         # -> TRAC_TRAD_DS_SUBTIT
                "conteudo_traduzido": string         # -> TRAC_TRAD_DS_CONTEUDO
            }
    """
    try:
        with conn:
            # 1. Insere o artigo
            conn.execute("INSERT INTO TRADUCAO_CACHE (TRAC_ARTI_DK, TRAC_TRAD_DT_INCLUSAO, TRAC_TRAD_DS_TITULO, TRAC_TRAD_DS_SUBTIT, TRAC_TRAD_DS_CONTEUDO) VALUES (?, ?, ?, ?, ?)",
                (
                    artigo["id_artigo"],
                    date.today().strftime('%Y-%m-%d %H:%M:%S'),
                    artigo["titulo_traduzido"],
                    artigo["descricao_traduzida"],
                    artigo["conteudo_traduzido"]
                )
            )
            conn.commit()
            return "OK"
    except sqlite3.IntegrityError as e:
        # Erro de integridade (ex: URL já existe)
        print(f"ERRO de integridade ao gravar Artigo Cache ({artigo.get('titulo', 'N/A')}): {str(e)}")
        return f"ERRO de integridade: {str(e)}"

    except Exception as e:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        mensagem_erro = f"ERRO {erro_completo}"
        print(f"ERRO ao gravar Artigo Cache ({artigo.get('titulo', 'N/A')}):")
        print(erro_completo)
        return mensagem_erro
    
def fc_exclui_traducao_cache(conn, id_artigo):
    """
    Exclui uma tradução do cache com base no ID do artigo.
    Parâmetros:
        - id_artigo (int): ID do artigo a remover do cache de traduções
    """
    try:
        with conn:
            conn.execute("DELETE FROM TRADUCAO_CACHE WHERE TRAC_ARTI_DK = ?", (id_artigo,))
            conn.commit()
            return "OK"
    except Exception as e:
        print(f"ERRO ao excluir Tradução do Cache (id: {id_artigo}): {str(e)}")
        return f"ERRO ao excluir Tradução do Cache: {str(e)}"

def fc_obtem_traducao_cache(conn, id_artigo):
    """
    Obtém um artigo da tabela TRADUCAO_CACHE com base no ID do artigo.
    Parâmetros:
        - id_artigo (int): ID do artigo a obter do cache de traduções
    """
    try:
        with conn:
            cursor = conn.execute("SELECT TRAC_TRAD_DS_TITULO, TRAC_TRAD_DS_SUBTIT, TRAC_TRAD_DS_CONTEUDO FROM TRADUCAO_CACHE WHERE TRAC_ARTI_DK = ?", (id_artigo,))
            reg = cursor.fetchone()
            return {"titulo_traduzido": reg[0], "descricao_traduzida": reg[1], "conteudo_traduzido": reg[2]} if reg else None
    except Exception as e:
        print(f"ERRO ao obter Artigo do Cache (id: {id_artigo}): {str(e)}")
        return f"ERRO ao obter Artigo do Cache: {str(e)}"

if __name__ == "__main__":
    try:
        # Testes 
        conn = open_connection()

        #Massa de teste
        #Nao existe na base de teste
        artigo_teste1 = {
            "titulo": "Teste de Artigo",
            "url_artigo": 'http://exemplo.com/artigo-teste',
            "fonte": "Fonte Exemplo"
        }
        #EXISTE na base de teste
        artigo_teste2 = {
            "titulo": "Um titulo bacana",
            "url_artigo": 'http://umaUrl.com/12',
            "fonte": "The NY Herald"
        }
        

        # 1. Teste Negativo: Consulta artigo 
        #print(f"\nURL: {artigo_teste1['url_artigo']}")
        resultado = fc_obtem_data_artigo(conn, artigo_teste1)
        print(f"\nTeste 1 (select): {resultado} - Esperado: None")

        #2. Teste Positivo: Consulta Artigo
        #print(f"\nURL: {artigo_teste2['url_artigo']}")
        resultado = fc_obtem_data_artigo(conn, artigo_teste2)
        print(f"\nTeste 2 (select): {resultado} - Esperado: data valida.")
        print(f"Tipo de Resultado: {type(resultado)} - Esperado: datetime.date")

        #3. Teste de Inserção: Insere artigo
        resultado = fc_insere_artigo(conn, artigo_teste1)
        print("\nTeste 3 (Inserção):", resultado)

        #4. Verifica a data do artigo recem inserido (deve ser a data atual)
        resultado = fc_obtem_data_artigo(conn, artigo_teste1)
        print(f"\nTeste 4: {resultado} - Esperado: {date.today().strftime('%Y-%m-%d')}.")
        print(f"Tipo de Resultado: {type(resultado)} - Esperado: datetime.date")

        #5. Teste de Exclusão: Exclui artigo
        resultado = fc_exclui_artigo(conn, artigo_teste1)       
        print(f"\nTeste 5 (Exclusão): Resultado: {resultado} - esperado: OK")

        #6. Teste de Exclusão: Verificacao da exclusao do artigo (deve retornar None)
        resultado = fc_obtem_data_artigo(conn, artigo_teste1)       
        print(f"\nTeste 6 (Verificação da Exclusão): Resultado: {resultado} - esperado: None")

        #7. Teste de Cache: Insere artigo no cache
        trad_cache_test = {
            "id_artigo": 28,  # id Real de artigo na base
            "titulo_traduzido": "Título Traduzido",
            "descricao_traduzida": "Descrição Traduzida",
            "conteudo_traduzido": "Conteúdo Traduzido"
        }
        resultado = fc_insere_traducao_cache(conn, trad_cache_test)
        print(f"\nTeste 7 (Inserção no Cache): {resultado} - Esperado: OK")

        #8. Teste de Cache: Obtem artigo do cache de traducoes
        resultado = fc_obtem_traducao_cache(conn, 28)
        print(f"\nTeste 8 (Obtenção do Cache): {resultado} - Esperado: Dicionário com as traduções do artigo")

        #9. Teste de Cache: Exclui artigo do cache de traducoes
        result = fc_exclui_traducao_cache(conn, 28) 
        print(f"\nTeste 9 (Exclusão do Cache): {result} - Esperado: OK")

        close_connection(conn)

    except Exception:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        mensagem_erro = f"ERRO {erro_completo}"
        print(erro_completo)



    
