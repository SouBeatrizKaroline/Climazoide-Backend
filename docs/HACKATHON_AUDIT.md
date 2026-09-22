# Protocolo de conformidade científica

Atualizado em 22/09/2026. Este documento consolida a regra temporal comunicada pela
organização, a auditoria da pesquisa original e as salvaguardas implementadas no
Climazoide. O relatório detalhado das branches permanece em
[`WORCAP_BRANCH_AUDIT.md`](WORCAP_BRANCH_AUDIT.md).

## 1. Regra que define uma previsão válida

Para prever um mês `T`, só pode entrar informação que estaria disponível até o fim de
`T−1`. A localização física de uma variável no arquivo não altera sua data real.

Exemplo oficial: para fevereiro de 2023, janeiro de 2023 pode ser usado; fevereiro de
2023 e qualquer mês posterior não podem. Os campos de janeiro presentes na linha de
fevereiro não podem ser deslocados para estimar janeiro. Isso seria diagnóstico do
próprio mês, não previsão.

## 2. Dados públicos e alvo proibido

Dados externos públicos são permitidos, inclusive outras reanálises, observações,
índices e previsões, desde que a versão usada estivesse disponível no instante
histórico da previsão. A disponibilidade atual na internet não torna o dado
retroativamente permitido.

A precipitação ERA5 observada de 2023–2024 é o alvo da avaliação. Embora hoje seja
pública, ela não pode ser baixada, consultada, derivada ou incorporada ao pipeline. O
Climazoide não lê esse alvo e trata `tp_alvo` do teste como obrigatoriamente `NaN`.

## 3. Público, privado e overfitting

O recorte público de 2023 fornece feedback e o recorte privado de 2024 define a
classificação final. Essa separação mitiga, mas não elimina, overfitting ao leaderboard.

Escolher arquitetura ou hiperparâmetros após observar scores é um risco metodológico,
mas não prova, por si só, contaminação. A auditoria distingue:

- **violação objetiva:** consulta ao alvo, variável de `T` ou posterior, valor real
  fixado, artefato derivado do período avaliado ou transformação ajustada com futuro;
- **risco de generalização:** muitas tentativas orientadas pelo score público, sem
  evidência direta de acesso ao alvo.

Por isso, o candidato é promovido primeiro por validação temporal independente. A
pontuação pública é registrada separadamente e nunca substitui essa validação.

## 4. Estado da pesquisa auditada

A atualização remota de 22/09/2026 foi novamente examinada somente para leitura. A
pesquisa agora inclui CV walk-forward em cinco cortes históricos, modelos de anomalia
e encolhimento em direção à climatologia. O melhor blend sem ONI presente no relatório
registra RMSE-CV LOFO `1,780512`, mas não foi promovido porque não há CSV final
versionado nem score oficial. O blend apontado como final inclui ONI trimestral centrado
em `T−1`, que pode incorporar SST de `T`; por isso continua bloqueado mesmo apresentando
RMSE-CV LOFO `1,778058`.

Não foi encontrada evidência versionada de consulta direta ao alvo. Os novos resultados
mantêm o diagnóstico em **precisa de ajustes**, sem autorizar pesos, ONI centrado ou
submissões da origem. A branch consolidada também adicionou bagging ao XGBoost e um
pipeline ConvLSTM temporalmente alinhado; ambos permanecem pesquisa sem artefato final
independente auditado.

O código GPL da origem não foi copiado para os repositórios MIT do Climazoide.

## 5. Pipelines aprovados no Climazoide

### Baseline `monthly-climatology-v1`

- entrada: somente precipitação histórica oficial de 1940–2022;
- validação: ajuste até 2018-12 e avaliação em 2019–2022;
- RMSE interno: `1,882056` em 3.770.928 observações;
- saída: 1.885.464 IDs oficiais, na ordem original;
- pontuação pública registrada: `1,85077`.

### Candidato `xgboost-anomaly-v1`

- entrada: nove variáveis atmosféricas oficiais da linha de `T`, que representam
  `time_origem = T−1`; precipitação congelada na origem; climatologia, posição,
  sazonalidade e horizonte;
- alvo de treino: anomalia de precipitação de `T`, somente no período histórico;
- validação: treino até 2018-12 e avaliação em dois blocos de 24 meses de 2019–2022;
- RMSE interno: `1,838655`, contra `1,882056` da climatologia no mesmo recorte;
- alvo 2023–2024: não lido;
- dados externos: nenhum;
- estado: candidato validado e enviado; score público `1,81358`, melhor que `1,85077`
  do baseline. O score privado continua indisponível.

## 6. Separação das camadas do produto

| Camada | Fontes | Entra no CSV mensal? | Finalidade |
| --- | --- | --- | --- |
| previsão mensal | 13 arquivos oficiais ERA5/distribuídos | sim | gerar `id,tp_mm_day` |
| contexto recente | Open-Meteo e MET Norway | não | condição atual e sete dias |
| ambiente | CAMS/Copernicus | não | ar e UV |
| contexto nacional | CPTEC/INPE | não | comparação meteorológica |
| contexto climático | NOAA CPC e NASA POWER | não | ENSO e séries complementares |
| efemérides | US Naval Observatory | não | Sol e Lua |
| apoio à decisão | saída mensal já gerada + climatologia histórica | não altera o CSV | interpretação setorial |

As fontes adicionais tornam o produto mais útil, mas não treinam, calibram, corrigem
nem preenchem a submissão. A API publica essa separação em
`GET /v1/integrations/catalog` e `GET /v1/model/manifest`.

## 7. Salvaguardas automatizadas

- `time_origem + 1 mês = time` para todas as linhas de teste;
- atmosfera de treino sempre em `T−1`;
- mutar linhas futuras do teste não altera a entrada de um alvo anterior;
- climatologias e transformações respeitam o corte do fold;
- `tp_alvo` do teste deve permanecer inteiramente ausente;
- IDs são copiados de `sample_submission.csv`, sem reconstrução;
- ordem, quantidade, finitude, não negatividade e hashes são verificados;
- fontes operacionais têm `enters_monthly_submission=false`;
- CI executa testes da API e do pipeline científico.

## 8. Veredito atual

O baseline e o novo candidato representam previsão legítima sob o contrato implementado:
dados disponíveis até `T−1` produzem a estimativa de `T`. O candidato superou o baseline
na validação temporal interna, mas só deve substituir o envio principal após avaliação
oficial identificável. A pesquisa histórica reprovada continua documentada sem ser
apresentada como solução aprovada.
