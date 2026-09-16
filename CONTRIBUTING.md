# Como contribuir

A branch de integração deste projeto é `Beatriz`.

Antes de abrir PR, rode:

```bash
ruff check .
pytest
```

Os commits seguem `tipo(escopo): descrição`, com os tipos `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `build`, `ci` e `chore`.

Ative o validador local no Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_hooks.ps1
```

Regras de dados:

- nunca versionar tokens, `.nc`, submissões ou artefatos de modelo pesados;
- documentar instituição, URL oficial, licença/termos, resolução, período e transformação de cada fonte;
- marcar números simulados como `demo`;
- só marcar métricas como `calculated` quando houver conjunto, código e artefato reproduzíveis.
