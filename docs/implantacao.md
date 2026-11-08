# Implantação: sistema ligado 24h

Como colocar o sistema para uso real: rodando 24h num computador de casa,
acessível pelo celular/tablet com segurança, com backup diário.

```
 Celular / tablet ──(Tailscale: rede privada criptografada, HTTPS)──► PC de casa
                                                                      ├─ Streamlit (só localhost:8501)
                                                                      ├─ C:\SitioFestas\database\sitio.db
                                                                      └─ backup diário → OneDrive
```

**Por que assim?**
- **Nada fica exposto na internet.** O Streamlit só aceita conexões do próprio PC.
  O Tailscale leva até ele apenas os aparelhos logados na sua conta.
- **Custo zero.** Tailscale é gratuito para uso pessoal.
- **O banco fica fora do OneDrive.** Se o OneDrive sincronizar o arquivo enquanto o
  sistema grava, o banco pode corromper. Os *backups* vão para o OneDrive, e aí
  sim: vira uma cópia fora de casa.

---

## 1. Cópia de produção (fora do OneDrive)

No PC que vai ficar ligado, no PowerShell:

```powershell
git clone https://github.com/CaioCunhaDantas/sitio-eventos-manager.git C:\SitioFestas
cd C:\SitioFestas
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Cadastrar a senha (com segurança)

```powershell
cd C:\SitioFestas
py -m database.criar_usuario
```

- Confira se a linha `Banco:` mostra `C:\SitioFestas\database\sitio.db`.
- Digite o nome e depois a senha duas vezes. Ela **não aparece** na tela e
  não fica no histórico do terminal.
- O banco guarda só o *hash* (PBKDF2), nunca a senha.
- **Nunca** escreva a senha em arquivo, commit, mensagem ou comando.
- Para trocar a senha depois: rode o mesmo comando e digite **o mesmo nome**.

## 3. Testar uma vez à mão

```powershell
.\.venv\Scripts\streamlit run app/main.py
```

Entre com a senha em `http://localhost:8501`. Depois feche com **Ctrl + C**.

## 4. Ligar 24h (tarefa agendada do Windows)

Abra o PowerShell **como Administrador** e rode:

```powershell
cd C:\SitioFestas
powershell -ExecutionPolicy Bypass -File scripts\instalar_servico.ps1 -PastaBackup "C:\Users\SEU_USUARIO\OneDrive\Backups Sitio"
```

Isso cria duas tarefas (você pode vê-las no **Agendador de Tarefas**):

| Tarefa | O que faz |
|---|---|
| SitioFestas - Sistema | Liga o sistema quando o Windows inicia (mesmo sem login) e reinicia sozinho se cair |
| SitioFestas - Backup | Backup do banco todo dia às 03:00 (guarda os últimos 60) |

Para desfazer: `powershell -ExecutionPolicy Bypass -File scripts\remover_servico.ps1`
(como Administrador). O banco e os backups não são apagados.

## 5. Não deixar o PC dormir

Em **Configurações → Sistema → Energia**, coloque "Suspender" em **Nunca**
quando estiver na tomada. Ou, como Administrador:

```powershell
powercfg /change standby-timeout-ac 0
```

A tela pode desligar, sem problema. Só o PC não pode suspender.

## 6. Acesso pelo celular/tablet (Tailscale)

1. Instale o Tailscale no PC (tailscale.com/download) e entre com uma conta
   (Google ou Microsoft).
2. Instale o app **Tailscale** no celular/tablet e entre com a **mesma conta**.
3. No PC, publique o sistema só para a sua rede Tailscale, com HTTPS:
   ```powershell
   tailscale serve --bg 8501
   ```
   O comando mostra um endereço como `https://nome-do-pc.algo.ts.net`.
   A configuração fica salva e volta sozinha depois de reiniciar.
4. No celular, abra esse endereço e use **"Adicionar à tela inicial"**. Vira
   um ícone, como se fosse um app.

Deixe o Tailscale do celular sempre ligado. Ele roda em segundo plano.

---

## Dia a dia

**Onde estão os logs?** Em `C:\SitioFestas\logs\`:

| Arquivo | Conteúdo |
|---|---|
| `sistema.log` | Início do sistema e backups |
| `streamlit.log` | Saída do Streamlit |
| `streamlit_erros.log` | Erros do Streamlit |

**Backup manual a qualquer hora:**
```powershell
cd C:\SitioFestas
.\.venv\Scripts\python.exe -m database.backup "C:\Users\SEU_USUARIO\OneDrive\Backups Sitio"
```

**Restaurar um backup** (como Administrador):
```powershell
Stop-ScheduledTask "SitioFestas - Sistema"
Copy-Item "C:\...\Backups Sitio\sitio_AAAA-MM-DD_HHMMSS.db" C:\SitioFestas\database\sitio.db
Start-ScheduledTask "SitioFestas - Sistema"
```

**Atualizar para uma versão nova do código** (como Administrador):
```powershell
cd C:\SitioFestas
git pull
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Stop-ScheduledTask "SitioFestas - Sistema"; Start-ScheduledTask "SitioFestas - Sistema"
```
Se o banco mudou de estrutura, as migrações rodam sozinhas ao ligar.
Antes disso, o script faz um backup.

**O sistema não abre?** Veja `logs\streamlit_erros.log` e confira se a tarefa
está "Em execução" no Agendador de Tarefas.
