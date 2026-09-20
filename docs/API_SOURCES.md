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
Dados atuais e previsão de sete dias também não são apresentados como a previsão mensal
M→M+1 da competição.

No contrato mensal, prever setembro significa usar no máximo dados de agosto. As APIs
operacionais podem mostrar condições atuais ao usuário, mas esses valores não entram
retroativamente na entrada do modelo científico para o mesmo mês.

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

- **Uso sugerido:** reprodução do contexto ERA5 e enriquecimento controlado.
- **Acesso:** cadastro, aceite manual dos termos do dataset e cliente `cdsapi`.
- **Documentação:** https://cds.climate.copernicus.eu/how-to-api
- **Cuidado:** registrar dataset, versão, variáveis, níveis, grade e transformação para mm/dia.

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
- **CSV completo/parcial:** o completo exige previsões válidas para todos os IDs oficiais na ordem exata. O parcial contém somente previsões válidas disponíveis para um subconjunto ordenado desses mesmos IDs; não usa o recorte experimental histórico, não completa ausências com zeros e não é aceito como entrega completa. Nenhum deles é liberado sem manifesto de modelo retreinado, artefato reproduzível e validação científica/temporal aprovada.
