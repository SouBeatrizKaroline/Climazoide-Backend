# Relatório de auditoria técnica da pesquisa

> **Atualização do produto — 19/09/2026, 22:56:51 (BRT, UTC−03:00):** o
> diagnóstico crítico abaixo continua válido para a branch consolidada do WORCAP.
> O Climazoide não promoveu esse pipeline. Foi criado no backend um baseline novo e
> independente de climatologia mensal, usando somente `treino_tp.nc` de 1940–2022.
> Ele foi validado em 2019–2022 (RMSE 1,882056 mm/dia), gerou 1.885.464 previsões
> para os IDs oficiais de 2023–2024 e passou nas verificações de ordem, cobertura,
> finitude, não negatividade e ausência de alvo no teste. Consulte o manifesto e
> `artifacts/submission_report.json`. Isso resolve a disponibilidade de um CSV
> baseline; não corrige nem aprova os modelos auditados na origem.

O diagnóstico detalhado atualizado está em
[`WORCAP_BRANCH_AUDIT.md`](WORCAP_BRANCH_AUDIT.md). A conclusão atual é **problema
crítico**: o pipeline consolidado mais recente usa atmosfera do mês-alvo no
treino/validação, e o ONI centrado do experimento pode conter SST do mês previsto.

Consequentemente:

- métricas antigas são históricas e não demonstram desempenho de previsão M→M+1;
- a correção encontrada em outras branches precisa ser integrada, retreinada e
  validada na versão final;
- nenhum modelo ou CSV **da branch científica auditada** estava aprovado naquele momento;
- o CSV parcial só pode conter previsões válidas associadas a IDs oficiais;
- não há evidência em código versionado de consulta direta ao alvo de 2023–2024,
  mas os arquivos binários não estavam disponíveis para inspeção independente.

Este documento substitui o parecer anterior, que descrevia a correção temporal
como concluída. A afirmação anterior não correspondia ao estado da branch mais
recente e não deve ser reutilizada.
