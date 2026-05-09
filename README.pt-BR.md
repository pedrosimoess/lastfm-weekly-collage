# tapmusic-collage

Gera automaticamente uma collage semanal dos álbuns mais ouvidos no Last.fm usando o [tapmusic.net](https://tapmusic.net) e salva localmente. Sem automação de browser — apenas uma requisição HTTP direta.

**Bônus no macOS:** importa para o app Fotos e sincroniza via iCloud Drive para o iPhone.

---

## Funcionalidades

- Baixa uma collage de álbuns 3×3 (ou outro tamanho) para qualquer usuário do Last.fm
- Salva as imagens em `Imagens/` com nome datado (`tapmusic_YYYY-MM-DD.png`)
- Funciona em **macOS, Windows e Linux**
- No **macOS**: também importa para o app Fotos e copia para o iCloud Drive (`~/iCloud Drive/Tapmusic/`)
- Sem dependências externas — usa apenas a biblioteca padrão do Python

---

## Requisitos

- Python 3.8+
- Conta no [Last.fm](https://www.last.fm) com histórico de reprodução

---

## Início Rápido

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/tapmusic-collage.git
cd tapmusic-collage

# 2. Edite tapmusic.py — troque USERNAME pelo seu usuário do Last.fm
#    (e, se quiser, ajuste PERIOD, SIZE, CAPTIONS, PLAYCOUNT)

# 3. Execute
python tapmusic.py
```

A imagem é salva em `Imagens/tapmusic_YYYY-MM-DD.png`.

---

## Configuração

Abra `tapmusic.py` e edite o bloco no topo:

| Variável    | Padrão       | Opções                                                           |
|-------------|--------------|------------------------------------------------------------------|
| `USERNAME`  | `"pedrosexo"`| seu usuário do Last.fm                                           |
| `PERIOD`    | `"7day"`     | `7day` · `1month` · `3month` · `6month` · `12month` · `overall` |
| `SIZE`      | `"3x3"`      | `3x3` · `4x4` · `5x5` · `10x10`                                 |
| `CAPTIONS`  | `False`      | `True` para exibir nome do álbum/artista                         |
| `PLAYCOUNT` | `False`      | `True` para exibir contagem de plays                             |

---

## Agendamento

### macOS — launchd (toda sexta-feira às 9h)

Veja as instruções completas em [agendamento/macos/](agendamento/macos/).

```bash
# 1. Edite o .plist com os seus caminhos (Python + script)
nano agendamento/macos/com.pedro.tapmusic.plist

# 2. Instale
cp agendamento/macos/com.pedro.tapmusic.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pedro.tapmusic.plist

# 3. Verifique
launchctl list | grep tapmusic

# Testar manualmente
launchctl start com.pedro.tapmusic
```

Para desinstalar:
```bash
launchctl unload ~/Library/LaunchAgents/com.pedro.tapmusic.plist
rm ~/Library/LaunchAgents/com.pedro.tapmusic.plist
```

> **Dica:** se você usa ambiente virtual, defina `ProgramArguments[0]` no plist
> como o Python do venv, ex: `/Users/seu_usuario/tapmusic-env/bin/python`.

---

### Windows — Agendador de Tarefas

Veja as instruções completas em [agendamento/windows/](agendamento/windows/).

**Opção A — importar pela interface gráfica:**
1. Edite `agendamento/windows/tapmusic_task.xml`: substitua `C:\path\to\LastfmAutomacao` pelo caminho real.
2. Abra o Agendador de Tarefas → Ação → **Importar Tarefa…** → selecione o arquivo XML.

**Opção B — importar via PowerShell (executar como Administrador):**
```powershell
Register-ScheduledTask `
  -Xml (Get-Content agendamento\windows\tapmusic_task.xml | Out-String) `
  -TaskName "tapmusic" -Force
```

---

### Linux — cron

```bash
crontab -e
```

Adicione esta linha (toda sexta às 9h):
```
0 9 * * 5 /usr/bin/python3 /caminho/para/LastfmAutomacao/tapmusic.py >> /caminho/para/LastfmAutomacao/Logs/tapmusic.log 2>&1
```

---

## Estrutura de Pastas

```
tapmusic-collage/
├── tapmusic.py                        # script principal
├── requirements.txt
├── .gitignore
├── README.md                          # documentação em inglês
├── README.pt-BR.md                    # este arquivo
├── Imagens/                           # collages geradas (ignoradas pelo git)
│   └── tapmusic_YYYY-MM-DD.png
├── Logs/                              # logs de execução (ignorados pelo git)
│   └── tapmusic.log
└── agendamento/
    ├── macos/
    │   ├── com.pedro.tapmusic.plist   # agente launchd
    │   └── LEIAME.md                  # instruções em português
    └── windows/
        ├── tapmusic.bat               # wrapper batch
        ├── tapmusic_task.xml          # definição do Agendador de Tarefas
        └── LEIAME.md                  # instruções em português
```

---

## macOS — Caminho do iCloud Drive

O script copia a imagem para:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Tapmusic/
```
que aparece como `iCloud Drive/Tapmusic/` no Finder e sincroniza automaticamente para o iPhone.

---

## Licença

MIT
