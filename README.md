# Climazoide API

[![CI](https://github.com/SouBeatrizKaroline/Climazoide-Backend/actions/workflows/ci.yml/badge.svg)](https://github.com/SouBeatrizKaroline/Climazoide-Backend/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-0b7a75.svg)](LICENSE)
[![OpenAPI](https://img.shields.io/badge/API-OpenAPI-6ba539.svg)](https://climazoide-api.onrender.com/docs)

Backend aberto de previsão mensal de precipitação e inteligência climática para a
América do Sul. A solução mantém o arquivo científico de previsão separado das camadas
recentes de contexto e apoio à decisão.

- **API:** https://climazoide-api.onrender.com/docs
- **Site:** https://soubeatrizkaroline.github.io/Climazoide-Frontend/
- **Frontend:** https://github.com/SouBeatrizKaroline/Climazoide-Frontend
- **Pesquisa auditada, somente leitura:** https://github.com/mazeeqe/WORCAP-2026

## Equipe

Beatriz Karoline • Daiane Fonseca • Tomáz Giansante

## Visão geral

O núcleo científico estima a precipitação média do mês `T` a partir de informação que
estaria disponível até o fim de `T−1`. O produto também apresenta tempo recente,
qualidade do ar, contexto climático e leituras setoriais, mas essas fontes adicionais
não treinam, calibram nem alteram o CSV mensal.

```text
13 arquivos oficiais ──► pipeline M→M+1 ──► id,tp_mm_day
                                 │
                                 ├── baseline enviado
                                 └── candidato XGBoost validado

APIs públicas recentes ──► contexto operacional e apoio à decisão
                            (fora do modelo e do CSV)
```

## Regra temporal e integridade

Para prever `T`, só vale informação disponível até `T−1`. Isso independe de onde o
dado aparece fisicamente.

- A linha de fevereiro de 2023 pode usar atmosfera de janeiro de 2023.
- Essa atmosfera não pode ser deslocada para estimar janeiro de 2023.
- Nenhuma linha posterior do teste pode influenciar uma previsão anterior.
- A precipitação ERA5 observada de 2023–2024 é alvo proibido, mesmo sendo pública.
- `tp_alvo` deve permanecer integralmente `NaN` durante a inferência.
- Estatísticas, normalizações e transformações são ajustadas dentro do corte temporal.

Dados externos públicos são permitidos em tese quando sua versão estava disponível no
instante histórico. A versão atual do modelo não usa dados externos na submissão.

O leaderboard público de 2023 e o privado de 2024 ajudam a reduzir overfitting, mas não
o eliminam. Escolha de hiperparâmetros por score é tratada como risco de generalização;
consulta ao alvo, uso de futuro ou valores derivados da avaliação são violações
objetivas. Consulte o [protocolo científico](docs/HACKATHON_AUDIT.md).

## Dados e papéis

| Camada | Fonte | Uso | Entra no CSV? |
| --- | --- | --- | --- |
| previsão mensal | arquivos oficiais ERA5/distribuídos | treino, teste e IDs | **sim** |
| tempo recente | Open-Meteo e MET Norway | condição e sete dias | não |
| atmosfera e saúde | CAMS/Copernicus | qualidade do ar e UV | não |
| referência nacional | CPTEC/INPE | comparação meteorológica | não |
| contexto climático | NOAA CPC e NASA POWER | ENSO e séries complementares | não |
| efemérides | US Naval Observatory | Sol e Lua | não |
| pesquisa futura | ERA5/CDS, INMET, PClima e Embrapa | fontes documentadas | não |

Essa classificação também é publicada por `GET /v1/integrations/catalog` nos campos
`use_scope` e `enters_monthly_submission`. Links, acesso e limitações estão em
[`docs/API_SOURCES.md`](docs/API_SOURCES.md).

## Dataset científico

- período de treino: `1940-01` a `2022-12`;
- avaliação: 24 meses de `2023-01` a `2024-12`;
- grade: `301 × 261`, resolução `0,25°`;
- domínio: `60°S–15°N`, `90°O–25°O`;
- pontos por mês: `78.561`;
- linhas da submissão: `1.885.464`;
- alvo: precipitação média mensal em `mm/dia`;
- métrica: RMSE global, menor é melhor.

Os IDs são copiados de `sample_submission.csv`, sem reconstrução. As entradas oficiais
são precipitação histórica e nove variáveis atmosféricas: temperatura a 2 m, cobertura
de nuvens, pressão superficial, umidades específica e relativa, temperatura e
geopotencial em 850 hPa, além dos ventos `u` e `v` em 850 hPa.

## Modelos publicados

| Modelo | Estado | Validação 2019–2022 | Pontuação pública |
| --- | --- | ---: | ---: |
| `monthly-climatology-v1` | baseline enviado | 1,882056 | 1,85077 |
| `xgboost-anomaly-v1` | melhor envio auditado | **1,838655** | **1,81358** |
| blend PLS defasado + LSTM (pesquisa) | CV walk-forward sem ONI | 1,780512* | pendente |

\* RMSE-CV LOFO em cinco cortes históricos, extraído do relatório da origem auditada em
22/09/2026. Não é score oficial e não foi promovido porque não há CSV final versionado.
O blend apontado como final na origem inclui ONI trimestral centrado em `T−1`, que pode
incorporar o mês `T`, e por isso permanece bloqueado.

### Baseline

Calcula a climatologia espacial de cada mês usando somente 1940–2022. Para validação,
é ajustado até 2018-12 e avaliado em 3.770.928 observações de 2019–2022.

### XGBoost de anomalias

Prevê o desvio em relação à climatologia usando:

- nove variáveis atmosféricas oficiais em `T−1`;
- precipitação congelada na origem e sua anomalia;
- climatologia do alvo, latitude, longitude, mês e horizonte.

O treino termina em 2018-12. A avaliação usa dois blocos operacionais de 24 meses,
totalizando 3.770.928 previsões. Nenhum alvo de 2023–2024 ou dado externo é lido.
O código foi implementado independentemente neste repositório MIT; código GPL da origem
auditada não foi copiado.

## Arquivos para download

| Arquivo | Rota | Estado |
| --- | --- | --- |
| baseline completo | `/v1/submission/download` | enviado e pontuado |
| XGBoost completo | `/v1/submission/candidate/download` | validado e enviado; score 1,81358 |
| parcial | `/v1/submission/partial.csv` | somente se faltarem previsões válidas |
| exemplo | `/v1/submission/example.csv` | três linhas; não enviável |

Baseline e candidato têm exatamente `id,tp_mm_day`, 1.885.464 linhas, valores finitos
e não negativos, IDs e ordem oficiais. Hashes ficam nos relatórios de `artifacts/`.
O XGBoost permanece separado do baseline para preservar a rastreabilidade, mas passou
a ser o melhor envio auditado do Climazoide após superar o score público do baseline.

## Reprodução científica

Obtenha os 13 arquivos pelo canal oficial e coloque-os em `data/`. Os dados brutos não
são redistribuídos por este repositório.

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -e ".[science,dev]"

python scripts/audit_readiness.py data
python scripts/train_monthly_climatology.py data
python scripts/train_xgboost_anomaly.py data --samples 500000 --estimators 500
python scripts/validate_submission.py \
  data/sample_submission.csv artifacts/submission-xgboost-anomaly-v1.csv
```

O relatório do candidato registra período, seed, features, entradas, métricas e hashes.
Os testes asseguram o índice `T−1`, o isolamento entre linhas do teste e o corte da
climatologia.

## Produto operacional

As integrações recentes alimentam 13 pontos representativos da América do Sul. Quando
Open-Meteo falha, MET Norway atua como contingência e informa período válido e origem.
Campos ausentes permanecem `null`; nunca são convertidos em zero ou simulados.

Uma ET₀ aproximada pode ser calculada por Hargreaves-Samani quando a fonte não a
fornece. Ela é explicitamente rotulada como estimativa e não entra no modelo mensal.
O mesmo isolamento vale para chuva de sete dias, qualidade do ar, ONI, Sol e Lua.

### Apoio à decisão

`Climazoide Decisão` cruza a saída mensal já gerada com climatologia histórica nos
pontos representativos para agricultura, logística, áreas de risco, hidroenergia,
turismo e gestão da água. Essa camada interpreta o resultado; não acrescenta colunas,
retreina o modelo ou altera o CSV. Recomendações são pontos de monitoramento, não alerta
oficial, ordem de evacuação, prescrição agronômica ou garantia operacional.

## API

| Método | Rota | Finalidade |
| --- | --- | --- |
| GET | `/health` | versão e saúde |
| GET | `/v1/live/locations` | localidades operacionais |
| GET | `/v1/live/overview` | contexto recente e proveniência |
| GET | `/v1/integrations/catalog` | fontes e papel científico |
| POST | `/v1/integrations/nasa-power/monthly` | série mensal complementar |
| GET | `/v1/model/manifest` | contrato, métricas e política de dados |
| GET | `/v1/submission/status` | disponibilidade e bloqueios |
| GET | `/v1/submission/download` | baseline completo |
| GET | `/v1/submission/candidate/download` | candidato completo |
| GET | `/v1/decision-support/options` | setores, locais e meses |
| GET | `/v1/decision-support/scenario` | leitura setorial explicável |

## Executar a API

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

- API local: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- saúde: http://localhost:8000/health

## Qualidade e publicação

```bash
ruff check .
pytest
```

- CI executa dependências operacionais e científicas em cada push;
- artefatos são conferidos por tamanho e SHA-256;
- nenhuma credencial fica no código;
- CORS é controlado por `ALLOWED_ORIGINS`;
- `Dockerfile` e `render.yaml` publicam a API no Render;
- `/health` deve retornar `api_version=0.6.4` e `model_contract_version=1.5`.

Consulte também [governança](GOVERNANCE.md), [segurança](SECURITY.md),
[contribuição](CONTRIBUTING.md), [changelog](CHANGELOG.md) e
[auditoria das branches](docs/WORCAP_BRANCH_AUDIT.md).

## Atribuição

*Contains modified Copernicus Climate Change Service information 2026. Neither the
European Commission nor ECMWF is responsible for any use that may be made of the
Copernicus information or data it contains.*
