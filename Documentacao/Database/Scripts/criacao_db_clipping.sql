/**
 * Base para o sistema de Clipping, usando SQLite.
 * (C) 2026 Gustavo Santos - gugahh.br@gmail.com
 
 * OBS: A base de dados do SQLite deve ser criada na pasta "raiz" SQLite, com o nome de "clipping_db.db".
 */ 
 -- DROP TABLE ARTIGO 
-- VERSAO NOVA
CREATE TABLE ARTIGO
(
	ARTI_DK               INTEGER PRIMARY KEY AUTOINCREMENT 	,
	ARTI_DT_LEITURA       DATE				NOT NULL 		, -- Usado nas buscas. Armazenar sem hh:mm:ss.
	ARTI_DS_FONTE         VARCHAR(150)		NOT NULL 	    ,  -- Fonte (jornal) do artigo.
	ARTI_URL         	  VARCHAR(300) 		NOT NULL 		, -- deve ser UNIQUE. Serve como chave de busca.
	ARTI_DS_TITULO_ORIG   VARCHAR(300) 		NOT NULL 		, -- Titulo Original do Artigo
	ARTI_DS_TITULO_TRAD     VARCHAR(300) 	NOT NULL			, -- Titulo Traduzido do Artigo
	ARTI_DS_DESCR_TRAD     VARCHAR(1000)		NULL 		, -- Descrição (Subtitulo) Traduzido
	ARTI_DS_CONTEUDO_TRAD  	VARCHAR(2000) 		NULL 		  -- Conteudo Traduzido
);
CREATE UNIQUE INDEX ARTI_PK ON ARTIGO (ARTI_DK);
CREATE UNIQUE INDEX ARTI_URL_UK_I ON ARTIGO (ARTI_URL);
CREATE INDEX ARTI_DT_LEITURA_I ON ARTIGO(ARTI_DT_LEITURA); 
