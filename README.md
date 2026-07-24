# MyAnimeList To Refract

Converte a tua lista de anime do MyAnimeList para o formato "TV Time Liberator" que o import de TV Time do [Refract](https://getrefract.app/) aceita — para quem, como eu, ficou sem os dados do TV Time quando ele fechou.

## Porquê: Top 10 traições dos animes

Venho usando TV Time há anos — desde 16 de julho de 2020, para ser mais específico, a app guardava a data exata — e, como a maioria dos utilizadores, perdi tudo o que vinha registando: 331 séries seguidas, 4928 likes, e sabe-se lá quantas horas de `time_spent`. Escravo de estatísticas, com muito orgulho.

Senti-me traído. 15 dias sem notificar adequadamente as pessoas não é tempo suficiente. Notificação in-app para avisar do encerramento de uma plataforma com uma comunidade gigante é sacanagem, vindo de uma empresa que tem os nossos emails.

Como a maioria, visitei a plataforma tarde — 3 dias depois do encerramento no dia 15 de julho. Tentei buscar os meus dados pelo portal oficial de GDPR (`gdpr.tvtime.com`): o DNS já estava morto. Anos de histórico, simplesmente inacessíveis de um dia para o outro.

Este repositório é o registo do meu esforço (do Plano A ao D) para tentar recuperar o máximo possível dos meus dados, para não ter de registar tudo de novo do zero — porque é isso que vai acontecer, já que sou escravo de estatísticas.

## Pelo menos tenho o MAL

### O que aceita

O export oficial de anime do MyAnimeList (`https://myanimelist.net/panel.php?go=export`, "Anime List") — qualquer pessoa consegue tirar o seu, mesmo sem nunca ter tido conta no TV Time.

### O que produz

O formato **"TV Time Liberator"** — o mesmo schema que a extensão Chrome oficial do Refract produzia quando o TV Time ainda estava no ar, e que o import "TV Time" do Refract continua a aceitar mesmo sem essa extensão:

- `tvtime-series-<hoje>.json` — séries seguidas + episódios vistos
- `tvtime-movies-<hoje>.json` — filmes vistos

O schema exato veio do conversor open-source [jeremy-albinet/tvtime-to-refract-converter](https://github.com/jeremy-albinet/tvtime-to-refract-converter), que o documenta a partir do export GDPR real do TV Time.

No processo, resolve um problema real: o MAL dá a cada temporada de um anime o seu próprio id (ex: "Attack on Titan" e "Attack on Titan Season 2" são entradas separadas), mas o TV Time/TheTVDB tratam a série toda como uma única entrada com várias temporadas. O script funde as entradas certas usando o mapeamento comunitário [Fribb/anime-lists](https://github.com/Fribb/anime-lists). Detalhe completo em [docs/mal-import](docs/mal-import/).

### Como correr

```bash
# 1. Exporta a tua lista de anime em https://myanimelist.net/panel.php?go=export
#    (com sessão iniciada) → "Anime List" → sai um .xml ou .xml.gz

# 2. Coloca o ficheiro em private/mal/ (ver private/mal/README.md)

# 3. Corre o script — sem argumentos, encontra sozinho o ficheiro em private/mal/
python3 mal_to_tvtime.py

# 4. Output gerado fica em private/output/
```

## Privacidade

O script corre inteiramente no teu computador — não envia nada para lado nenhum, exceto o download único e público do mapeamento [Fribb/anime-lists](https://github.com/Fribb/anime-lists) (`anime-list-full.json`, dados de terceiros sobre animes, não teus).

Tudo o que é pessoal (o teu export do MAL, os ficheiros gerados) vive em `private/`, que está fora do controlo de versões (ver `.gitignore`) — só os `README.md` de cada subpasta ficam versionados, como guia de onde as coisas vão. Ver [Estrutura do repo](#estrutura-do-repo) abaixo.

## Estrutura do repo

- [`docs/`](docs/) — resultados documentados de cada plano (público, sem dados pessoais)
  - [`docs/research/`](docs/research/) — notas de terceiros, dados de exemplo e o `tvtime_recover.py` (fica junto da narrativa do Plano A que o usa)
- [`mal_to_tvtime.py`](mal_to_tvtime.py) — o script, na raiz
- `private/` — os meus dados pessoais, exports e resultados reais (fora do repo público, ver `.gitignore`)
  - `private/mal/` — exports brutos do MyAnimeList
  - `private/output/` — resultados reais gerados pelos scripts sobre os meus dados

## Minhas tentativas: Planos A–D

Quatro tentativas, por ordem, cada uma documentada com o que foi tentado e por que funcionou ou não.

### Plano A — recuperar via cache do Android sem root

Beco sem saída: `adb backup` está bloqueado para apps de terceiros desde o Android 12, em qualquer telemóvel sem root. Ver [docs/unrooted-android](docs/unrooted-android/).

### Plano B — recuperar via storage do browser

Beco sem saída: mesmo com uma sessão válida guardada localmente, o backend (`api2.tozelabs.com` e `api.tvtime.com`) está completamente desligado. Ver [docs/browser-storage](docs/browser-storage/).

### Plano C — reconstruir a lista de anime a partir do MAL

O MAL continua no ar — em vez de recuperar, reconstruir um ficheiro de importação a partir do que já lá está registado. É o `mal_to_tvtime.py` acima. Ver [docs/mal-import](docs/mal-import/).

### Plano D — voltar a registar tudo de novo

Felizmente não vai ser tudo, porque a maioria dos animes eu já registava sempre no MAL e no TV Time — só me restam filmes e séries.

Espero ter ajudado de algum jeito.

## Licença

[MIT](./LICENSE)
