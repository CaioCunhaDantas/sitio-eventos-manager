<#
  Inicia o sistema em modo "produção".
  Normalmente quem chama este script é a tarefa agendada do Windows
  (criada pelo instalar_servico.ps1), toda vez que o computador liga.

  1. Faz um backup do banco (segurança extra antes de subir).
  2. Sobe o Streamlit na porta 8501, só para este computador (localhost).
     O acesso pelo celular passa pelo Tailscale (ver docs/implantacao.md).
  Tudo o que acontece vai para logs\sistema.log.
#>
param(
    [string]$PastaBackup = "",
    [int]$Porta = 8501
)

$Raiz = Split-Path -Parent $PSScriptRoot   # pasta do projeto (um nível acima de scripts\)
Set-Location $Raiz

$PastaLogs = Join-Path $Raiz "logs"
New-Item -ItemType Directory -Force $PastaLogs | Out-Null
$Log = Join-Path $PastaLogs "sistema.log"
$Python = Join-Path $Raiz ".venv\Scripts\python.exe"

"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') iniciando ====" | Out-File $Log -Append -Encoding utf8

# 1. Backup ao ligar
$argsBackup = @("-m", "database.backup")
if ($PastaBackup) { $argsBackup += $PastaBackup }
& $Python @argsBackup 2>&1 | ForEach-Object { "$_" } | Out-File $Log -Append -Encoding utf8

# 2. Sistema (fica rodando até o computador desligar)
# Saída do Streamlit em arquivos próprios (recriados a cada vez que o sistema liga)
Start-Process -FilePath $Python -WorkingDirectory $Raiz -NoNewWindow -Wait `
    -ArgumentList "-m streamlit run app/main.py --server.headless true --server.port $Porta" `
    -RedirectStandardOutput (Join-Path $PastaLogs "streamlit.log") `
    -RedirectStandardError (Join-Path $PastaLogs "streamlit_erros.log")

# Se chegou aqui, o Streamlit parou: código de saída diferente de 0 faz o
# Windows reiniciar a tarefa (configurado no instalar_servico.ps1).
exit 1
