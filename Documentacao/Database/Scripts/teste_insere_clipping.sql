Insert into ARTIGO
(
	ARTI_DS_TITULO        ,
	ARTI_DT_LEITURA       ,
	ARTI_URL         	  ,
	ARTI_DS_FONTE         
)
values 
(
	'Um titulo bacana'		, 
	date('now')				,
	'http://umaUrl.com/12'	,
	'The NY Herald'
);

-- Conferencia 
SELECT * FROM ARTIGO;

