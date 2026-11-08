<#
  Deixa o sistema ligado 24h neste computador, criando 2 tarefas agendadas:
    * "SitioFestas - Sistema": liga o sistema quando o Windows inicia
      (mesmo sem ninguém fazer login) e reinicia sozinho se ele cair.
    * "SitioFestas - Backup": backup do banco todo dia às 03:00.

  Rodar no PowerShell COMO ADMINISTRADOR, dentro da pasta do projeto:
    powershell -ExecutionPolicy Bypass -File scripts\instalar_servico.ps1 -PastaBackup "C:\Users\SEU_USUARIO\OneDrive\Backups Sitio"

  Para desfazer: scripts\remover_servico.ps1
#>
#Requires -RunAsAdministrator
param(
    [string]$PastaBackup = ""
)

$ErrorActionPreference = "Stop"
$Raiz = Split-Path -Parent $PSScriptRoot

# O banco NÃO pode ficar numa pasta sincronizada: o OneDrive copiando o
# arquivo enquanto o sistema grava pode corromper o banco.
if ($Raiz -match "OneDrive|Dropbox|Google Drive") {
    Write-Error "O projeto está numa pasta sincronizada ($Raiz). Clone em C:\SitioFestas (ver docs/implantacao.md)."
}
if (-not (Test-Path (Join-Path $Raiz ".venv\Scripts\python.exe"))) {
    Write-Error "Ambiente .venv não encontrado. Crie com: py -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt"
}
if (-not (Test-Path (Join-Path $Raiz "database\sitio.db"))) {
    Write-Error "Banco não encontrado. Cadastre a senha antes: py -m database.criar_usuario"
}

$Usuario = "$env:USERDOMAIN\$env:USERNAME"
# S4U: roda com o seu usuário mesmo sem login, sem precisar guardar sua senha do Windows
$Principal = New-ScheduledTaskPrincipal -UserId $Usuario -LogonType S4U -RunLevel Limited

# ---- Tarefa 1: sistema ----
$argsIniciar = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Raiz\scripts\iniciar_sistema.ps1`""
if ($PastaBackup) { $argsIniciar += " -PastaBackup `"$PastaBackup`"" }

Register-ScheduledTask -TaskName "SitioFestas - Sistema" -Force `
    -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argsIniciar -WorkingDirectory $Raiz) `
    -Trigger (New-ScheduledTaskTrigger -AtStartup) `
    -Principal $Principal `
    -Settings (New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable) | Out-Null

# ---- Tarefa 2: backup diário ----
$argsBackup = "-m database.backup"
if ($PastaBackup) { $argsBackup += " `"$PastaBackup`"" }

Register-ScheduledTask -TaskName "SitioFestas - Backup" -Force `
    -Action (New-ScheduledTaskAction -Execute "$Raiz\.venv\Scripts\python.exe" -Argument $argsBackup -WorkingDirectory $Raiz) `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 3am) `
    -Principal $Principal `
    -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries) | Out-Null

Start-ScheduledTask -TaskName "SitioFestas - Sistema"
Write-Host "Pronto! O sistema está rodando e vai ligar sozinho junto com o computador." -ForegroundColor Green
Write-Host "Teste neste computador: http://localhost:8501"
