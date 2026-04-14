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

def fc_verifica_artigo_existente(conn, artigo):  
    """
    Verifica se um determinado artigo já existe, com data anterior a de hoje.
    Artigos cadastrados na data de hoje devem ser ignorados.
    O criterio da busca e a URL do artigo, que deve ser única.
    """
    try:
        with conn:
            cursor = conn.execute(
                """
                    SELECT count(*) 
                    FROM ARTIGO
                    where ARTI_URL = ?
                    and date(ARTI_DT_LEITURA) < date('now')
                """,
                (
                    [artigo["url_artigo"]]
                )
            )
            resultado = cursor.fetchone()
            return True if resultado[0] > 0 else False
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
        

        #Teste Negativo: Consulta artigo 
        #print(f"\nURL: {artigo_teste1['url_artigo']}")
        resultado = fc_verifica_artigo_existente(conn, artigo_teste1)
        print(f"Resultado do teste de verificação 1: {resultado} - Esperado: False")

        #Teste Positivo: Consulta Artigo
        #print(f"\nURL: {artigo_teste2['url_artigo']}")
        resultado = fc_verifica_artigo_existente(conn, artigo_teste2)
        print(f"Resultado do teste de verificação 2: {resultado} - Esperado: True")

        #Teste de Inserção: Insere artigo
        resultado = fc_insere_artigo(conn, artigo_teste1)
        print("Resultado do teste de insercao:", resultado)

        #Teste de Exclusão: Exclui artigo
        resultado = fc_exclui_artigo(conn, artigo_teste1)       
        print("Resultado do teste de exclusao:", resultado)

        close_connection(conn)

    except Exception:
        # Erro: imprime no console + retorna "ERROR" + stack trace
        erro_completo = traceback.format_exc()
        mensagem_erro = f"ERRO {erro_completo}"
        print(erro_completo)



    
