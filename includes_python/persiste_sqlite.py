from datetime import date, datetime, timedelta
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

def fc_obtem_artigo(conn, artigo):  
    """
    Obtem dados do artigo com base na URL do artigo.
    Retorna um dicionário com os dados do artigo ou None se não encontrado.
    O dicionário retornado tem a seguinte estrutura:
    {
        "id": int,          # -> ARTI_DK
        "dt_leitura": date  # -> ARTI_DT_LEITURA 
        "titulo": string    # -> ARTI_DS_TITULO_ORIG
        "titulo_traduzido": string  # -> ARTI_DS_TITULO_TRAD
        "descricao_traduzida": string  # -> ARTI_DS_DESCR_TRAD
        "conteudo_traduzido": string  # -> 	ARTI_DS_CONTEUDO_TRAD  
    O criterio da busca e a URL do artigo, que deve ser única.
    """
    try:
        with conn:
            cursor = conn.execute(
                """
                    SELECT 	ARTI_DK, ARTI_DT_LEITURA, ARTI_DS_TITULO_ORIG, ARTI_DS_TITULO_TRAD, ARTI_DS_DESCR_TRAD, ARTI_DS_CONTEUDO_TRAD
                    FROM ARTIGO
                    where ARTI_URL = ?
                """,
                (
                    [artigo["url_artigo"]]
                )
            )
            resultado = cursor.fetchone()
            return {"id": resultado[0], 
                    "dt_leitura": date.fromisoformat(resultado[1]), 
                    "titulo": resultado[2], 
                    "titulo_traduzido": resultado[3], 
                    "descricao_traduzida": resultado[4], 
                    "conteudo_traduzido": resultado[5] 
                    }  if resultado else None
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
                "titulo": string        # -> ARTI_DS_TITULO_ORIG
                "url_artigo": string    # -> ARTI_URL
                "fonte": string         # -> ARTI_DS_FONTE
                "dt_leitura": date      # -> ARTI_DT_LEITURA 
                "titulo_traduzido": string      # -> ARTI_DS_TITULO_TRAD
                "descricao_traduzida": string   # -> ARTI_DS_DESCR_TRAD
                "conteudo_traduzido": string    # -> 	ARTI_DS_CONTEUDO_TRAD  
            }
    Retorna: uma tupla com o resultado da operação. 
    Se a inserção for bem-sucedida, retorna ("OK", id_artigo), 
    onde id_artigo é o ID do artigo recém-inserido. Em caso de erro, retorna ("ERRO", mensagem_erro).
    """
    #_criar_tabelas()  # Garante que as tabelas existem (removido)

    try:
        with conn:
            # 1. Insere o artigo
            cursor = conn.execute(
                """
                INSERT INTO ARTIGO 
                (
                    ARTI_DS_TITULO_ORIG, 
                    ARTI_URL,
                    ARTI_DS_FONTE, 
                    ARTI_DT_LEITURA, 
                    ARTI_DS_TITULO_TRAD, 
                    ARTI_DS_DESCR_TRAD, 
                    ARTI_DS_CONTEUDO_TRAD
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artigo["titulo"],
                    artigo["url_artigo"],
                    artigo["fonte"],
                    date.today().strftime('%Y-%m-%d'),
                    artigo["titulo_traduzido"],
                    artigo["descricao_traduzida"],
                    artigo["conteudo_traduzido"]
                )
            )
            conn.commit()
            lastrowid = cursor.lastrowid  # Retorna o Id do registro criado
            return ("OK", lastrowid)
    except sqlite3.IntegrityError as e:
        # Erro de integridade (ex: URL já existe)
        print(f"ERRO de integridade ao gravar Artigo ({artigo.get('titulo', 'N/A')}): {str(e)}")
        return ("ERRO", f"ERRO de integridade: {str(e)}")

    except Exception as e:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        mensagem_erro = f"ERRO {erro_completo}"
        print(f"ERRO ao gravar Artigo ({artigo.get('titulo', 'N/A')}):")
        print(erro_completo)
        return mensagem_erro
    
