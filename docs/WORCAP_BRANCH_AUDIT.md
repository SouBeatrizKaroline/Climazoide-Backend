# Auditoria técnica da pesquisa WORCAP-2026

Auditoria atualizada em **20 de setembro de 2026, às 19:24:50 (BRT, UTC−03:00)**.
O repositório de pesquisa foi consultado somente para leitura. A lista remota
confirmada contém oito branches. A nova leitura incluiu `main@228b15c` e
`vermelho@8c7fdb5`, publicados em 20/09/2026. Nenhum push, commit ou alteração foi
feito na origem. As regras temporais fornecidas pela equipe foram tratadas como
requisito da auditoria.

## Resultado

**Precisa de ajustes: a atualização mais recente corrige o principal deslocamento
atmosférico, mas ainda não constitui uma release promovível.** Para prever o mês `T`,
o contrato é usar apenas
informação originada e publicada até o instante de emissão definido no mês `T−1`.
O pipeline sem ONI em `vermelho@8c7fdb5` usa atmosfera em `alvo_idx − 1` e foi
retreinado. A `main@228b15c` também incorporou a correção anterior. Ainda assim,
ONI e o pós-processamento ENSO não passam na auditoria temporal, e a métrica agregada
do LSTM não pondera os 24 horizontes como o conjunto oficial. Por isso, nenhum novo
artefato substitui o baseline ou o candidato independente do Climazoide.

## Achados temporais

| Componente | Evidência | Decisão |
| --- | --- | --- |
| Treino/validação em `vermelho@8c7fdb5` | `src/data.py` seleciona atmosfera em `feature_idx = alvo_idx − 1` e `TP[alvo_idx]` como alvo | **Alinhamento básico conforme:** atmosfera de `T−1` para prever `T` |
| `main@228b15c` | Integra a correção T−1 e resultados anteriores com correção ENSO | Correção básica integrada; saída com ENSO continua não aprovada |
| Features do teste | O contrato informado associa cada alvo `T` a `time_origem = T−1` | Não foi encontrada dependência automática da linha posterior para prever a anterior; faltam assertions de origem no carregador |
| ONI | Índice centrado em três meses é atribuído ao mês central; a nova variante lê o ONI de `T−1` | **Bloqueado:** o valor centrado em `T−1` pode incluir SST observada em `T`; a execução também piorou o RMSE interno |
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

A fórmula do RMSE observada é correta para uma grade completa e pesos iguais. A nova
execução sem ONI registrou RMSE interno `1,840456` e MAE `1,112441`; com ONI,
RMSE `1,865132` e MAE `1,134670`. Esses valores são informativos, mas a agregação
contém quantidades diferentes de exemplos por horizonte (47 para lag 1 até 24 para
lag 24), enquanto o teste oficial tem exatamente uma grade por cada um dos 24 meses.
A comparação não deve ser tratada como score esperado da competição.
A validação é cronológica; o embaralhamento do DataLoader ocorre somente entre
amostras já atribuídas ao treino. Separar e reportar explicitamente horizonte de
um mês (`lag=1`) e executar avaliação walk-forward após corrigir o pipeline.
Também foram observadas métricas divergentes em arquivos de resultado sem hash de
código/execução que permita explicar a diferença.

## Estado das branches

O catálogo completo, commits e resumo de contribuição está em
[`artifacts/research_catalog.json`](../artifacts/research_catalog.json) e na rota
`GET /v1/research/branches`. Pontos que afetam prontidão:

- `vermelho@8c7fdb5` é a atualização remota mais recente: reduz os tetos de
  componentes, executa novo sweep e promove internamente `lr=5e-4`, `hidden_size=128`
  e `dropout=0,1`; isso permanece pesquisa, não produção.
- `main@228b15c` incorporou a correção temporal anterior, mas não a execução mais
  recente de 20/09 e ainda mantém resultado associado à correção ENSO.
- `feature/melhorar-pls-lstm-daiane@54ab930` passou a ser um snapshot histórico;
  seu desalinhamento atmosférico não representa o estado mais recente.
- `feature/xgboost-v3-daiane` não deve ser descrita como validada “sem vazamento”:
  seu construtor de exemplos no snapshot usa atmosfera do mês-alvo.
- O novo script de walk-forward para a correção ENSO está versionado, mas o próprio
  histórico do commit declara que ele ainda não foi executado até a conclusão; não
  há relatório final que autorize a correção.
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

1. Manter a correção já implementada de `atmosfera T−1 → alvo TP T`.
2. Avaliar os 24 horizontes com o mesmo peso e a mesma geometria do teste oficial.
3. Remover ONI centrado ou reconstruí-lo com vintage estritamente disponível no corte.
4. Concluir e revisar o walk-forward antes de considerar pós-processamento ENSO.
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
