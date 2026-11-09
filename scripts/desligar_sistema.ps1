<#
  Desliga o sistema AGORA (até ligar de novo ou o computador reiniciar).
  O banco e os backups não são tocados.

  Rodar no PowerShell COMO ADMINISTRADOR:
    powershell -ExecutionPolicy Bypass -File C:\SitioFestas\scripts\desligar_sistema.ps1

  Parar só a tarefa agendada não basta: o Python do sistema é um processo
  "filho" e continuaria rodando. Por isso também encerramos quem usa a porta.
#>
#Requires -RunAsAdministrator
param([int]$Porta = 8501)

Stop-ScheduledTask -TaskName "SitioFestas - Sistema" -ErrorAction SilentlyContinue

Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2
if (Get-NetTCPConnection -LocalPort $Porta -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "Ainda tem algo usando a porta $Porta. Tente de novo." -ForegroundColor Yellow
} else {
    Write-Host "Sistema desligado." -ForegroundColor Green
    Write-Host "Ele volta sozinho quando o computador reiniciar, ou com ligar_sistema.ps1."
}
