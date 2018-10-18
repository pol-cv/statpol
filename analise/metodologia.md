# Metodologia

## Como os dados foram considerados

Foram coletados os dados dos deputados federais mais votados nos estados mais populosos do Brasil (SP, RJ e MG), com a ferramenta `statpol`.

Para cada deputado foi considerado o período em que ele esteve na câmara. Devido a limitações na API **Dados Abertos** e de situações difíceis de contornar facilmente (exemplo: Tiririca renunciou antes do fim do mandato), foi considerado o período da legislatura como o tempo entre o primeiro e o último evento registrado (proposição). Exemplos:

* Tiririca: 7 anos e 13 meses, entre 7 de junho de 2011 e 3 de julho de 2018
* Jair Bolsonaro: 27 anos e 13 meses, entre 2 de março de 1991 e 27 de abril de 2018.

Observe que esse período não corresponde ao inicio ou fim de legislatura, e chamaremos de *limites de tempo efetivo de legislatura* (**LTEL**). Além disso, se o deputado passou um período fora da Câmara, especialmente se não foi reeleito ou eleito para outro cargo, ele ficará prejudicado nas estatísticas geradas. Esse não foi o caso de nenhum dos deputados analisados.

Considerando o tempo, a análise de desempenho considerou o número de eventos encontrados em função do LTEL, indicando qual é o temp o médio necessário para geração de um evento. Todos os eventos foram computados, dando maior atenção a *projetos aprovados* e a *relatórios e comunicações*. Deve-se levar em consideração que *relatórios de comunicações* podem incluir eventos pouco relevantes como a elaboração de um memorando para alguém ou uma reclamação formal.

Todos os eventos são organizados no **Dados Aberto** de uma maneira particular e muito detalhada que não permite análises mais justas. Por este motivo, foi desenvolvida essa organização que mapeia diversos tipos de proposições para a classificação sugerida. 

O detalhamento sobre a classificação usada pode ser encontrado no arquivo `dados/categorias.json`. Basicamente, ele descreve o mapeamento entre os dados `/referencias/tiposProposicao` da [API Dados Abertos](https://dadosabertos.camara.leg.br/swagger/api.html) e a classificação adotada neste trabalho.

## Dificuldades

Estabelecer quando um projeto foi aprovado não é não simples com possa parecer. Encontramos projetos aprovados que estavam identificados de maneiras diferentes no **Dados Abertos**. Da mesma forma, não encontramos a indicação de um deputado como autor de um projeto, enquanto em outras pesquisas na Câmara, ele consta como autor (problema encontrado com o Dep. Tiririca). A solução temporária, foi colocar essa informação hardcoded.

## Dúvidas

Quaisquer dúvidas ou inconsistências, por favor, entre em contato por email: **`pol-cv@protonmail.com`**
