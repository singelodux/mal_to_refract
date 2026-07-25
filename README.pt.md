# MyAnimeList To Refract

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3](https://img.shields.io/badge/python-3-blue.svg)

[English](README.md) | **Português**

Converte a tua lista de anime do MyAnimeList para o formato "TV Time Liberator" que o import de TV Time do [Refract](https://getrefract.app/) aceita — para quem, como eu, ficou sem os dados do TV Time quando ele fechou.

## Porquê: TV Time garantiu vaga no Top 10 traições dos animes

Toda saga de anime tem a sua traição inesquecível — aquele melhor amigo que vira vilão do nada. Desta vez não foi ficção.

Usei o TV Time desde 16 de julho de 2020 — a app guardava a data exata, e eu, escravo de estatísticas, sabia-a de cor. Perdi tudo o que vinha registando, como a maioria: 331 séries seguidas, 4928 likes, sabe-se lá quantas horas de `time_spent`. Com muito orgulho, diga-se.

Senti-me traído: 15 dias de aviso não chega, e uma notificação in-app não é forma de fechar uma plataforma com uma comunidade gigante. Fui tentar recuperar os dados só 3 dias depois do encerramento — e o portal oficial de GDPR (`gdpr.tvtime.com`) já tinha o DNS morto. Anos de histórico, gone.

Este repositório é o registo do meu esforço (Planos A–D) para recuperar o máximo possível, para não ter de registar tudo de novo do zero — porque é isso que vai acontecer, já que sou escravo de estatísticas.

## Pelo menos tenho o MAL

### O que aceita

O export oficial de anime do MyAnimeList (`https://myanimelist.net/panel.php?go=export`, "Anime List") — qualquer pessoa consegue tirar o seu, mesmo sem nunca ter tido conta no TV Time.

### O que produz

O formato **"TV Time Liberator"** — o mesmo schema que a extensão Chrome oficial do Refract produzia quando o TV Time ainda estava no ar, e que o import "TV Time" do Refract continua a aceitar mesmo sem essa extensão:

- `tvtime-series-<hoje>.json` — séries seguidas + episódios vistos
- `tvtime-movies-<hoje>.json` — filmes vistos

O schema exato veio do conversor open-source [jeremy-albinet/tvtime-to-refract-converter](https://github.com/jeremy-albinet/tvtime-to-refract-converter), que o documenta a partir do export GDPR real do TV Time.

No processo, resolve um problema real: o MAL dá a cada temporada de um anime o seu próprio id (ex: "Attack on Titan" e "Attack on Titan Season 2" são entradas separadas), mas o TV Time/TheTVDB tratam a série toda como uma única entrada com várias temporadas. O script funde as entradas certas usando o mapeamento comunitário [Fribb/anime-lists](https://github.com/Fribb/anime-lists). Detalhe completo em [docs/mal-import](docs/mal-import/).

### O que precisas antes de começar

Não precisas de saber programar, mas precisas de duas coisas no teu computador:

1. **Python 3** — Mac e Linux normalmente já vêm com ele. Para confirmar, abre um terminal (ver abaixo como) e escreve:

   ```bash
   python3 --version
   ```

   Se aparecer `Python 3.x.x`, está tudo pronto. Se der erro tipo "comando não encontrado", instala em [python.org/downloads](https://www.python.org/downloads/) (no Windows, marca a caixa **"Add Python to PATH"** durante a instalação — é o erro mais comum quando as pessoas saltam esse passo).

2. **Este repositório, descarregado** — não precisas de `git`. Vai a [github.com/singelodux/mal_to_refract](https://github.com/singelodux/mal_to_refract), clica no botão verde **Code → Download ZIP**, e descompacta a pasta onde quiseres.

### Como abrir um terminal na pasta do projeto

- **Windows**: dentro da pasta descompactada, segura Shift e clica com o botão direito num espaço vazio → "Abrir janela do PowerShell aqui" (ou "Abrir no Terminal").
- **Mac**: clica com o botão direito na pasta → Serviços → "Novo Terminal na Pasta". (Se essa opção não existir, abre o Terminal normalmente, escreve `cd` e arrasta a pasta para a janela.)
- **Linux**: clica com o botão direito dentro da pasta, no gestor de ficheiros → "Abrir num Terminal".

### Como correr

```bash
# 1. Exporta a tua lista de anime em https://myanimelist.net/panel.php?go=export
#    (com sessão iniciada) → "Anime List" → sai um .xml ou .xml.gz

# 2. Coloca esse ficheiro dentro da pasta private/mal/ (dentro da pasta do projeto)

# 3. No terminal aberto na pasta do projeto, corre:
python3 mal_to_refract.py

# 4. O resultado (2 ficheiros .json) aparece na pasta private/output/
```

### Como importar no Refract

1. Abre o Refract → Definições/Import → escolhe a opção de import **"TV Time"**.
2. Quando pedir os ficheiros, seleciona os dois `.json` que saíram de `private/output/` (um é `tvtime-series-<data>.json`, o outro `tvtime-movies-<data>.json`).
3. Confirma o import — o Refract mostra quantas séries/filmes reconheceu.

## Privacidade

O script corre inteiramente no teu computador — não envia nada para lado nenhum, exceto o download único e público do mapeamento [Fribb/anime-lists](https://github.com/Fribb/anime-lists) (`anime-list-full.json`, dados de terceiros sobre animes, não teus).

Tudo o que é pessoal (o teu export do MAL, os ficheiros gerados) vive em `private/`, que está fora do controlo de versões (ver `.gitignore`) — só os `README.md` de cada subpasta ficam versionados, como guia de onde as coisas vão. Ver [Estrutura do repo](#estrutura-do-repo) abaixo.

## Estrutura do repo

| Caminho | Conteúdo |
| --- | --- |
| [`docs/`](docs/) | resultados documentados de cada plano (público, sem dados pessoais) |
| [`docs/resources/`](docs/resources/) | notas de terceiros, dados de exemplo, `tvtime_recover.py` |
| [`mal_to_refract.py`](mal_to_refract.py) | o script, na raiz |
| `private/` | dados pessoais, exports e resultados reais (fora do repo público, ver `.gitignore`) |
| `private/mal/` | exports brutos do MyAnimeList |
| `private/output/` | resultados reais gerados pelos scripts sobre os meus dados |

## Minhas tentativas: Planos A–D

| Plano | Resultado | Detalhe |
| --- | --- | --- |
| **A** — cache do Android sem root | ❌ Beco sem saída — `adb backup` bloqueado para apps de terceiros desde o Android 12 | [docs/unrooted-android](docs/unrooted-android/) |
| **B** — storage do browser | ❌ Beco sem saída — sessão válida guardada localmente, mas o backend está completamente desligado | [docs/browser-storage](docs/browser-storage/) |
| **C** — reconstruir a lista via MAL | ✅ Funciona — é o `mal_to_refract.py` acima | [docs/mal-import](docs/mal-import/) |
| **D** — registar tudo de novo | 🤷 Só o que sobrar — a maioria já estava também no MAL, só faltam filmes e séries | — |

Espero ter ajudado de algum jeito.

## Licença

[MIT](./LICENSE)
