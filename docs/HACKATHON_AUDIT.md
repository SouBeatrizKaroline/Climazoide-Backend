# Relatório de auditoria técnica da pesquisa

O diagnóstico detalhado atualizado está em
[`WORCAP_BRANCH_AUDIT.md`](WORCAP_BRANCH_AUDIT.md). A conclusão atual é **problema
crítico**: o pipeline consolidado mais recente usa atmosfera do mês-alvo no
treino/validação, e o ONI centrado do experimento pode conter SST do mês previsto.

Consequentemente:

- métricas antigas são históricas e não demonstram desempenho de previsão M→M+1;
- a correção encontrada em outras branches precisa ser integrada, retreinada e
  validada na versão final;
- nenhum modelo ou CSV está aprovado para download como previsão completa;
- o CSV parcial só pode conter previsões válidas associadas a IDs oficiais;
- não há evidência em código versionado de consulta direta ao alvo de 2023–2024,
  mas os arquivos binários não estavam disponíveis para inspeção independente.

Este documento substitui o parecer anterior, que descrevia a correção temporal
como concluída. A afirmação anterior não correspondia ao estado da branch mais
recente e não deve ser reutilizada.
