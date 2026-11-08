<#
  Desliga o sistema 24h: para e remove as tarefas agendadas.
  O banco e os backups NÃO são apagados.

  Rodar no PowerShell COMO ADMINISTRADOR:
    powershell -ExecutionPolicy Bypass -File scripts\remover_servico.ps1
#>
#Requires -RunAsAdministrator

foreach ($nome in "SitioFestas - Sistema", "SitioFestas - Backup") {
    if (Get-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $nome -Confirm:$false
        Write-Host "Removida: $nome"
    }
}
Write-Host "Pronto. O banco e os backups continuam guardados."
