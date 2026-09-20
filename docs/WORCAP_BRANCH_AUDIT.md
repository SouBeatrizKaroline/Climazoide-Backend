# Auditoria técnica da pesquisa WORCAP-2026

Auditoria registrada em **19 de setembro de 2026, às 22:16:28 (BRT, UTC−03:00)**.
O repositório de pesquisa foi consultado somente para leitura. A lista remota
confirmada contém oito branches; os commits examinados localmente eram os refs
disponíveis até 17/09/2026. Nenhum arquivo de dados binário oficial nem CSV final
estava disponível para perícia independente. As regras temporais fornecidas pela
equipe foram tratadas como requisito da auditoria.

## Resultado

**Problema crítico: a branch consolidada mais recente não comprova uma previsão
legítima de um mês à frente.** Para prever o mês `T`, o contrato é usar apenas
informação originada e publicada até o instante de emissão definido no mês `T−1`.
O pipeline consolidado associa variáveis atmosféricas do mês-alvo à precipitação
desse mesmo mês no construtor de exemplos. As métricas resultantes não devem ser
apresentadas como desempenho de previsão `T−1 → T`.

Há correção de deslocamento nas branches `Beatriz` e `vermelho`, mas ela não está
na branch consolidada mais recente nem na `main`. É necessário integrar/revisar o
alinhamento e refazer treino, validação e inferência antes de qualquer promoção.

## Achados temporais

| Componente | Evidência | Decisão |
| --- | --- | --- |
| Treino/validação na branch mais recente | `src/data.py` seleciona atmosfera no índice `alvo_idx` e `TP[alvo_idx]` como alvo | **Bloqueado:** usa atmosfera de `T`, não de `T−1` |
| Branches `Beatriz` e `vermelho` | Implementam índice de feature `alvo_idx − 1` | Referências de correção; ainda exigem integração e nova validação da versão final |
| Features do teste | O contrato informado associa cada alvo `T` a `time_origem = T−1` | Não foi encontrada dependência automática da linha posterior para prever a anterior; faltam assertions de origem no carregador |
| ONI | Índice centrado em três meses é atribuído ao mês central e usado como feature | **Bloqueado:** para `T−1`, pode incluir SST observada em `T`; série revisada não prova disponibilidade no instante histórico |
| Scaler/PCA/PLS/climatologia | Ajustes examinados usam dados até `2018-12` | Não foi identificado ajuste sobre 2023/2024; no retreino final, reajustar somente dentro de cada fold temporal |
| EDA do teste | Estatísticas agregadas consultam múltiplas linhas do teste, mas não foram vistas alimentando inferência | Risco de análise transdutiva/manual; isolar do pipeline de decisão e documentar |

Médias mensais ERA5T geralmente são publicadas alguns dias após o fim do mês, e
os valores finais podem ser revisados posteriormente. Portanto, se a regra exigir
literalmente disponibilidade até o fim de `T−1`, o uso de uma média mensal ERA5
completa de `T−1` requer esclarecer o horário de emissão ou usar fonte disponível
naquele corte. Fontes: [documentação ECMWF ERA5](https://confluence.ecmwf.int/pages/viewpage.action?pageId=669811810)
e [NOAA CPC ONI](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/).

## Alvo e avaliação

Não foi encontrada no código versionado consulta/download explícito da precipitação
real de 2023–2024, nem uso visível de `tp_alvo` do teste na inferência. A busca no
código não indicou chamadas à CDS API para recuperar o alvo. Isso **não certifica**
arquivos binários ausentes: nenhum NetCDF/CSV oficial foi submetido a inspeção
forense independente, e não se deve baixar o alvo real para esta verificação.

A fórmula do RMSE observada é correta para uma grade completa e pesos iguais, mas
as métricas atuais são inutilizáveis como validação M→M+1 devido ao desalinhamento.
A validação é cronológica; o embaralhamento do DataLoader ocorre somente entre
amostras já atribuídas ao treino. Separar e reportar explicitamente horizonte de
um mês (`lag=1`) e executar avaliação walk-forward após corrigir o pipeline.
Também foram observadas métricas divergentes em arquivos de resultado sem hash de
código/execução que permita explicar a diferença.

## Estado das branches

O catálogo completo, commits e resumo de contribuição está em
[`artifacts/research_catalog.json`](../artifacts/research_catalog.json) e na rota
`GET /v1/research/branches`. Pontos que afetam prontidão:

- `feature/melhorar-pls-lstm-daiane` é a mais recente no snapshot examinado, mas
  mantém o desalinhamento atmosférico e inclui o experimento ONI não validado.
- `feature/xgboost-v3-daiane` não deve ser descrita como validada “sem vazamento”:
  seu construtor de exemplos no snapshot usa atmosfera do mês-alvo.
- `vermelho` contém correção de deslocamento no snapshot examinado; não equivale a
  uma release retreinada, reproduzida e aprovada.
- ConvLSTM não está integrado como pipeline treinado e reproduzível na branch
  consolidada. Não deve ser mostrado como modelo pronto para treinamento sem essa
  comprovação.

## Submissão e prontidão

Não havia CSV final no workspace. Logo, não foi possível confirmar contagem,
ordem, unicidade/cobertura dos IDs, valores finitos, associação ID-previsão ou
RMSE oficial. O validador da API exige o template de IDs, ordem e valores finitos
não negativos; agora também exige aprovação explícita da auditoria científica e
uma comprovação automatizada do contrato temporal antes de servir CSV completo ou
parcial.

O parcial deve conter somente previsões válidas já disponíveis para IDs oficiais,
na ordem original; não é um recorte experimental arbitrário. O CSV de exemplo é
apenas ilustrativo e não pode ser submetido.

## Próximas condições para promoção

1. Corrigir `atmosfera T−1 → alvo TP T` na branch científica escolhida.
2. Definir o instante real de emissão e comprovar disponibilidade/vintage das fontes.
3. Remover ONI centrado ou reconstruí-lo com dados estritamente disponíveis no corte.
4. Retreinar, revalidar temporalmente por walk-forward e registrar métricas com hash.
5. Publicar artefato de inferência reproduzível e executar testes de invariância
   temporal, alinhamento de origem e integridade dos IDs.
6. Gerar CSV a partir dos IDs oficiais e validar cobertura, ordem, unicidade,
   finitude e unidade antes de habilitar download.

Esta auditoria descreve pesquisa; não promove métricas, pesos ou previsões para
produção. Código e artefatos de pesquisa não foram copiados para o produto.

## Atualização posterior no Climazoide

Em **19 de setembro de 2026, às 22:56:51 (BRT, UTC−03:00)**, após a obtenção dos
13 arquivos oficiais pelo canal da competição, o backend validou dimensões,
coordenadas, `time_origem`, ausência de `tp_alvo` no teste e a ordem dos IDs. Para
não promover o pipeline crítico descrito acima, foi implementado um baseline
independente de climatologia mensal:

- ajuste final: precipitação oficial de 1940–2022;
- validação temporal: ajuste em 1940–2018 e holdout em 2019–2022;
- RMSE interno: 1,882056 mm/dia em 3.770.928 observações;
- saída: 1.885.464 linhas para janeiro de 2023 a dezembro de 2024;
- alvo real de 2023–2024: não acessado e não incluído;
- integridade: IDs oficiais preservados, valores finitos e não negativos, hashes
  registrados em `artifacts/submission_report.json`.

Essa atualização cria uma submissão baseline reproduzível no repositório de destino.
Ela não muda o veredito sobre as branches do WORCAP, não copia código GPL e não
representa pontuação oficial nem um modelo que já supere a climatologia.
