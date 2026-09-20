# Changelog

Este projeto segue [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.6.0] - 2026-09-20

- implementa de forma independente o XGBoost de anomalias com nove variáveis oficiais em T−1;
- valida o candidato em 3.770.928 previsões de 2019–2022, sem consultar o alvo de 2023–2024;
- reduz o RMSE interno de 1,882056 para 1,838655 e preserva o baseline oficial até haver pontuação pública;
- publica separadamente o candidato completo, seu modelo reproduzível, relatório, hashes e testes de corte temporal;
- registra a pontuação pública 1,85077 do baseline já enviado.

## [0.5.0] - 2026-09-20

- cria a camada `Climazoide Decisão` para agricultura, agronegócio, áreas de risco, hidroenergia, turismo e gestão da água;
- cruza previsões mensais já validadas com estatísticas históricas locais, sem alterar a submissão oficial;
- identifica explicitamente os cenários 2023–2024 como históricos e não como previsão atual;
- adiciona limites setoriais e ações prudentes, sem prescrição automática ou alertas oficiais.

## [0.4.0] - 2026-09-20

- publica no manifesto as nove variáveis atmosféricas e o contrato completo do dataset oficial;
- acrescenta leitura cruzada da previsão curta com período, cobertura e proveniência;
- calcula chuva acumulada, dias chuvosos/quentes, concentração da chuva e correlação chuva–temperatura;
- mantém essas análises separadas do modelo mensal e explicita que correlação não implica causalidade.

## [0.3.3] - 2026-09-19

- gera um baseline completo de climatologia mensal com 1.885.464 previsões, usando apenas 1940–2022;
- valida temporalmente em 2019–2022, com RMSE interno de 1,882056 mm/dia;
- preserva os IDs oficiais, rejeita valores inválidos e registra hashes dos dados e da saída;
- publica o CSV compactado no backend e o entrega descompactado por streaming;
- mantém os dados brutos oficiais fora do repositório e separa baseline de pontuação oficial.

- atualiza a auditoria científica: branch consolidada não comprova alinhamento M→M+1, e bloqueia inferência/submissão sem aprovação temporal explícita;
- acrescenta MET Norway como contingência gratuita, com cache conforme validade da resposta e metadados de período;
- valida cada ID e sua ordem contra o arquivo oficial do conjunto de teste e exige manifesto de modelo validado antes de liberar o CSV completo;
- deixa a quantidade de linhas seguir os IDs oficiais, sem presumir meses a partir do exemplo de formato.
- registra a disponibilidade real dos campos de contingência e impede impactos de somas parciais tratadas como completas.
- substitui o download parcial histórico por um gerador de previsões parciais baseado somente nos IDs oficiais disponíveis.

## [0.3.2] - 2026-09-19

- atualiza o contrato público do modelo para `1.3`;
- troca rótulos públicos de entrega externa por linguagem própria do Climazoide;
- mantém a proveniência científica em documentação e auditoria, sem expor branch no CSV parcial.

## [0.3.1] - 2026-09-18

- adiciona retentativas e identificação do cliente nas fontes públicas;
- amplia o timeout do serviço publicado sem ocultar indisponibilidades;
- documenta APIs, dados e os papéis de frontend, backend e WORCAP-2026.

## [0.3.0] - 2026-09-18

- auditoria das oito branches remotas do WORCAP-2026;
- catálogo científico rastreável em `/v1/research/branches`;
- documentação da estratégia de migração sem copiar binários ou promover métricas experimentais;
- contrato científico atualizado para a consolidação mais recente.

## [0.2.0] - 2026-09-16

- integração com Open-Meteo, CAMS/Copernicus, CPTEC/INPE, NASA POWER, NOAA CPC e USNO;
- cobertura operacional de 13 pontos sul-americanos;
- proveniência, disponibilidade e horário das fontes;
- manifesto dos modelos WORCAP e validação de submissão Kaggle;
- contêiner, blueprint Render, testes e CI.
