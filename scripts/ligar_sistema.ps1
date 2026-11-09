<#
  Liga o sistema de novo (depois de desligar_sistema.ps1).

  Rodar no PowerShell COMO ADMINISTRADOR:
    powershell -ExecutionPolicy Bypass -File C:\SitioFestas\scripts\ligar_sistema.ps1
#>
#Requires -RunAsAdministrator
param([int]$Porta = 8501)

if (Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "O sistema já está ligado." -ForegroundColor Green
    exit 0
}

Start-ScheduledTask -TaskName "SitioFestas - Sistema"

# Espera até 30 segundos o sistema responder
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $resposta = curl.exe -s -m 2 "http://localhost:$Porta/_stcore/health"
    if ($resposta -eq "ok") {
        Write-Host "Sistema ligado! http://localhost:$Porta" -ForegroundColor Green
        exit 0
    }
}
Write-Host "O sistema não respondeu. Veja C:\SitioFestas\logs\streamlit_erros.log" -ForegroundColor Yellow
exit 1
