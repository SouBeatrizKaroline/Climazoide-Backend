# Climazoide API

[![CI](https://github.com/SouBeatrizKaroline/Climazoide-Backend/actions/workflows/ci.yml/badge.svg)](https://github.com/SouBeatrizKaroline/Climazoide-Backend/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-0b7a75.svg)](LICENSE)
[![OpenAPI](https://img.shields.io/badge/contract-OpenAPI-6ba539.svg)](http://localhost:8000/docs)

API de inteligência climática operacional e suporte ao desafio **WORCAP 2026 — Previsão Climática de Precipitação sobre a América do Sul**.

O backend conecta o frontend a dados públicos recentes, preserva o contrato científico da competição e nunca substitui uma falha externa por números inventados.

Projeto aberto sob licença MIT. Consulte [como contribuir](CONTRIBUTING.md), [governança](GOVERNANCE.md), [segurança](SECURITY.md) e [histórico de versões](CHANGELOG.md).

> Migração WORCAP: as oito branches foram auditadas sem alterar a origem. Consulte
> [a auditoria](docs/WORCAP_BRANCH_AUDIT.md) ou `GET /v1/research/branches`.

## Ecossistema do projeto

- **Backend operacional:** este repositório, responsável por integrações, proveniência e API.
- **Frontend público:** [Climazoide-Frontend](https://github.com/SouBeatrizKaroline/Climazoide-Frontend).
- **Pesquisa e experimentos:** [WORCAP-2026](https://github.com/mazeeqe/WORCAP-2026), usado como laboratório científico, histórico de branches e referência para PCA/PLS + LSTM, ConvLSTM, XGBoost, ONI e EDA. Ele não é modificado pelo Climazoide.
- **Dashboard:** [soubeatrizkaroline.github.io/Climazoide-Frontend](https://soubeatrizkaroline.github.io/Climazoide-Frontend/).
- **API publicada:** [climazoide-api.onrender.com](https://climazoide-api.onrender.com/docs).

## Dados utilizados

| Fonte | Uso atual | Natureza |
| --- | --- | --- |
| Open-Meteo | condição atual e previsão de 7 dias | dado meteorológico modelado, sem chave |
| CAMS/Copernicus via Open-Meteo | AQI, partículas, gases e UV | composição atmosférica modelada |
| CPTEC/INPE | comparação meteorológica no Brasil | XML público, disponibilidade variável |
| NOAA CPC | ONI e fase observada do ENSO | contexto climático, não previsão local |
| US Naval Observatory | Sol e Lua | efemérides astronômicas |
| NASA POWER | séries mensais sob consulta | comparação climática complementar |
| Kaggle/WORCAP + ERA5 | treino, teste e submissão científica | dados do desafio, fora da API operacional ao vivo |

Detalhes, links oficiais e cuidados metodológicos estão em [Fontes e APIs](docs/API_SOURCES.md).
Falhas em fontes complementares são isoladas; a fonte meteorológica principal usa tentativas curtas antes de declarar indisponibilidade, sem inventar valores.

## Funcionalidades

- condições atuais e previsão de sete dias em 13 pontos sul-americanos;
- chuva, temperatura, vento, pressão, solo e evapotranspiração;
- qualidade do ar, PM2.5, PM10, ozônio e UV via CAMS/Copernicus;
- consulta ao CPTEC/INPE, com disponibilidade informada no payload;
- análises automáticas de água, agricultura, calor e saúde ambiental;
- consulta mensal à NASA POWER;
- manifesto auditável do PCA/EOF + LSTM, atualmente marcado para retreino;
- catálogo rastreável de PCA, PLS concorrente, PLS defasado e ConvLSTM;
- download verificável do Kaggle e validação do CSV de submissão.

## Arquitetura

```text
React → FastAPI
          ├── Open-Meteo: tempo + chuva + solo + ET₀
          ├── CAMS/Copernicus: composição atmosférica
          ├── CPTEC/INPE: referência nacional
          ├── NASA POWER: séries mensais agroclimáticas
          └── ERA5/WORCAP: treino e avaliação M→M+1
```

Se a fonte meteorológica principal falhar, a API responde `502`. Se CAMS ou CPTEC falharem, os outros dados reais permanecem disponíveis e a fonte afetada aparece como indisponível.

## Executar

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- saúde: `http://localhost:8000/health`

## Rotas

| Método | Rota | Função |
|---|---|---|
| GET | `/health` | saúde da aplicação |
| GET | `/v1/live/locations` | localidades disponíveis |
| GET | `/v1/live/overview?location=brasilia` | agregação recente completa |
| GET | `/v1/integrations/catalog` | fontes, acesso e documentação |
| POST | `/v1/integrations/nasa-power/monthly` | série mensal NASA POWER |
| GET | `/v1/model/manifest` | proveniência e métricas do modelo |

Pontos operacionais: `buenos-aires`, `la-paz`, `brasilia`, `santiago`, `bogota`, `quito`, `georgetown`, `asuncion`, `lima`, `paramaribo`, `montevideu`, `caracas` e `caiena`.

Esses pontos dão contexto recente aos 13 países e territórios continentais. A competição continua sendo atendida pela grade científica completa de **78.561 pontos mensais**; uma capital nunca é tratada como substituta da grade.

## Fontes públicas

| Fonte | Escopo | Uso | Estado |
|---|---|---|---|
| Open-Meteo | internacional | condições atuais, previsão, solo e ET₀ | ativo, sem chave |
| CAMS/Copernicus | internacional | qualidade do ar e UV | ativo, sem chave |
| NOAA CPC | internacional | ONI e fase do ENSO | ativo, sem chave |
| US Naval Observatory | internacional | fase lunar, nascer e pôr do Sol | ativo, sem chave |
| CPTEC/INPE | nacional | previsão brasileira independente | integrado, sujeito à disponibilidade |
| NASA POWER | internacional | séries mensais agroclimáticas | ativo, sem chave |
| Kaggle/WORCAP | competição | treino, teste e submissão | exige conta e aceite |
| ERA5/CDS | internacional | reanálise e reprodução | exige cadastro e termos |
| INMET | nacional | observações de estações | acesso conforme canal oficial |

Detalhes e atribuições: [`docs/API_SOURCES.md`](docs/API_SOURCES.md).

## Dataset oficial do Kaggle

São **13 arquivos**, aproximadamente **2,06 GB**, grade ERA5 de `0,25°`, `301 × 261` e **78.561 pontos por mês**. O treino cobre 1940–2022. O estado atmosférico de `M` alimenta a estimativa de precipitação de `M+1`. A avaliação cobre 2023–2024.

Após autenticar a conta Kaggle e aceitar as regras:

```bash
pip install kagglehub
python scripts/download_competition.py
```

O script executa `kagglehub.competition_download('previsao-climatica-de-precipitacao-sobre-a-america-do-sul')` e confirma os 13 nomes esperados. A tentativa sem autenticação termina de forma explícita; os NetCDF não são versionados.

### Arquivos

- `treino_tp.nc`: precipitação observada em mm/dia;
- `treino_tp_alvo.nc`: precipitação de M+1;
- nove `treino_*.nc`: temperatura, nuvens, pressão, umidades, geopotencial e vento em 850 hPa;
- `teste_features.nc`: meses-alvo, `time_origem`, `tp_ultima_obs` e `lag_meses`;
- `sample_submission.csv`: IDs oficiais em ordem obrigatória.

### Regras invariantes

- não reconstruir o ID;
- manter `id,tp_mm_day` e **1.885.464 linhas**;
- rejeitar NaN, infinito e precipitação negativa;
- avaliar com RMSE global;
- tratar `tp_alvo` do teste como desconhecido;
- respeitar a licença **Subject to Competition Rules**.

```bash
python scripts/validate_submission.py data/sample_submission.csv submission.csv
```

Auditoria conjunta do dataset e da submissão:

```bash
python scripts/audit_readiness.py data --submission submission.csv
```

O parecer completo, com pendências e evidências, está em [`docs/HACKATHON_AUDIT.md`](docs/HACKATHON_AUDIT.md).

## Análise automática e IA responsável

Os cartões de impacto usam um motor determinístico e explicável:

- balanço hídrico = chuva prevista − evapotranspiração de referência;
- demanda evaporativa = soma de ET₀ em sete dias;
- calor = maior temperatura prevista;
- saúde ambiental = AQI atual do CAMS.

Isso é análise automática, não texto inventado por um modelo generativo. Uma IA pública só deve ser adicionada se possuir modelo, licença, versão, dados de entrada e saída documentados, além de não substituir alertas oficiais ou a avaliação científica.

Endpoints citados pela comunidade são testados antes de entrar no produto. Nesta validação, NOAA CPC e USNO responderam; o exemplo `apiclima.inmet.gov.br` não respondeu de forma estável e o WFS TerraBrasilis informado devolveu uma exceção de camada. Por isso, ambos permanecem documentados, mas não são anunciados como ativos.

## Modelo do hackathon

A auditoria identificou que a execução histórica do `pca_lstm_run1` alinhava as variáveis atmosféricas ao mês-alvo. O contrato correto é usar o estado do mês anterior para prever `M+1`. O código científico foi corrigido e agora exige **retreino**.

As métricas anteriores foram removidas do manifesto ativo e da interface. Elas não são pontuação do leaderboard e não devem ser usadas para comparar modelos. Como pesos e objetos PCA não estão versionados, a API também não afirma executar inferência Kaggle em produção.

A branch `vermelho` foi revisada no commit `9492b93`. PLS, checkpoints por época e execução de múltiplas variações foram registrados como propostas de pesquisa, não como resultados. O endpoint `/v1/model/manifest` expõe as fontes revisadas, os quatro candidatos e cada bloqueio de prontidão para o frontend.

O ConvLSTM possui arquitetura funcional desde o commit científico `e07dffb`, com células empilhadas, preservação espacial e saída não negativa. Seu estado é **pronto para treinamento**, não validado: métricas só serão publicadas após o dataset oficial e uma rodada temporal reproduzível.

O commit científico `bcfc011` adiciona execução própria para Kaggle Notebook. Com a competição anexada em `/kaggle/input`, `python kaggle_notebook.py` valida os 13 arquivos, treina, confere 1.885.464 linhas e grava o CSV acompanhado de manifesto SHA-256.

A partir de `cf9ea4b`, a mesma execução pode publicar opcionalmente esses artefatos no Cloud Storage e registrar a proveniência no BigQuery usando a conta Google Cloud vinculada pelo Kaggle Secrets. Nenhuma credencial é armazenada no código ou no manifesto.

## Qualidade, segurança e commits

```bash
ruff check .
pytest
powershell -ExecutionPolicy Bypass -File scripts/install_hooks.ps1
```

- CI em Linux para cada push e pull request em `main`;
- Conventional Commits em português;
- nenhuma credencial no código;
- timeout e falha parcial nas integrações;
- CORS por `ALLOWED_ORIGINS`;
- dados críticos devem ser confirmados em alertas oficiais.

## Publicação HTTPS

O `render.yaml` e o `Dockerfile` deixam a API pronta para implantação como Web Service no Render. Após conectar este repositório à conta:

1. criar um Blueprint a partir de `render.yaml`;
2. confirmar que `/health` retorna `api_version=0.2.0` e `model_contract_version=1.1`;
3. copiar a URL HTTPS criada;
4. cadastrar essa URL como variável `VITE_API_URL` no repositório do frontend;
5. executar novamente o workflow **Deploy Pages**.

O CORS de produção já permite `https://soubeatrizkaroline.github.io`.

## Atribuição

*Contains modified Copernicus Climate Change Service information 2026. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.*
