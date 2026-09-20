# Climazoide API

[![CI](https://github.com/SouBeatrizKaroline/Climazoide-Backend/actions/workflows/ci.yml/badge.svg)](https://github.com/SouBeatrizKaroline/Climazoide-Backend/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-0b7a75.svg)](LICENSE)
[![OpenAPI](https://img.shields.io/badge/contract-OpenAPI-6ba539.svg)](http://localhost:8000/docs)

API de inteligência climática operacional e suporte ao desafio **WORCAP 2026 — Previsão Climática de Precipitação sobre a América do Sul**.

O backend conecta o frontend a dados públicos recentes, preserva o contrato científico da competição e nunca substitui uma falha externa por números inventados.

Projeto aberto sob licença MIT. Consulte [como contribuir](CONTRIBUTING.md), [governança](GOVERNANCE.md), [segurança](SECURITY.md) e [histórico de versões](CHANGELOG.md).

## Equipe

Beatriz Karoline • Daiane Fonseca • Tomáz Giansante

> A pesquisa foi auditada sem alterar sua origem. Consulte
> [o diagnóstico técnico](docs/WORCAP_BRANCH_AUDIT.md) ou `GET /v1/research/branches`.

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
| MET Norway | contingência gratuita para tempo e previsão curta | ativada somente se Open-Meteo falhar |
| CAMS/Copernicus via Open-Meteo | AQI, partículas, gases e UV | composição atmosférica modelada |
| CPTEC/INPE | comparação meteorológica no Brasil | XML público, disponibilidade variável |
| NOAA CPC | ONI e fase observada do ENSO | contexto climático, não previsão local |
| US Naval Observatory | Sol e Lua | efemérides astronômicas |
| NASA POWER | séries mensais sob consulta | comparação climática complementar |
| Kaggle/WORCAP + ERA5 | treino, teste e submissão científica | dados do desafio, fora da API operacional ao vivo |

Detalhes, links oficiais e cuidados metodológicos estão em [Fontes e APIs](docs/API_SOURCES.md).
Falhas são isoladas por fonte. A fonte meteorológica principal usa tentativas curtas; se
falhar, o backend tenta MET Norway e informa a fonte e o período válido. Campos ausentes
na contingência permanecem `null`; ausência nunca é convertida em zero ou dado simulado.

## Funcionalidades

- condições atuais e previsão de sete dias em 13 pontos sul-americanos;
- chuva, temperatura, vento, pressão, solo e evapotranspiração;
- qualidade do ar, PM2.5, PM10, ozônio e UV via CAMS/Copernicus;
- consulta ao CPTEC/INPE, com disponibilidade informada no payload;
- análises automáticas de água, agricultura, calor e saúde ambiental;
- leitura cruzada da previsão curta: chuva acumulada, concentração, dias quentes e correlação chuva–temperatura;
- consulta mensal à NASA POWER;
- baseline completo de climatologia mensal, auditado e validado temporalmente;
- catálogo rastreável de PCA, PLS concorrente, PLS defasado e ConvLSTM;
- download verificável do Kaggle e validação do CSV de submissão.

## Arquitetura

```text
React → FastAPI
          ├── Open-Meteo: tempo + chuva + solo + ET₀
          ├── MET Norway: contingência meteorológica gratuita
          ├── CAMS/Copernicus: composição atmosférica
          ├── CPTEC/INPE: referência nacional
          ├── NASA POWER: séries mensais agroclimáticas
          └── ERA5/WORCAP: treino e avaliação M→M+1
```

Se Open-Meteo falhar, a API tenta MET Norway como contingência; se ambas falharem, os dados meteorológicos ficam indisponíveis sem bloquear as demais fontes. CAMS e CPTEC também são isolados e identificados individualmente.

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
| GET | `/v1/submission/status` | prontidão e bloqueios do CSV Kaggle |
| GET | `/v1/submission/example.csv` | exemplo pequeno, explicitamente não enviável |
| GET | `/v1/submission/partial.csv` | previsões válidas já disponíveis para IDs oficiais, se houver |
| GET | `/v1/submission/download` | CSV completo somente quando validado e publicado |

Pontos operacionais: `buenos-aires`, `la-paz`, `brasilia`, `santiago`, `bogota`, `quito`, `georgetown`, `asuncion`, `lima`, `paramaribo`, `montevideu`, `caracas` e `caiena`.

Esses pontos dão contexto recente aos 13 países e territórios continentais. A competição continua sendo atendida pela grade científica completa de **78.561 pontos mensais**; uma capital nunca é tratada como substituta da grade.

### Leituras derivadas do contexto recente

`GET /v1/live/overview` também retorna `short_range_analysis`, calculado somente
com os dias efetivamente recebidos da fonte meteorológica identificada no mesmo
payload. A seção informa início e fim da janela, número de dias e:

- chuva acumulada, apenas quando todos os dias possuem precipitação;
- dias com chuva prevista ≥ 0,1 mm;
- dias com temperatura máxima ≥ 32 °C;
- parcela da chuva concentrada no dia mais úmido;
- correlação de Pearson entre chuva diária e temperatura máxima.

A correlação é ocultada quando há menos de três pares ou ausência de variação. Ela
descreve somente a pequena janela de sete dias, não demonstra causalidade e não é
usada no CSV mensal nem no treinamento do baseline.

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

São **13 arquivos**, aproximadamente **2,06 GB**, grade ERA5 regular de `0,25°`, `301 × 261` e **78.561 pontos por mês**, entre `60°S–15°N` e `90°O–25°O`. O treino cobre janeiro de 1940 a dezembro de 2022. A avaliação contém 24 meses, de janeiro de 2023 a dezembro de 2024: 2023 compõe o leaderboard público e 2024 define a classificação final.

> **Resolução da grade:** a especificação formal e as dimensões/coordenadas dos arquivos NetCDF indicam `0,25°`. Uma legenda resumida de visualização que mencione `0,5°` é inconsistente com essa grade e não deve ser usada para reconstruir a malha. Sempre valide as coordenadas e a ordem diretamente nos arquivos oficiais.

### Regra temporal obrigatória

A previsão só pode usar informação que já existia no momento da emissão. Portanto, para
prever setembro, a entrada mais recente permitida é agosto. Variáveis atmosféricas de
setembro não podem entrar no modelo que prevê setembro, pois isso caracteriza vazamento
temporal. O pipeline científico deve preservar `time_origem = M` e `time_alvo = M+1` em
treino, validação, teste e geração do CSV de submissão.

O encadeamento é mensal e móvel: janeiro → previsão de fevereiro; fevereiro → previsão
de março; e assim por diante. Para uma previsão de setembro de 2026, usa-se agosto de
2026 completo; setembro só poderá servir de origem para prever outubro depois que seus
dados mensais estiverem completos e disponíveis. Um modelo pode usar meses anteriores
adicionais se sua arquitetura os exigir, mas nunca dados posteriores à origem `M`.

**Estado auditado:** a branch científica consolidada mais recente foi encontrada usando
campos atmosféricos do próprio mês-alvo no treino/validação e permanece somente como
pesquisa. Para não promover esse resultado, o backend implementa de forma independente
um baseline de climatologia mensal que usa apenas 1940–2022. Esse baseline cumpre o
contrato temporal, gera todos os IDs oficiais e não copia código ou artefatos do WORCAP.
A auditoria da origem e o estado detalhado estão em
[`docs/WORCAP_BRANCH_AUDIT.md`](docs/WORCAP_BRANCH_AUDIT.md) e
`GET /v1/model/manifest`.

Esse princípio vale sempre que o produto gerar uma previsão mensal atual. Não muda,
porém, o arquivo de avaliação oficial: ele pede somente os alvos de janeiro de 2023 a
dezembro de 2024, com os IDs já fornecidos. Previsões para 2025 ou 2026 são uma execução
operacional separada. Os 13 arquivos distribuídos não contêm entradas de 2026; será
necessário obter os campos ERA5 mensais correspondentes na mesma grade e validar uma
execução atualizada antes de afirmar que há previsão contínua em produção.

O ERA5 preliminar (ERA5T) costuma ter atraso de cerca de cinco dias; os campos mensais
normalmente ficam disponíveis por volta do dia 6 do mês seguinte e podem ser substituídos
pela versão final cerca de 2–3 meses depois. A origem e a versão usadas devem acompanhar
cada previsão ([disponibilidade oficial do ERA5](https://confluence.ecmwf.int/pages/viewpage.action?pageId=669811810)).

Previsões diárias ou semanais são produtos diferentes: exigem outros alvos e validação.
A regra mensal não transforma automaticamente o modelo M→M+1 em previsão diária ou
semanal.

Após autenticar a conta Kaggle e aceitar as regras:

```bash
pip install kagglehub
python scripts/download_competition.py
```

O script executa `kagglehub.competition_download('previsao-climatica-de-precipitacao-sobre-a-america-do-sul')` e confirma os 13 nomes esperados. A tentativa sem autenticação termina de forma explícita; os NetCDF não são versionados.

### Arquivos e alinhamento temporal

- `treino_tp.nc`: precipitação mensal observada em mm/dia, com dimensão `(time, lat, lon)`;
- `treino_tp_alvo.nc`: `tp_alvo` já deslocado para a precipitação do mês seguinte; o último alvo é `NaN` porque aponta para fora do período de treino;
- nove `treino_*.nc`: estado atmosférico do mês de observação — temperatura a 2 m, cobertura de nuvens, pressão à superfície, umidade específica, umidade relativa, temperatura em 850 hPa, geopotencial em 850 hPa e componentes zonal/meridional do vento em 850 hPa;
- `teste_features.nc`: `time` indica o mês-alvo; as variáveis atmosféricas dessa posição correspondem ao mês anterior, indicado em `time_origem`. Inclui `tp_alvo` inteiramente `NaN`, `tp_ultima_obs` (dezembro de 2022) e `lag_meses` de 1 a 24;
- `sample_submission.csv`: lista completa dos IDs para os 24 meses, na ordem exigida. Os zeros em `tp_mm_day` são apenas preenchimento do modelo de submissão, não previsões nem valores observados.

O alinhamento exigido é variáveis atmosféricas do mês `M` → precipitação de `M+1`. Na avaliação, use as variáveis já defasadas em `teste_features.nc`; não desloque `time` uma segunda vez. A latitude está em ordem crescente. A chuva observada dos 24 meses de teste não é distribuída. O baseline publicado não lê `tp_alvo` do teste e confirma automaticamente que ele permanece inteiramente `NaN`.

O manifesto `GET /v1/model/manifest` publica o contrato completo do dataset, incluindo
as nove variáveis, seus níveis, períodos, grade, alvo, unidade e referência temporal.
Isso permite ao frontend explicar a metodologia sem confundir essas variáveis com as
fontes operacionais de sete dias.

### Regras invariantes

- não reconstruir o ID;
- manter `id,tp_mm_day`, os IDs do `sample_submission.csv` sem reconstrução e sua ordem exata: **1.885.464 previsões** (24 × 78.561);
- rejeitar NaN, infinito e precipitação negativa;
- avaliar com RMSE global;
- tratar `tp_alvo` do teste como desconhecido;
- não usar os zeros do arquivo de exemplo como previsões;
- respeitar a licença **Subject to Competition Rules**.

```bash
python scripts/validate_submission.py data/sample_submission.csv submission.csv
```

O produto nunca transforma o exemplo de três linhas em submissão. O download completo
responde com o baseline validado: 1.885.464 previsões finitas e não negativas, IDs e
ordem oficiais preservados. O arquivo compactado é conferido no Render pelo SHA-256
registrado no manifesto e entregue ao navegador como `submission.csv`.

### Reproduzir o baseline completo

Depois de obter os 13 arquivos oficiais pelo canal da competição:

```bash
pip install -e ".[science,dev]"
python scripts/audit_readiness.py data
python scripts/train_monthly_climatology.py data
python scripts/validate_submission.py data/sample_submission.csv artifacts/submission.csv
```

O treino final calcula, para cada célula e mês do ano, a média histórica de 1940–2022.
A validação é separada: ajusta em 1940–2018 e calcula o RMSE global em 2019–2022. O
resultado reproduzido em 19/09/2026 foi **1,882056 mm/dia** em 3.770.928 observações.
Essa é uma métrica interna de holdout, não uma pontuação do leaderboard. O relatório
com período, hashes e tamanhos fica em `artifacts/submission_report.json`.

### Três níveis de download

- **Completo:** contém as 1.885.464 previsões do baseline validado para janeiro de 2023
  a dezembro de 2024 e está disponível em `/v1/submission/download`;
- **Parcial oficial:** é gerado com as previsões válidas que já existirem para IDs do
  `sample_submission.csv`, mantendo sua ordem. IDs sem previsão válida são omitidos,
  nunca preenchidos com zero ou com valores de outro período. Não pode ser enviado como
  submissão completa;
- **Exemplo de formato:** contém apenas três linhas fictícias para visualizar
  `id,tp_mm_day` e também não pode ser enviado.

O antigo recorte experimental de 2019 não é servido como CSV parcial oficial. Como o
baseline possui todos os IDs oficiais, o parcial permanece desnecessário e indisponível.
O comando abaixo monta um parcial somente quando um futuro modelo tiver previsões válidas
para parte dos IDs, a partir de um CSV de previsões candidatas
produzido pelo modelo, filtrando previsões ausentes, NaN, infinitas ou negativas e
rejeitando IDs desconhecidos ou fora de ordem:

```bash
python scripts/build_partial_submission.py \
  data/sample_submission.csv data/model_predictions.csv
```

O script `scripts/build_research_partial.py` serve apenas para reproduzir uma análise
histórica interna. Seu resultado não é publicado como parcial oficial nem é elegível
para envio.

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

## Estado da validação científica

O artefato publicado é o **baseline `monthly-climatology-v1`**, não uma promoção das
métricas antigas. Ele usa somente precipitação de treino de 1940–2022, preserva os IDs
do arquivo oficial e foi validado num bloco futuro completo de 2019–2022. A checagem
também confirma grade `301 × 261`, 24 meses-alvo, `time_origem = T−1` e `tp_alvo` do
teste inteiramente ausente.

PCA/LSTM, ConvLSTM, XGBoost e ONI continuam como candidatos de pesquisa. A branch mais
recente do WORCAP não foi promovida porque sua auditoria encontrou atmosfera do
mês-alvo; o ONI centrado também exige prova adicional de disponibilidade temporal.
Assim, o CSV atual é tecnicamente válido e completo, mas representa a régua de
climatologia — não há alegação de que supere essa própria régua nem de pontuação
oficial. Um modelo mais forte só deve substituí-lo depois de repetir todas as mesmas
salvaguardas e obter RMSE temporal inferior.

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
2. confirmar que `/health` retorna `api_version=0.4.0` e `model_contract_version=1.4`;
3. copiar a URL HTTPS criada;
4. cadastrar essa URL como variável `VITE_API_URL` no repositório do frontend;
5. executar novamente o workflow **Deploy Pages**.

O CORS de produção já permite `https://soubeatrizkaroline.github.io`.

## Atribuição

*Contains modified Copernicus Climate Change Service information 2026. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.*
