# Auditoria de branches WORCAP-2026

Auditoria publicada em **18 de setembro de 2026, às 08:14:54 (BRT, UTC−03:00)**,
somente por leitura do repositório
`mazeeqe/WORCAP-2026`. Nenhum commit, push ou alteração foi realizado na origem.

## Decisão de arquitetura

O WORCAP contém pesquisa GPL-3.0, dependências de treinamento e artefatos binários.
A API operacional permanece pequena e desacoplada: publica um catálogo rastreável de
branches, commits, estado e trabalho concluído, mas não copia pesos, grades `.npz`,
logs ou notebooks. O treino continua no repositório científico; a promoção para a API
exige release validada, artefato reproduzível e contrato de inferência.

## Consolidação

- `main`: base PCA/PLS + LSTM e comparação das variantes.
- `Beatriz`: contrato M→M+1, ConvLSTM, execução Kaggle/GCP, testes e governança.
- `vermelho`: correção de vazamento, cache, sweep e pós-processamento ENSO.
- `feature/eda-outliers-daiane`: EDA, outliers e estatísticas, incorporada à branch mais recente.
- `feature/xgboost-ensemble-daiane`: primeira versão, superada pelo XGBoost v3.
- `feature/xgboost-v3-daiane`: XGBoost sem vazamento, incorporado à branch mais recente.
- `feature/oni-experimento-daiane`: ONI no XGBoost, incorporado à branch mais recente.
- `feature/melhorar-pls-lstm-daiane`: consolidação mais recente, commit `54ab930`.

O arquivo `artifacts/research_catalog.json` é a fonte consumida pela rota
`GET /v1/research/branches` e registra explicitamente que métricas experimentais não
são métricas de produção.
