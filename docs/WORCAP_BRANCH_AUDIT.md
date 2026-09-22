# Auditoria técnica da pesquisa WORCAP-2026

Auditoria atualizada em **22 de setembro de 2026, às 18:24:09 (BRT, UTC−03:00)**.
O repositório de pesquisa foi consultado somente para leitura. A lista remota
confirmada contém oito branches. A nova leitura incluiu `main@2813ee6`,
`vermelho@6101abb` e `feature/melhorar-pls-lstm-daiane@c58d1cb`, publicados em
22/09/2026. O checkout local da origem permaneceu em `main@fac2fa7`, limpo e 25
commits atrás das referências remotas; nenhum push, commit, checkout ou alteração de
arquivo foi feito na origem. As regras temporais fornecidas pela equipe foram tratadas
como requisito da auditoria.

## Resultado

**Precisa de ajustes: a atualização introduz uma validação temporal mais forte, mas o
artefato apontado como final ainda não é promovível.** Para prever o mês `T`, o contrato
é usar apenas informação originada e publicada até o instante de emissão definido no
mês `T−1`. A `main@2813ee6` incorporou cinco cortes walk-forward, modelos de anomalia
e encolhimento em direção à climatologia. O melhor blend **sem ONI** registrado no
relatório alcança RMSE-CV LOFO `1,780512`; porém não há CSV final versionado nem score
oficial. O blend indicado como final usa ONI trimestral centrado e permanece bloqueado.
Nenhum artefato da origem substitui o baseline ou o XGBoost independente do Climazoide.

## Achados temporais

| Componente | Evidência | Decisão |
| --- | --- | --- |
| Treino/validação em `vermelho@6101abb` | `src/data.py` seleciona atmosfera em `feature_idx = alvo_idx − 1` e `TP[alvo_idx]` como alvo | **Alinhamento básico conforme:** atmosfera de `T−1` para prever `T` |
| `main@2813ee6` | Integra correção T−1, CV walk-forward de cinco cortes, anomalias e shrinkage | Avanço metodológico pertinente; os resultados continuam pesquisa |
| Features do teste | O contrato informado associa cada alvo `T` a `time_origem = T−1` | Não foi encontrada dependência automática da linha posterior para prever a anterior; faltam assertions de origem no carregador |
| ONI no blend final | `final_blend.py` usa ONI associado a `T−1`, mas `src/oni.py` declara temporadas trimestrais centradas | **Bloqueado:** o ONI centrado em `T−1` incorpora o mês `T`; a melhora de CV não remove essa violação |
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

A fórmula do RMSE observada é correta para uma grade completa. O relatório novo usa
cinco dobras cronológicas, com cortes de treino em 1969, 1979, 1989, 2009 e 2018, e
avalia o encolhimento leave-one-fold-out. O melhor modelo individual sem ONI registra
`1,781878`; o melhor blend sem ONI presente no relatório registra `1,780512`. O arquivo
separado que aponta `1,778058` como melhor combinação inclui ONI e, portanto, não passa
no corte temporal. Esses valores não são pontuação pública ou privada e não devem ser
tratados como score esperado. A origem não versiona o CSV final gerado, impedindo
validar IDs, hashes e a associação exata entre previsão e linha oficial.

## Estado das branches

O catálogo completo, commits e resumo de contribuição está em
[`artifacts/research_catalog.json`](../artifacts/research_catalog.json) e na rota
`GET /v1/research/branches`. Pontos que afetam prontidão:

- `vermelho@6101abb` é a referência remota mais recente. Os commits posteriores ao
  merge de `main` reorganizam o repositório e documentam no notebook o blend enviado;
  o commit final acrescenta uma legenda reproduzível para as configurações da CV.
- `main@2813ee6` incorporou a CV walk-forward e o blend, mas não os commits posteriores
  de organização e documentação de `vermelho`.
- `feature/melhorar-pls-lstm-daiane@c58d1cb` corrigiu o ensemble PCA/PLS, adicionou
  bagging ao XGBoost e implementou o treino ConvLSTM com `feature_idx = alvo_idx − 1`.
  O ensemble XGBoost + LSTM registra RMSE interno `1,871368` em protocolo diferente e
  não diretamente comparável ao XGBoost do Climazoide; o ConvLSTM possui histórico de
  treino, porém não versiona `metrics.json` nem submissão final.
- `feature/xgboost-v3-daiane` não deve ser descrita como validada “sem vazamento”:
  seu construtor de exemplos no snapshot usa atmosfera do mês-alvo.
- O blend sem ONI é a linha de pesquisa temporalmente aceitável. O blend final com ONI
  centrado não é aceito, ainda que sua CV seja numericamente melhor.

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

1. Manter a correção já implementada de `atmosfera T−1 → alvo TP T`.
2. Preservar a CV walk-forward e reportar separadamente modelos sem ONI.
3. Remover ONI centrado do blend final ou reconstruí-lo com vintage estritamente disponível no corte.
4. Validar os 24 meses na mesma geometria e no mesmo peso do teste oficial.
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

Em **20 de setembro de 2026**, o repositório de destino também implementou,
independentemente, o `xgboost-anomaly-v1`. Ele usa atmosfera de `T−1`, precipitação
congelada na origem e nenhum dado externo. Em 3.770.928 previsões de 2019–2022,
obteve RMSE interno 1,838655 contra 1,882056 da climatologia no mesmo recorte. O CSV
candidato preserva os 1.885.464 IDs oficiais e obteve score público 1,81358 no envio
de 20/09/2026.

A nova leitura do WORCAP melhora o veredito do alinhamento atmosférico básico, mas não
promove nenhum artefato da origem. Código GPL, pesos e binários continuam fora do
Climazoide. O baseline registra pontuação pública 1,85077; o candidato independente
XGBoost registra 1,81358. A pontuação privada continua indisponível.
