-- Testa a tabela de cache de traducao

insert into TRADUCAO_CACHE
(
	TRAC_ARTI_DK          	,
	TRAC_TRAD_DT_INCLUSAO	,
	TRAC_TRAD_DS_TITULO     ,
	TRAC_TRAD_DS_SUBTIT     ,
	TRAC_TRAD_DS_CONTEUDO  	
)
values
(
	39						, 
	date('now')				,
	'Title: A Superpower Besieged: America Acts Like a Cornered Animal — and the World Will Pay the Price' ,
	'Subtitle: A Superpower Besieged: America Acts Like a Cornered Animal — and the World Will Pay the Price' ,
	'Content: A Superpower Besieged: America Acts Like a Cornered Animal — and the World Will Pay the Price'
);

Select * from TRADUCAO_CACHE where TRAC_ARTI_DK = 39;

-- Testando o trigger (delete cascade).
Delete from ARTIGO where ARTI_DK = 39;

