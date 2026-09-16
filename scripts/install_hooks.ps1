$hook = ".git/hooks/commit-msg"
$content = "#!/bin/sh`nnode scripts/validate_commit.mjs `"`$1`"`n"
[System.IO.File]::WriteAllText((Join-Path (Get-Location) $hook), $content)
Write-Host "Hook de commits instalado."
