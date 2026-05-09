# Agendamento no Windows — Agendador de Tarefas

O Windows usa o **Agendador de Tarefas** (Task Scheduler) para executar scripts automaticamente em horários definidos.

## Arquivos incluídos

| Arquivo                | Descrição                                                   |
|------------------------|-------------------------------------------------------------|
| `tapmusic_task.xml`    | Definição da tarefa — importe diretamente no Agendador     |
| `tapmusic.bat`         | Wrapper `.bat` para rodar o script (opcional)              |

---

## Instalação passo a passo

### 1. Ajuste os caminhos

Antes de importar, abra `tapmusic_task.xml` num editor de texto e substitua **todas** as ocorrências de:
```
C:\path\to\LastfmAutomacao
```
pelo caminho real onde você clonou o repositório, por exemplo:
```
C:\Users\seu_usuario\Documents\LastfmAutomacao
```

Faça o mesmo para `tapmusic.bat` se for usá-lo.

### 2. Opção A — Interface gráfica

1. Pressione `Win + S` e pesquise **"Agendador de Tarefas"**.
2. No painel direito, clique em **Ação → Importar Tarefa…**
3. Selecione o arquivo `tapmusic_task.xml`.
4. Revise as configurações e clique em **OK**.

### 2. Opção B — PowerShell (como Administrador)

```powershell
Register-ScheduledTask `
  -Xml (Get-Content "agendamento\windows\tapmusic_task.xml" | Out-String) `
  -TaskName "tapmusic" -Force
```

---

## Testar manualmente

Pelo Agendador de Tarefas:
1. Encontre a tarefa **tapmusic** na lista.
2. Clique com o botão direito → **Executar**.

Pela linha de comando:
```cmd
schtasks /run /tn "tapmusic"
```

---

## Verificar a última execução

No Agendador de Tarefas, selecione a tarefa e veja a aba **Histórico** para conferir o resultado da última execução.

---

## Desinstalar

Pela interface:
1. Clique com o botão direito na tarefa → **Excluir**.

Via PowerShell:
```powershell
Unregister-ScheduledTask -TaskName "tapmusic" -Confirm:$false
```

---

## Sobre o `tapmusic.bat`

O arquivo `.bat` é um wrapper opcional. Você pode usá-lo como ação da tarefa no lugar do `python` direto — útil se quiser adicionar variáveis de ambiente ou ativar um ambiente virtual antes de rodar o script.

Edite as variáveis no topo do arquivo:
```batch
set PYTHON=python          :: ou caminho completo para python.exe
set SCRIPT=C:\...\tapmusic.py
set WORKDIR=C:\...\LastfmAutomacao
```

---

## Observações

- **Python no PATH:** se `python` não estiver no PATH do sistema, use o caminho completo, ex: `C:\Users\seu_usuario\AppData\Local\Programs\Python\Python312\python.exe`.
- **Ambiente virtual:** se usar venv, substitua `python` pelo caminho do Python dentro do venv: `C:\...\venv\Scripts\python.exe`.
- **Logs:** o script salva saída em `Logs\tapmusic.log` (dentro da pasta do repositório). O Agendador de Tarefas não redireciona stdout automaticamente; para ter log, use o arquivo `.bat` com redirecionamento:
  ```batch
  "%PYTHON%" "%SCRIPT%" >> "%WORKDIR%\Logs\tapmusic.log" 2>&1
  ```
