# Fontes de dados e integrações

## Como as camadas se relacionam

O [Climazoide-Backend](https://github.com/SouBeatrizKaroline/Climazoide-Backend)
integra dados públicos e entrega respostas normalizadas. O
[Climazoide-Frontend](https://github.com/SouBeatrizKaroline/Climazoide-Frontend)
apenas apresenta essas respostas e não guarda credenciais. O
[WORCAP-2026](https://github.com/mazeeqe/WORCAP-2026) é o repositório de pesquisa,
testes de modelos e experimentos científicos. Código experimental e métricas ainda
não promovidas permanecem nele e aparecem no produto somente como estado de pesquisa.

Os pontos operacionais do painel não substituem a grade científica ERA5 de 301 × 261.
No contrato mensal, prever setembro significa usar no máximo dados de agosto.

## Declaração de uso atual

| Grupo | Fontes | Papel | Entra no modelo/CSV? |
| --- | --- | --- | --- |
| oficial | 13 arquivos distribuídos | treino, teste e IDs | **sim** |
| meteorologia recente | Open-Meteo, MET Norway e CPTEC | painel de curto prazo | não |
| ambiente e clima | CAMS, NOAA CPC e NASA POWER | contexto e comparação | não |
| astronomia | USNO | efemérides | não |
| referências futuras | ERA5/CDS, INMET, PClima e Embrapa | pesquisa documentada | não |

O baseline e o `xgboost-anomaly-v1` foram produzidos somente com arquivos oficiais. As
fontes adicionais deixam a solução mais completa, mas não treinam, calibram, corrigem
ou preenchem a submissão. Dados atuais também nunca são aplicados retroativamente.

## Exigido para a competição

### Kaggle / WORCAP 2026

- **Uso:** baixar os 13 arquivos oficiais e enviar `submission.csv`.
- **Exigência:** conta, aceite das regras, credencial individual e IDs preservados do arquivo de exemplo.
- **Documentação:** https://www.kaggle.com/docs/api
- **Observação:** o dataset da competição é o contrato de avaliação. Nenhuma API externa substitui essa base.

## Extras nacionais

### INMET

- **Uso sugerido:** observações de estações brasileiras para contexto e análise de consistência.
- **Acesso:** o portal informa que o acesso à API deve ser solicitado por `api@inmet.gov.br`.
- **Canal oficial:** https://portal.inmet.gov.br/fale-conosco
- **Dados históricos:** https://bdmep.inmet.gov.br/
- **Cuidado:** dados horários podem ser brutos, conter `9999`, `null` ou lacunas; registrar UTC e rotina de qualidade.

### INPE / CPTEC

- **Uso implementado:** previsão nacional de sete dias por coordenadas, como comparação independente.
- **Documentação:** https://servicos.cptec.inpe.br/XML/
- **Comportamento:** o adaptador não bloqueia o painel quando o serviço recusa ou interrompe a consulta; retorna `available: false` e preserva as demais fontes reais.

## Extras internacionais

### Open-Meteo

- **Uso implementado:** condição atual, previsão de sete dias, chuva, vento, solo e evapotranspiração.
- **Documentação:** https://open-meteo.com/en/docs
- **Origem:** combinação de modelos de serviços nacionais, incluindo ECMWF, NOAA e DWD.
- **Acesso:** sem chave para o cenário não comercial do projeto; atribuição obrigatória.

### MET Norway · Locationforecast

- **Uso implementado:** contingência gratuita para condição e previsão de curto prazo quando a consulta meteorológica principal falha.
- **Documentação:** https://api.met.no/weatherapi/locationforecast/2.0/documentation
- **Limites de interpretação:** valores são previsão modelada, não observação de estação; timestamp de atualização do modelo e janela de validade acompanham a resposta. Campos não fornecidos (como probabilidade de chuva, umidade do solo e ET₀) continuam indisponíveis.
- **Atribuição e acesso:** requisição identifica o Climazoide por User-Agent; não requer chave.

### CAMS / Copernicus

- **Uso implementado:** AQI, PM2.5, PM10, CO, NO₂, ozônio e UV.
- **Documentação:** https://open-meteo.com/en/docs/air-quality-api
- **Origem:** CAMS European/Global, disponibilizado pelo endpoint do Open-Meteo.
- **Cuidado:** composição atmosférica modelada não equivale a sensor local nem orientação médica.

### ECMWF / Copernicus CDS · ERA5

- **Uso possível:** reprodução ou pesquisa futura, sob auditoria temporal.
- **Acesso:** cadastro, aceite manual dos termos do dataset e cliente `cdsapi`.
- **Documentação:** https://cds.climate.copernicus.eu/how-to-api
- **Cuidado:** a precipitação real de 2023–2024 é o alvo proibido e não pode ser
  consultada, mesmo sendo pública. Registrar dataset, versão, disponibilidade histórica,
  variáveis, níveis, grade e transformação para mm/dia.

### NASA POWER

- **Uso sugerido:** comparação rápida de séries meteorológicas mensais por ponto ou região.
- **Acesso:** API pública em JSON, CSV, ASCII ou NetCDF.
- **Documentação:** https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
- **Limites relevantes:** até 20 parâmetros em consulta pontual; região aceita um parâmetro. A resolução é a da fonte e não deve ser confundida com a grade ERA5 da competição.
- **Implementado:** `POST /v1/integrations/nasa-power/monthly`.

### NOAA PSL · ONI

- **Uso sugerido:** contexto ENSO no anel “El Niño/La Niña”.
- **Fonte:** https://psl.noaa.gov/data/correlation/oni.data
- **Cuidado:** mostrar período de três meses e data da leitura; ONI não é uma previsão de chuva nem deve entrar automaticamente no modelo sem validação temporal.

## Contrato mínimo para um novo conector

1. Cliente isolado em `app/services/`.
2. Timeout, tratamento de erro e nenhuma credencial no código.
3. Modelo de resposta validado.
4. Cache e limitação de requisições antes de produção.
5. Metadados de origem no payload.
6. Teste com resposta simulada; CI não deve depender de rede externa.

## Política de indisponibilidade

- cada fonte informa `available` e horário de atualização;
- uma falha externa não derruba o restante do painel;
- campos sem resposta usam `null`, nunca zero inventado;
- a API tenta novamente falhas transitórias da fonte meteorológica principal;
- o frontend traduz `null` como **Indisponível** e mantém visível a proveniência.

## Catálogo Embrapa AgroAPI e PClima

- **Embrapa AgroAPI:** APIs de cadastro agrícola/solo podem ser contexto complementar para decisões agropecuárias, mas não substituem observações, previsão meteorológica, ERA5 nem os IDs oficiais do arquivo de submissão. APIs freemium não são tratadas como gratuitas permanentes; nenhuma foi integrada por não acrescentar dado necessário ao objetivo científico atual.
- **PClima/INPE:** disponibiliza projeções climáticas por modelos e cenários, com credenciais; não é fonte de tempo atual ou previsão operacional de sete dias. Não é usado para preencher lacunas do painel nem para gerar o CSV M→M+1.
- **CSV completo/parcial:** o completo principal contém as 1.885.464 previsões do
  baseline na ordem oficial; o candidato XGBoost completo é publicado separadamente.
  O parcial só contém previsões válidas para um subconjunto ordenado dos mesmos IDs,
  sem preencher ausências. Nenhum artefato é liberado sem manifesto, geração
  reproduzível e validação científica/temporal aprovada.
