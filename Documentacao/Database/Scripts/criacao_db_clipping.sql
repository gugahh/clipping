/**
 * Base para o sistema de Clipping, usando SQLite.
 * (C) 2026 Gustavo Santos - gugahh.br@gmail.com
 
 * OBS: A base de dados do SQLite deve ser criada na pasta "raiz" SQLite, com o nome de "clipping_db.db".
 */ 
CREATE TABLE ARTIGO
(
	ARTI_DK               INTEGER PRIMARY KEY AUTOINCREMENT ,
	ARTI_DS_TITULO        VARCHAR(300) 		NOT NULL 		, -- Titulo Original do Artigo
	ARTI_DT_LEITURA       DATE				NOT NULL 		, -- Usado nas buscas. Armazenar sem hh:mm:ss.
	ARTI_URL         	  VARCHAR(300) 		NOT NULL 		, -- deve ser UNIQUE. Serve como chave de busca.
	ARTI_DS_FONTE         VARCHAR(150)		NOT NULL 	      -- Fonte (jornal) do artigo.
);
CREATE UNIQUE INDEX ARTI_PK ON ARTIGO (ARTI_DK);
CREATE UNIQUE INDEX ARTI_URL_UK_I ON ARTIGO (ARTI_URL);
CREATE INDEX ARTI_DT_LEITURA_I ON ARTIGO(ARTI_DT_LEITURA); 

-- Cache da traducao dos artigos.
CREATE TABLE TRADUCAO_CACHE
(
	TRAC_ARTI_DK          	INTEGER PRIMARY KEY REFERENCES ARTIGO(ARTI_DK) , -- PK / FK para ARTIGO 
	TRAC_TRAD_DT_INCLUSAO	DATE				NOT NULL	, -- Dada da inclusao deste item.
	TRAC_TRAD_DS_TITULO     VARCHAR(300) 		NOT NULL	, -- Titulo Original do Artigo
	TRAC_TRAD_DS_SUBTIT     VARCHAR(1000)		NULL 		, -- Subtitulo
	TRAC_TRAD_DS_CONTEUDO  	VARCHAR(2000) 		NULL 		  -- Conteudo
);

-- TRIGGER: Exclui cache de traducao quando o artigo e excluido.
CREATE TRIGGER ARTIGO_BD
BEFORE DELETE ON ARTIGO 
FOR EACH ROW
BEGIN
    DELETE FROM TRADUCAO_CACHE 
	WHERE TRAC_ARTI_DK = OLD.ARTI_DK;
END;
