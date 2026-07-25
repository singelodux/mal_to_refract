# MyAnimeList To Refract

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3](https://img.shields.io/badge/python-3-blue.svg)

[English](README.md) | **Português**

Converte a tua lista de anime do MyAnimeList para o formato "TV Time Liberator" que o import de TV Time do [Refract](https://getrefract.app/) aceita — para quem, como eu, ficou sem os dados do TV Time quando ele fechou.

---

## 💔 Porquê isto existe

Toda saga de anime tem a sua traição inesquecível — aquele melhor amigo que vira vilão do nada. Desta vez não foi ficção — o TV Time fez questão de garantir a sua vaga no Top 10 traições dos animes.

Usei o TV Time desde 16 de julho de 2020, com 331 séries seguidas e 4928 likes registados. Fechou com apenas 15 dias de aviso, e quando fui à procura dos meus dados 3 dias depois, o portal oficial de GDPR (`gdpr.tvtime.com`) já tinha o DNS morto. Anos de histórico, gone.

Este repositório é o Plano C das minhas tentativas de recuperação — o único que funcionou. O resto do registo (o que não funcionou) está no fundo, em "Minhas tentativas".

---

## ⚙️ Como funciona

**Aceita:** o export oficial de anime do MyAnimeList (`https://myanimelist.net/panel.php?go=export` → "Anime List") — qualquer pessoa consegue tirar o seu, mesmo sem nunca ter tido conta no TV Time.

**Produz:** o formato **"TV Time Liberator"** — o mesmo schema que a extensão Chrome oficial do Refract produzia quando o TV Time ainda estava no ar, e que o import "TV Time" do Refract continua a aceitar:

- `tvtime-series-<hoje>.json` — séries seguidas + episódios vistos
- `tvtime-movies-<hoje>.json` — filmes vistos

Schema documentado pelo conversor open-source [jeremy-albinet/tvtime-to-refract-converter](https://github.com/jeremy-albinet/tvtime-to-refract-converter), a partir do export GDPR real do TV Time.

No processo, resolve um problema real: o MAL dá a cada temporada de um anime o seu próprio id (ex: "Attack on Titan" e "Attack on Titan Season 2" são entradas separadas), mas o TV Time/TheTVDB tratam a série toda como uma única entrada com várias temporadas. O script funde as entradas certas usando o mapeamento comunitário [Fribb/anime-lists](https://github.com/Fribb/anime-lists). Detalhe completo em [docs/mal-import](docs/mal-import/).

---

## 🚀 Como começar

### 1. Pré-requisitos

Não precisas de saber programar, só:

- **Python 3** — confirma com `python3 --version` num terminal. Não tens? Instala em [python.org/downloads](https://www.python.org/downloads/) (Windows: marca "Add Python to PATH" durante a instalação).
- **Este repositório, descarregado** — não precisas de `git`. Clica em **Code → Download ZIP** na [página do repo](https://github.com/singelodux/mal_to_refract) e descompacta onde quiseres.

### 2. Abrir um terminal na pasta do projeto

- **Windows**: segura Shift e clica com o botão direito num espaço vazio dentro da pasta → "Abrir janela do PowerShell aqui".
- **Mac**: clica com o botão direito na pasta → Serviços → "Novo Terminal na Pasta" (ou abre o Terminal e escreve `cd`, depois arrasta a pasta para dentro).
- **Linux**: clica com o botão direito dentro da pasta, no gestor de ficheiros → "Abrir num Terminal".

### 3. Correr

```bash
# Exporta a tua lista em https://myanimelist.net/panel.php?go=export → "Anime List"
# Coloca o ficheiro descarregado em private/mal/, depois corre:
python3 mal_to_refract.py
# O resultado (2 ficheiros .json) aparece em private/output/
```

### 4. Importar no Refract

> ⚠️ **Nota:** este script foi pensado para quem nunca chegou a importar dados reais do TV Time. Se já importaste séries/filmes do TV Time no Refract antes, correr este import por cima pode sobrescrever esses dados — faz um backup do teu import atual primeiro. Se decidires arriscar mesmo assim, conta-nos o resultado.

Refract → Definições/Import → **"TV Time"** → seleciona os dois `.json` de `private/output/`. O Refract mostra quantas séries/filmes reconheceu.

---

## 🔒 Privacidade

Corre inteiramente no teu computador — não envia nada para lado nenhum, exceto o download único e público do mapeamento [Fribb/anime-lists](https://github.com/Fribb/anime-lists) (`anime-list-full.json`, dados de terceiros sobre animes, não teus).

Tudo o que é pessoal (o teu export do MAL, os ficheiros gerados) vive em `private/`, fora do controlo de versões (ver `.gitignore`) — ver "Estrutura do repo" abaixo.

---

## 📁 Estrutura do repo

| Caminho | Conteúdo |
| --- | --- |
| [`docs/`](docs/) | resultados documentados de cada plano (público, sem dados pessoais) |
| [`docs/resources/`](docs/resources/) | notas de terceiros, dados de exemplo, `tvtime_recover.py` |
| [`mal_to_refract.py`](mal_to_refract.py) | o script, na raiz |
| `private/` | dados pessoais, exports e resultados reais (fora do repo público, ver `.gitignore`) |
| `private/mal/` | exports brutos do MyAnimeList |
| `private/output/` | resultados reais gerados pelos scripts sobre os meus dados |

---

## 🧭 Minhas tentativas: Planos A–D

| Plano | Resultado | Detalhe |
| --- | --- | --- |
| **A** — cache do Android sem root | ❌ Beco sem saída — `adb backup` bloqueado para apps de terceiros desde o Android 12 | [docs/unrooted-android](docs/unrooted-android/) |
| **B** — storage do browser | ❌ Beco sem saída — sessão válida guardada localmente, mas o backend está completamente desligado | [docs/browser-storage](docs/browser-storage/) |
| **C** — reconstruir a lista via MAL | ✅ Funciona — é o `mal_to_refract.py` acima | [docs/mal-import](docs/mal-import/) |
| **D** — registar tudo de novo | 🤷 Só o que sobrar — a maioria já estava também no MAL, só faltam filmes e séries | — |

Espero ter ajudado de algum jeito.

---

## 📄 Licença

[MIT](./LICENSE)
