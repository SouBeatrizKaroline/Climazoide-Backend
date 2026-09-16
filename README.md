# Climazoide API

API de inteligência climática operacional e suporte ao desafio **WORCAP 2026 — Previsão Climática de Precipitação sobre a América do Sul**.

O backend conecta o frontend a dados públicos recentes, preserva o contrato científico da competição e nunca substitui uma falha externa por números inventados.

## Funcionalidades

- condições atuais e previsão de sete dias em cinco capitais brasileiras;
- chuva, temperatura, vento, pressão, solo e evapotranspiração;
- qualidade do ar, PM2.5, PM10, ozônio e UV via CAMS/Copernicus;
- consulta ao CPTEC/INPE, com disponibilidade informada no payload;
- análises automáticas de água, agricultura, calor e saúde ambiental;
- consulta mensal à NASA POWER;
- manifesto auditável do PCA/EOF + LSTM;
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
| GET | `/v1/live/overview?location=recife` | agregação recente completa |
| GET | `/v1/integrations/catalog` | fontes, acesso e documentação |
| POST | `/v1/integrations/nasa-power/monthly` | série mensal NASA POWER |
| GET | `/v1/model/manifest` | proveniência e métricas do modelo |

Localidades: `recife`, `sao-paulo`, `manaus`, `brasilia`, `porto-alegre`.

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

## Análise automática e IA responsável

Os cartões de impacto usam um motor determinístico e explicável:

- balanço hídrico = chuva prevista − evapotranspiração de referência;
- demanda evaporativa = soma de ET₀ em sete dias;
- calor = maior temperatura prevista;
- saúde ambiental = AQI atual do CAMS.

Isso é análise automática, não texto inventado por um modelo generativo. Uma IA pública só deve ser adicionada se possuir modelo, licença, versão, dados de entrada e saída documentados, além de não substituir alertas oficiais ou a avaliação científica.

Endpoints citados pela comunidade são testados antes de entrar no produto. Nesta validação, NOAA CPC e USNO responderam; o exemplo `apiclima.inmet.gov.br` não respondeu de forma estável e o WFS TerraBrasilis informado devolveu uma exceção de camada. Por isso, ambos permanecem documentados, mas não são anunciados como ativos.

## Modelo do hackathon

Validação temporal interna do `pca_lstm_run1`:

| Método | RMSE | MAE |
|---|---:|---:|
| PCA/EOF + LSTM | 1,564 | 0,949 |
| Climatologia | 1,891 | 1,137 |
| Persistência | 4,004 | 2,372 |

Skill contra climatologia: **17,29%**. Não é pontuação do leaderboard. Como pesos e objetos PCA não estão versionados, a API não afirma executar inferência Kaggle em produção.

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

## Atribuição

*Contains modified Copernicus Climate Change Service information 2026. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.*
