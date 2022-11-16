# Voz Delas

_Atualizado em 16 de novembro de 2022._

O Voz Delas é uma ferramenta que aponta quantas mulheres aparecem em citações diretas em um corpo de textos em português. Foi desenvolvido pelo jornal **Folha de S.Paulo** para monitorar a participação feminina nos conteúdos do jornal.

O projeto foi um dos [vencedores do Desafio de Inovação da Google News Initiative na América Latina 2021](https://brasil.googleblog.com/2021/07/desafio-da-inovacao-gni-2021-projetos-selecionados.html).

Este repositório contém uma série de bots para monitoramento do gênero das fontes especialistas entrevistadas pela Folha, além do algoritmo que extrai os dados de pessoas diretamente citadas nos textos.

Ele inclui a estrutura que faz a recepção e tratamento dos conteúdos publicados, o algoritmo em si e o frontend para a exibição dos resultados por meio de dashboard e alertas por email.

Por fim, os nomes de mulheres extraídas do corpo de textos passam também a integrar um banco de fontes para futura consulta dos jornalistas da **Folha**, cuja estrutura também está presente neste repositório. Esses dados também são usados nos alertas disparados por email.

Todo o conteúdo está sob a licença [GNU General Public License v3.0](/LICENSE), o que significa que você pode reproduzir o Voz Delas em sua instituição.

## Objetivos

1. Reconhecer as fontes diretamente citadas em reportagens publicadas no [site](https://www1.folha.uol.com.br) da **Folha**;
1. Classificar o gênero dessas fontes;
1. Quantificar o percentual de citações atribuídas a mulheres, recortando por autor (repórter) e por seção do jornal (editoria);
1. Monitorar a evolução dessas métricas por meio de relatórios e alertas;
1. Sugerir fontes mulheres de acordo com o tópico de preferência do jornalista.

## Estrutura

O Voz Delas foi montado usando uma arquitetura de microsserviços, organizados na pasta [./system](./system). Cada subpasta é um serviço.

O sistema foi implementado originalmente na [Google Cloud Platform](https://cloud.google.com/), por isso as pastas fazem referência aos serviços Cloud Function (_cf_) e Cloud Run (_cr_).

### [./system](./system)

#### [./system/cf_data_warehouse_verification](./system/cf_data_warehouse_verification)

Cloud function responsável por verificar se os dados diários foram devidamente enriquecidos e enviados ao Data Warehouse. Se os dados no banco não condizem com os que foram recebidos para análise, dispara alerta por email.

#### [./system/cf_error_notification](./system/cf_error_notification)

Aplicação responsável por mandar email notificando existência de erro em algum dos outros sistemas do Voz Delas.

#### [./system/cr_data_transformation](./system/cr_data_transformation)

Recebe dados enviados diariamente ao bucket do Voz Delas contendo _.json_ com os textos publicados pela **Folha** nos dias anteriores.

Envia os textos para a [API CR Speaker Assignment](./system/cr_speaker_assignment/) para identificar as fontes e atualiza o [banco de fontes](./system/cr_speaker_database/).

#### [./system/cr_report_dashboard](./system/cr_report_management_front)

Frontend para visualizar os dados do Data Warehouse do projeto, como estatísticas de citações feitas a mulheres e outras informações extraídas de [./system/cr_speaker_assignment](./system/cr_speaker_assignment).

#### [./system/cr_report_notification](./system/cr_report_notification)

Gera os relatórios e alertas a serem enviados por email para repórteres, editores e para a chefia do jornal.

Inclui relatórios periódicos de desempenho em relação à proporção de mulheres citadas nos textos e alertas para o caso de um acúmulo de textos publicados sem citar uma mulher.

#### [./system/cr_speaker_assignment/](./system/cr_speaker_assignment/)

API que determina quem são as fontes (_speakers_) em citações diretas de um texto.

O input é um corpo de texto. A saída é um array com as fontes, respectivos gêneros e as citações que o algoritmo atribuiu a essa pessoa.

Quando a aplicação não identifica speakers ou gêneros, retorna a palavra "undefined".

#### [./system/cr_speaker_database](./system/cr_speaker_database)

Aplicação web para consumir dados do banco de fontes criado a partir da leitura dos textos. Nomes de _speakers_ mulheres são extraídos e integram tabela com tags de textos em que apareceram (ou seja, os assuntos sobre os quais falaram).

#### [./system/cr_speaker_database_front](./system/cr_speaker_database_front)

Frontend da aplicação web criada em [./system/cr_speaker_database](./system/cr_speaker_database).

## Detalhes

O coração do projeto é o algoritmo disposto nos arquivos [./cr_speaker_assignment/text_analysis.py](./cr_speaker_assignment/text_analysis.py) e [./cr_speaker_assignment/speaker_assignment.py](./cr_speaker_assignment/speaker_assignment.py) (veja abaixo mais detalhes sobre outras partes da estrutura e, na sequência, como funciona o algoritmo).

Esses arquivos são usados em uma API ([./cr_speaker_assignment/main.py](./cr_speaker_assignment/main.py)) que recebe os arquivos de texto e retorna um _array_ com as informações de citações extraídas, entidades a quem atribuiu e o gênero dessa entidade.

Quando a aplicação não identifica speakers ou gêneros, retorna a palavra "undefined".

[No Voz Delas, a API](./system/cr_speaker_assignment/) integra nossa arquitetura de microsserviços.

Os textos recebidos pelo sistema têm um tratamento inicial antes de serem processados pelo algoritmo do Voz Delas, parte que parcialmente se aplica exclusivamente ao formato usado pela **Folha** (extrair o conteúdo de um _.json_ específico, que contém também metadados), e outra parte aplicável a qualquer texto que passe pelo serviço. Isso inclui a remoção de alguns caracteres especiais, espaços múltiplos, bem como a checagem de que o texto enviado inclui um número par de aspas.

O texto é todo [_tokenizado_](https://monkeylearn.com/blog/named-entity-recognition/) usando a biblioteca [_Spacy_](https://spacy.io/usage/linguistic-features#tokenization). Depois, o projeto usa um modelo treinado em português da biblioteca [_Hugging Face_](https://) para o reconhecimento das entidades.

A atribuição, chave nesse processo, é feita a partir de um conjunto de regras encadeadas:

1. Verbo: procura por verbos que indicam fala, como "disse" e "afirmou", e retorna o nome mais próximo
1. Distância: procura a entidade mais próxima dentro do mesmo parágrafo da citação.
1. Nota: procura por termos como "nota" ou "assessoria" no mesmo parágrafo do par de aspas.
1. Pronome: se um pronome "ele" ou "ela" está próximo a uma fala, atribui-se à entidade de mesmo gênero mais próxima da palavra.
1. Por fim, atribui-se à entidade mais próxima citada anteriormente, respeitando-se um limite de três parágrafos.

Caso não seja possível atribuir a fala a uma pessoa usando esses critérios, o sistema retornará que não pôde fazer a classificação --indicará a palavra-chave "undefined".

Nos testes feitos no desenvolvimento desta aplicação, comparando o resultado do sistema a um corpo de 430 falas (em 66 textos) classificadas manualmente, o Voz Delas classificou corretamente cerca de 75% das citações. Nessa avaliação notou-se que o limite de três parágrafos era o ideal para minimizar os erros mantendo o máximo possível de atribuições.

Uma vez feita a atribuição, os gêneros das fontes é reconhecido através deste [banco de dados de nomes brasileiros](https://brasil.io/dataset/genero-nomes/nomes/).

### Funcionamento do algoritmo

O algoritmo do Voz Delas começa com um processamento dos textos e depois se divide em um conjunto de regras, heurísticas, que são então encadeadas para termos um output único.

#### Processamento de texto

Nessa etapa, o conteúdo inserido é tratado para que seja feita:

* Rotulação morfossintática
* Reconhecimento de entidades
* Reconhecimento de citações (texto entre pares de aspas)

Textos sem entidades ou citações não são analisados. Esses casos retornam um erro na aplicação.

#### Heurística de verbo

A mais intuitiva. A ideia é que há maior probabilidade de a entidade que corretamente falou uma citação esteja próxima do que apelidamos de um verbo de comunicação.

Identificamos se o texto contém algum desses 28 verbos: `'AFIRMA', 'AFIRMOU', 'CITA', 'CITOU', 'CONTA', 'CONTOU', 'DECLARA', 'DECLAROU', 'DESCREVE', 'DESCREVEU', 'ELUCIDA', 'ELUCIDOU', 'ESCREVE', 'ESCREVEU', 'EXPLICA', 'EXPLICOU', 'DIZ', 'DISSE', 'FALA', 'FALOU', 'FRISA', 'FRISOU', 'INFORMA', 'INFORMOU', 'LISTA', 'LISTOU', 'PONTUA', 'PONTUOU'`

Esses verbos de comunicação são atribuídos aos pares de aspas. O verbo fica associado ao par de aspas mais próximo dentro de um mesmo parágrafo.

Em seguida, procuramos por entidades na vizinhança do verbo encontrado.

#### Heurística de distância

Também intuitiva, é o baseline de muitos estudos. A ideia é atribuir fala à entidade mais próxima do par de aspas.

A distância pode ser calculada em número de termos/palavras ou parágrafos. Consideramos a proximidade em relação aos extremos da citação (começo e fim das aspas).

A busca começa pelo trecho onde estão as aspas e depois olha para trás no texto, iterando parágrafo por parágrafo.

#### Heurística de pronome

Procura por pronomes "ele" e "ela", então os vincula à entidade de mesmo gênero mais próxima.

Nessa lógica, o pronome pode ser usado para substituir a presença direta do nome da entidade no parágrafo.

#### Heurística de nota

Identifica pares de aspas que vêm de organizações, e não pessoas, o que significa que não cabe uma análise de gẽnero.

Procura pelas expressões: `'NOTA', 'COMUNICADO', 'ASSESSORIA', 'TRECHO', 'TEXTO'` e as atribui ao par de aspas mais próximo.

#### Combinação das heurísticas

No fim das contas, cada par de aspas terá resultados das entidades das quatro heurísticas descritas acima. Como atribuir a entidade final? O resultado sai do seguinte conjunto de regras:

1. Se a heurística de verbo retornou algo.
1. Se a heurística de distância retornou uma entidade e ela é do mesmo parágrafo das aspas;
1. Se a heurística de nota retornou uma entidade e ela é do mesmo parágrafo das aspas;
1. Se a heurística de pronome retornou uma entidade e ela é do mesmo parágrafo das aspas;
1. Se a heurística de nota retornou uma entidade e ela está até K=3 parágrafos antes do parágrafo das aspas;
1. Se a heurística de pronome retornou uma entidade e ela está até K=3 parágrafos antes do parágrafo das aspas;
1. Se a heurística de distância retornou uma entidade e ela está até K=3 parágrafos antes do parágrafo das aspas;
1. Se a heurística de distância retornou uma entidade e ela está distante em mais do que K=3 parágrafos antes do parágrafo das aspas nós dizemos que esse par de aspas fica indefinido ('_undefined_').

## Créditos

O Voz Delas foi desenvolvido por [Larissa Sayuri Futino](https://github.com/larissasayurifutino), [Yuri Tavares](https://github.com/vstgio), [Raphael Hernandes](https://github.com/rhhernandes) e Bruno Pereira.

O projeto contou com idealização e supervisão de Alexandra de Moraes, Camila Marques, Fábio Takahashi, Flávia Faria e Flávia Lima. Também teve o apoio da equipe de tecnologia da Folha, com Marcelo Morote e Rafael Campos. Contou ainda com o apoio de Diana Yukari, Guilherme Garcia, Irapuan Campos, Leonardo Diegues e Rubens Alencar.

### Estudos que ajudaram a embasar o projeto

* [Quotation Attribution for Portuguese News Corpora](https://fenix.tecnico.ulisboa.pt/downloadFile/395146461029/dissertacao.pdf) - Marta Quintão (Técnico Lisboa / UTL)
* [Extraction, Attribution, and Classification of Quotations in Newspaper Articles](https://fenix.tecnico.ulisboa.pt/downloadFile/281870113704383/Thesis_Report.pdf) - João Daniel Fernandes Godinho (Técnico Lisboa / UTL)
* [Quote Extraction and Analysis for News](https://research.signal-ai.com/assets/RnD_at_the_BBC__and_quotes.pdf) - Chris Newell, Tim Cowlishaw, David Man (BBC Research & Development)
* [Quotebank: A Corpus of Quotations from a Decade of News](https://dl.acm.org/doi/10.1145/3437963.3441760) - Timoté Vaucher, Andreas Spitz, Robert West (EPFL), Michele Catasta (Universidade Stanford)
* [Direct Quote: a dataset for direct quotation extraction and attribution in news articles](https://arxiv.org/abs/2110.07827) - Yuanchi Zhang, Yang Liu (Departamento de Ciência da Computação e Tecnologia, Universidade Tsinghua)

### Outros repositórios

* [BERTimbau - Portuguese BERT](https://github.com/neuralmind-ai/portuguese-bert)
* [CS224u: Natural Language Understanding](https://github.com/cgpotts/cs224u)
* [DirectQuote](https://github.com/THUNLP-MT/DirectQuote)
* [Quootstrap](https://github.com/epfl-dlab/quootstrap)
* [Repositório do Livro NLP with Transformers (Transformers Notebooks)](https://github.com/nlp-with-transformers/notebooks)
