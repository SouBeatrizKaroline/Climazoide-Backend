# Fontes de dados e integrações

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

- **Uso sugerido:** produtos nacionais de previsão e monitoramento para comparação visual, não como verdade do alvo.
- **Portal:** https://www.cptec.inpe.br/
- **Antes de integrar:** confirmar produto, endpoint, termos, frequência e estabilidade diretamente na documentação do produto escolhido.

## Extras internacionais

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