def fc_exclui_artigo(conn, id_artigo):
    """
    Exclui um artigo da tabela ARTIGO com base na URL do artigo.
    Parâmetros:
        - id_artigo (int): ID do artigo a ser excluído
    """
    try:
        with conn:
            conn.execute("DELETE FROM ARTIGO WHERE ARTI_DK = ?", (id_artigo,))
            conn.commit()
            return "OK"
    except Exception as e:
        print(f"ERRO ao excluir Artigo (ID: {id_artigo}): {str(e)}")
        return f"ERRO ao excluir Artigo: {str(e)}"
    
def fc_exclui_artigos_antigos(conn, recuo):
    """
    Exclui todos os artigos na base com data igual ou anterior ao recuo;
    Isso eh usado para otimizar a base no SQLite, mantendo-a pequena.
    Parâmetros:
        - recuo (int): Numero de dias de recuo.
    """
    if(recuo == None or recuo < 0):
        msg = "ERRO. Parametros recuo deve ser um inteiro positivo."
        print(msg)
        raise msg

    data_de_corte_str = (datetime.now() - timedelta(days=recuo)).strftime('%Y-%m-%d')

    try:
        with conn:
            conn.execute("DELETE FROM ARTIGO WHERE ARTI_DT_LEITURA < ?", (data_de_corte_str,))
            conn.commit()
            return "OK"
    except Exception as e:
        print(f"ERRO ao excluir Artigos  antigos (Recuo: {recuo}): {str(e)}")
        return f"ERRO ao excluir Artigo: {str(e)}"



if __name__ == "__main__":
    try:
        # Testes 
        conn = open_connection()

        #Massa de teste
        #Nao existe na base de teste
        artigo_teste1 = {
            "titulo": "Teste de Artigo",
            "url_artigo": 'http://exemplo.com/artigo-teste',
            "fonte": "Fonte Exemplo",
            "titulo_traduzido": "Titulo Traduzido",
            "descricao_traduzida": "Descricao Traduzida",
            "conteudo_traduzido": "Conteúdo Traduzido"
        }
        #EXISTE na base de teste
        artigo_teste2 = {
            "titulo": "Um titulo bacana",
            "url_artigo": 'http://umaUrl.com/12',
            "fonte": "The NY Herald"
        }
        

        # 1. Teste Negativo: Consulta artigo 
        #print(f"\nURL: {artigo_teste1['url_artigo']}")
        resultado = fc_obtem_artigo(conn, artigo_teste1)
        print(f"\nTeste 1 (select): {resultado} - Esperado: None")

        #2. Teste Positivo: Consulta Artigo
        #print(f"\nURL: {artigo_teste2['url_artigo']}")
        resultado = fc_obtem_artigo(conn, artigo_teste2)
        print(f"\nTeste 2 (select): {resultado} - Esperado: dados válidos.")
        print(f"Tipo de Resultado: {type(resultado)} - Esperado: dict")

        #3. Teste de Inserção: Insere artigo
        resultado = fc_insere_artigo(conn, artigo_teste1)
        print("\nTeste 3 (Inserção):", resultado)

        #4. Verifica a data do artigo recem inserido (deve ser a data atual)
        resultado_inc = fc_obtem_artigo(conn, artigo_teste1)
        print(f"\nTeste 4: {resultado_inc} - Esperado: {date.today().strftime('%Y-%m-%d')}.")
        print(f"Tipo de Resultado: {type(resultado_inc)} - Esperado: Data.")

        #5. Teste de Exclusão: Exclui artigo recem-criado
        resultado = fc_exclui_artigo(conn, resultado_inc["id"])       
        print(f"\nTeste 5 (Exclusão): Resultado: {resultado} - esperado: OK")

        #6. Teste de Exclusão: Verificacao da exclusao do artigo (deve retornar None)
        resultado = fc_obtem_artigo(conn, artigo_teste1)
        print(f"\nTeste 6 (Verificação da Exclusão): Resultado: {resultado} - esperado: OK")

        #6. Teste de Exclusao de Artigos antigos 
        resultado = fc_exclui_artigos_antigos(conn, 10)
        print(f"\nTeste 6 (Verificação da Exclusão de art. antigos): Resultado: {resultado} - esperado: OK")

        close_connection(conn)

    except Exception:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        mensagem_erro = f"ERRO {erro_completo}"
        print(erro_completo)



    
