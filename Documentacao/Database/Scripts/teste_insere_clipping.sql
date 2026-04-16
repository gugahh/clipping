Insert into ARTIGO
(
	ARTI_DS_TITULO_ORIG   ,
	ARTI_DT_LEITURA       ,
	ARTI_URL         	  ,
	ARTI_DS_FONTE         ,
	ARTI_DS_TITULO_TRAD   ,
	ARTI_DS_DESCR_TRAD    ,
	ARTI_DS_CONTEUDO_TRAD 
)
values 
(
	'Um titulo bacana'		, 
	date('now')				,
	'http://umaUrl.com/12'	,
	'The NY Herald'			,
	'Título Traduzido'		,
	'Descrição Traduzida'	,
	'Conteúdo Traduzido'
);

-- Conferencia 
SELECT * FROM ARTIGO;

