# Auditoria de aderência ao WORCAP 2026

Data da auditoria: **16 de setembro de 2026**.

## Veredito

O projeto está estruturado para o desafio e possui pipeline científico, API, interface e checagem de submissão. Ainda não deve ser chamado de **submissão final pronta**: a auditoria encontrou um desalinhamento temporal na validação histórica, o download oficial exige autenticação e aceite das regras no Kaggle, e os pesos, objetos PCA e o CSV candidato não estão disponíveis neste repositório.

As integrações recentes são uma camada operacional complementar. Elas não substituem o ERA5, não alteram o alvo secreto e não são apresentadas como pontuação oficial.

## Matriz de conformidade

| Exigência | Evidência atual | Estado |
|---|---|---|
| Prever precipitação média de `M+1` | índice corrigido para usar atmosfera de `alvo - 1` | corrigido, requer retreino |
| Cobrir toda a América do Sul | domínio declarado `60°S–15°N`, `90°O–25°O`, grade `301 × 261` | atendido no pipeline |
| Usar os 13 arquivos oficiais | download confere os nomes esperados | pronto, depende do acesso Kaggle |
| Treino 1940–2022 | carregamento e divisão temporal documentados no repositório científico | atendido no código |
| Avaliação 2023–2024 sem acessar o alvo | manifesto não declara alvo de teste nem score privado | atendido por desenho |
| RMSE como métrica | avaliação calcula RMSE global, mas métricas antigas foram invalidadas pelo alinhamento | requer retreino |
| Baselines | climatologia e persistência documentadas e comparadas | atendido |
| `id,tp_mm_day` em ordem | validador compara linha a linha com o `sample_submission.csv` | atendido no validador |
| 1.885.464 previsões | auditor exige a contagem oficial | atendido no validador |
| Sem NaN, infinito ou valor negativo | validação em streaming rejeita esses casos | atendido |
| Código e documentação públicos | frontend e backend públicos, README e fontes documentados | atendido |
| Reprodutibilidade integral | semente registrada; pesos e PCA ainda precisam ser regenerados ou publicados | pendente |
| Score público/privado Kaggle | nenhum score oficial foi informado | pendente |
| ConvLSTM | não há evidência de modelo final validado no produto | fora do modelo ativo |

## Achado crítico corrigido

No treino histórico, `alvo_atm` era obtido em `alvo_idx`. Isso permitia que a validação enxergasse as variáveis atmosféricas do próprio mês a prever. O dataset de teste informa, em cada posição de mês-alvo, campos do mês anterior em `time_origem`.

O pipeline passou a usar `alvo_idx - 1` no treino. A inferência continua lendo diretamente os campos de `teste_features.nc`, pois ali o deslocamento já foi aplicado pela organização. As métricas antigas ficam preservadas apenas como histórico de execução, não como evidência válida.

## Cobertura geográfica

Há duas coberturas diferentes, deliberadamente separadas:

1. **Científica:** todos os 78.561 pontos da grade ERA5, em cada um dos 24 meses avaliados. Esta é a cobertura que vale para o ranking.
2. **Operacional:** 13 pontos representativos de Argentina, Bolívia, Brasil, Chile, Colômbia, Equador, Guiana, Paraguai, Peru, Suriname, Uruguai, Venezuela e Guiana Francesa. Esta camada mostra condições recentes e contexto público.

Uma capital por território não equivale à grade do desafio. O painel informa essa limitação para evitar uma conclusão incorreta.

## Dados públicos complementares

| Fonte | Uso permitido no produto | Limite |
|---|---|---|
| Open-Meteo | tempo recente, previsão de sete dias, solo e evapotranspiração | não é o alvo ERA5 mensal |
| CAMS/Copernicus | composição atmosférica e AQI | apoio ambiental, não avaliação médica |
| CPTEC/INPE | referência meteorológica no Brasil | não se aplica aos demais países |
| NOAA CPC | ONI e fase do ENSO | contexto de grande escala, não causalidade local |
| USNO | nascer/pôr do Sol e fase lunar | contexto astronômico |
| NASA POWER | séries agroclimáticas mensais | fonte auxiliar, resolução diferente |
| INMET e TerraBrasilis | fontes brasileiras candidatas | só entram como ativas após endpoint estável e validação |

## Checklist para uma submissão real

1. Entrar no Kaggle e aceitar as regras da competição.
2. Executar `python scripts/download_competition.py`.
3. Treinar novamente o pipeline científico com ambiente e semente registrados.
4. Gerar as 24 grades na ordem temporal do arquivo de teste.
5. Preencher os IDs diretamente a partir do `sample_submission.csv`.
6. Executar:

```bash
python scripts/audit_readiness.py CAMINHO_DOS_DADOS --submission submission.csv
```

7. Registrar hash do CSV, commit, configuração, métricas internas e versão das dependências.
8. Enviar ao Kaggle e registrar separadamente score público e privado.

## Critério de comunicação

- **Comprovado:** código, testes locais, métricas internas e respostas públicas observadas.
- **Pendente:** download autenticado, artefatos regenerados, submissão final e score Kaggle.
- **Extra:** painel recente, AQI, ENSO, astronomia e indicadores derivados.

Essa distinção deve permanecer no README, na interface e em qualquer apresentação do projeto.

## Revisão de branches e forks

Foram comparadas `main`, `Beatriz`, `vermelho` e o fork público `SouBeatrizKaroline/WORCAP-2026`.

- `Beatriz`: mantém o contrato temporal corrigido, testes de contrato e IDs oficiais.
- `vermelho`: acrescenta PLS concorrente/defasado, checkpoints por época e orquestração de experimentos. As ideias são úteis, mas o código deriva da versão anterior à correção temporal e não foi promovido como resultado.
- fork `SouBeatrizKaroline/main`: aponta para a base anterior e não contém ganho adicional sobre a versão auditada.

O manifesto registra essa proveniência e impede que um candidato de pesquisa apareça como modelo validado.
