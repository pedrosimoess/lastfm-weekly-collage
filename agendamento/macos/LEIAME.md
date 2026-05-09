# Agendamento no macOS — launchd

O macOS usa o **launchd** para tarefas agendadas (o equivalente nativo ao cron, mais robusto e integrado ao sistema).

## Como funciona

O arquivo `com.pedro.tapmusic.plist` define um agente que roda toda **sexta-feira às 9h** e executa `tapmusic.py`. Logs são salvos em `Logs/tapmusic.log`.

---

## Instalação passo a passo

### 1. Ajuste os caminhos no `.plist`

Abra `com.pedro.tapmusic.plist` num editor de texto e substitua os caminhos pelos corretos para o seu sistema:

| Chave                  | O que editar                                      |
|------------------------|---------------------------------------------------|
| `ProgramArguments[0]`  | Caminho do Python (venv ou sistema)               |
| `ProgramArguments[1]`  | Caminho absoluto para `tapmusic.py`               |
| `WorkingDirectory`     | Pasta onde está `tapmusic.py`                     |
| `StandardOutPath`      | Arquivo de log (normalmente na pasta `Logs/`)     |
| `StandardErrorPath`    | Mesmo caminho do log acima                        |

Para descobrir o caminho do seu Python:
```bash
which python3
# ou, se usar ambiente virtual:
which python  # dentro do venv ativo
```

### 2. Instale o agente

```bash
cp agendamento/macos/com.pedro.tapmusic.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pedro.tapmusic.plist
```

### 3. Verifique se foi carregado

```bash
launchctl list | grep tapmusic
# Saída esperada: -   0   com.pedro.tapmusic
```

O primeiro campo é o PID (- significa que não está rodando agora, o que é normal).  
O segundo campo é o código de saída da última execução (0 = sucesso).

---

## Testar sem esperar sexta-feira

```bash
launchctl start com.pedro.tapmusic
```

Verifique o resultado no log:
```bash
tail -f Logs/tapmusic.log
```

---

## Desinstalar

```bash
launchctl unload ~/Library/LaunchAgents/com.pedro.tapmusic.plist
rm ~/Library/LaunchAgents/com.pedro.tapmusic.plist
```

---

## Observações

- **Mac bloqueado:** o launchd roda mesmo com o Mac bloqueado. A importação para o app Fotos pode falhar neste cenário (timeout de 30 s), mas o iCloud Drive funciona normalmente.
- **Mac desligado às 9h:** a tarefa **não** é recuperada automaticamente ao ligar o Mac. Se quiser executar assim que ligar, mude `RunAtLoad` para `true` no plist.
- **Alterar o horário:** edite `Hour` e `Minute` no plist, depois recarregue:
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.pedro.tapmusic.plist
  launchctl load   ~/Library/LaunchAgents/com.pedro.tapmusic.plist
  ```
