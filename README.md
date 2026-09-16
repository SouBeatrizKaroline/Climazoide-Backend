# Climazoide API

Backend leve para servir o dashboard do Climazoide e receber integrações climáticas nacionais e internacionais sem acoplar a interface ao pipeline científico.

> Estado atual: MVP. A rota do dashboard devolve valores demonstrativos explicitamente marcados. O endpoint NASA POWER é o primeiro conector funcional. O modelo PCA/EOF + LSTM existe no repositório científico; o ConvLSTM ainda está em desenvolvimento.

## Responsabilidades

- entregar um contrato estável ao frontend;
- catalogar fontes obrigatórias e extras;
- isolar conectores externos;
- impedir que uma falha externa derrube o painel;
- carregar, futuramente, artefatos versionados de inferência e métricas.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Saúde: `GET /health`

## Rotas

| Método | Rota | Função |
|---|---|---|
| GET | `/health` | disponibilidade da aplicação |
| GET | `/v1/dashboard/options` | meses e regiões disponíveis |
| GET | `/v1/dashboard/summary?target_month=2024-12&region=america-do-sul` | painel filtrado |
| GET | `/v1/integrations/catalog` | fontes, exigência, acesso e documentação |
| POST | `/v1/integrations/nasa-power/monthly` | consulta mensal pontual à NASA POWER |
| GET | `/v1/model/manifest` | versão, proveniência, métricas e limitações do modelo |

Exemplo NASA POWER:

```json
{
  "latitude": -8.05,
  "longitude": -34.9,
  "start": 2023,
  "end": 2024,
  "parameters": ["PRECTOTCORR", "T2M"]
}
```

## Exigido × extra

- **Exigido:** arquivos oficiais da competição via Kaggle, submissão no contrato fornecido, RMSE, reprodutibilidade, código e documentação públicos.
- **Extra:** INMET, INPE/CPTEC, ECMWF CDS, NASA POWER e NOAA ONI. Extras só entram no modelo após validação temporal e documentação da transformação.

O guia completo, com canais oficiais e cuidados, está em [docs/API_SOURCES.md](docs/API_SOURCES.md).

## Validar uma submissão

O validador percorre os dois CSVs em streaming, preserva a ordem original dos IDs e rejeita NaN, infinito, negativos, linhas extras ou ausentes:

```bash
python scripts/validate_submission.py caminho/sample_submission.csv caminho/submission.csv
```

## Métricas disponíveis

O manifesto registra resultados reais da validação temporal interna do artefato `pca_lstm_run1`: RMSE `1,564` do modelo, `1,891` da climatologia e `4,004` da persistência. Isso equivale a um Skill Score de aproximadamente `17,29%` contra climatologia. Esses números não são pontuação pública ou privada do Kaggle.

## Estrutura

```text
app/
├── main.py              rotas e configuração HTTP
├── config.py            ambiente e CORS
├── models.py            contratos Pydantic
└── services/            catálogo, dashboard e conectores
tests/                   testes sem dependência de rede
docs/API_SOURCES.md      fontes obrigatórias e extras
```

## Qualidade e commits

```bash
ruff check .
pytest
powershell -ExecutionPolicy Bypass -File scripts/install_hooks.ps1
```

Os commits seguem Conventional Commits em português. Consulte [CONTRIBUTING.md](CONTRIBUTING.md). A CI roda na branch `main`.

## Próximos passos objetivos

1. Publicar do pipeline científico um `manifest.json` com versão, modelo, período, RMSE e caminhos dos artefatos.
2. Trocar o fallback de demonstração por leitura do manifesto e previsões reais.
3. Implementar cache e rate limit nos conectores.
4. Acrescentar autenticação somente se surgirem rotas privadas ou custos de API.

## Contrato do desafio preservado

O resumo informa explicitamente origem M, alvo M+1, grade de 301 × 261 pontos, 78.561 previsões por mês, 1.885.464 linhas na submissão completa e RMSE global em mm/dia. Esses metadados são verificáveis; a previsão do MVP continua marcada como `demo` até o pipeline científico publicar um artefato versionado.

## Licença e dados

A licença do código deve ser confirmada com a equipe. Dados externos mantêm seus próprios termos; não redistribua ERA5/Kaggle ou artefatos derivados sem revisar as regras aplicáveis.
