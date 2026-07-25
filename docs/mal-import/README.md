# Converter a lista de anime do MyAnimeList para o formato do TV Time (Plano C)

*[Read in English](README.en.md)*

Com os Planos A e B esgotados ([docs/unrooted-android](../unrooted-android/), [docs/browser-storage](../browser-storage/)), não encontrámos forma de recuperar o histórico completo do TV Time por essas vias — o que não significa que seja impossível, só que estes dois caminhos bateram num beco sem saída. O MyAnimeList (MAL), ao contrário do TV Time, continua no ar e tem um export oficial — por isso o Plano C muda de "recuperar" para "reconstruir": usar o que já está registado no MAL para gerar um ficheiro de importação de anime para a app seguinte.

**Testado e confirmado a funcionar** contra o import "TV Time" real do [Refract](https://getrefract.app/): 52 filmes + 237 séries aceites sem erro, na primeira tentativa com o schema correto (ver secção 5).

## 1. O problema: o app seguinte não importa do MAL diretamente

O app de destino testado aqui (Refract) só importa de 4 fontes: **Letterboxd, TV Time, IMDb e Trakt (backup ZIP)**. Nenhuma delas é o MAL. As opções e porque foram descartadas:

- **Letterboxd**: CSV bem documentado publicamente, mas é só filmes — sem conceito de séries/episódios, mal servido para anime.
- **IMDb**: CSV bem documentado, mas cada linha precisa do ID do IMDb (`tconst`) por título — implicaria mapear cada anime do MAL para o IMDb.
- **Trakt (ZIP)**: só o próprio Trakt gera este ficheiro a partir de uma conta real; a alternativa seria escrever os dados lá via API e depois exportar — mais trabalho (conta, API app, matching título→Trakt).
- **TV Time**: escolhida aqui — e não pelo caminho que se esperava.

## 2. A reviravolta: o import "TV Time" do Refract não é o que parecia

A ideia inicial era fabricar um ficheiro no vocabulário de campos que a API do TV Time usava (reaproveitando o que já se tinha percebido em `tvtime_recover.py`, Plano A). Ao abrir o ecrã de import do Refract, percebeu-se que isso estava errado em dois pontos:

1. O import "TV Time" não aceita um único ficheiro à nossa maneira — espera até **três ficheiros com nomes fixos**: `tvtime-movies-YYYY-MM-DD.json`, `tvtime-series-YYYY-MM-DD.json` e `tvtime-lists-YYYY-MM-DD.json` (opcional), o mesmo que a extensão Chrome oficial "Refract's TV Time Out" produz quando o TV Time ainda estava no ar.
2. Isso não bloqueia quem já perdeu o acesso: a app aceita os ficheiros carregados diretamente, não exige que sejam gerados pela extensão em tempo real — só têm de ter a **forma** certa.

Encontrámos essa forma exata através de um conversor open-source já existente para este problema: [jeremy-albinet/tvtime-to-refract-converter](https://github.com/jeremy-albinet/tvtime-to-refract-converter), cujo `src/core/model.js` documenta o schema canónico ("TV Time Liberator") e `src/core/parse-gdpr.js` mostra exatamente como o export GDPR real do TV Time preenche cada campo — incluindo os que ficam `null` mesmo em dados genuínos (o nome de cada episódio e o `id.tvdb` por episódio não vêm no export GDPR oficial; não é uma lacuna nossa, é assim mesmo com dados reais).

Schema (por show):

```json
{
  "uuid": null,
  "id": { "tvdb": 306269, "imdb": "tt6074794" },
  "created_at": null,
  "title": "3-gatsu no Lion",
  "status": "followed",
  "is_favorite": false,
  "seasons": [{
    "number": 1,
    "is_specials": false,
    "episodes": [{
      "id": { "tvdb": null, "imdb": null },
      "number": 1, "name": null, "special": false,
      "is_watched": true, "watched_at": "2018-08-31 00:00:00",
      "rewatch_count": 0, "watched_count": 1
    }]
  }]
}
```

`status` só tem dois valores reais no export do TV Time — `"followed"` ou `"archived"` — nada de "watching"/"completed"/"plan to watch" ao nível do show; isso é inteiramente derivado do `is_watched`/`watched_at` por episódio.

## 3. O problema da temporada: MAL e TVDB contam de forma diferente

O MAL dá a cada temporada de um anime o seu próprio id e a sua própria entrada — "Attack on Titan", "Attack on Titan Season 2", "Attack on Titan Season 3 Part 1" são três `mal_id` diferentes, cada um com a sua contagem de episódios. O TV Time (tal como o TheTVDB, em que se baseia) trata a série inteira como **uma** entrada com várias temporadas numeradas. Converter id-a-id dava-te três "séries" desligadas em vez de uma com três temporadas.

A solução: o mapeamento comunitário [Fribb/anime-lists](https://github.com/Fribb/anime-lists) (`anime-list-full.json`) associa cada `mal_id` a um `tvdb_id` (e, por vezes, `imdb_id`) mais o número real da temporada na TVDB:

```json
{ "mal_id": 397, "tvdb_id": 72025, "imdb_id": ["tt0286390"], "season": { "tvdb": 3 } }
```

Com isto, agrupamos por `tvdb_id` e fundimos as várias entradas do MAL numa só série, com episódios `SxxEyy` construídos a partir do número real da temporada — não uma sequência às cegas.

Cobertura: nem tudo tem `tvdb_id` — filmes, OVAs e specials normalmente não estão na TVDB (é uma base de dados de séries de TV). Esses ficam com `id.tvdb: null` (nunca com o id do MAL disfarçado de id da TVDB — isso enganaria um parser real a associar à série errada). Séries do tipo `Movie` no MAL são emitidas como filme, não como série de um episódio só — usando o `imdb_id` do mapeamento quando existe, já que a TVDB cobre mal filmes de anime.

## 4. Porquê alguns títulos ficam "não encontrados" no Refract

O import do Refract reporta quantas entradas não conseguiu casar com o catálogo dele. A hipótese óbvia seria o mesmo problema de contagem temporada-a-temporada da secção 3 — mas isso não se sustenta: o script já funde multi-temporada corretamente antes de o ficheiro sair de cá. Comparando o `anime-list-full.json` com o que o script gera, há **duas causas sobrepostas**, distintas desse problema:

**a) O script descartava `tvdb_id` bons sem necessidade.** O código original só aceitava o `tvdb_id` de uma entrada se o mapeamento também trouxesse `season.tvdb` explícito — senão, descartava os dois. Mas o Fribb só marca `season.tvdb` quando o `mal_id` corresponde a uma temporada **diferente** da primeira: "One Piece", "Pokemon", "Hunter x Hunter (2011)", "Bleach" e outras séries longas têm dezenas de `mal_id` de filmes/specials/arcos posteriores com `season` explícito (2, 6, 14, ou 0 para specials) — mas a entrada **original** de cada uma, que É a temporada 1, não tem campo `season` nenhum. Verificado contra o dataset inteiro: nenhum `tvdb_id` tem ao mesmo tempo uma entrada sem `season` e outra explicitamente em `season 1` — logo, faltar `season` ao lado de um `tvdb_id` presente significa sempre "isto é a temporada 1", nunca ambiguidade real. A regra antiga estava a apagar ids corretos e inequívocos de séries bem conhecidas só por excesso de cautela.

  Corrigido: se `tvdb_id` existe, é sempre mantido, com `season` a assumir `1` quando ausente (ver comentário em `ensure_mapping()` no script).

**b) A parte que não dá para corrigir por aqui: o fallback por título do Refract.** Nos testes feitos aqui, mesmo depois do fix, séries como `Bleach` e `Naruto` já eram encontradas com sucesso apesar de ficarem sem `tvdb_id` (o Refract caiu para um fallback por título e acertou) — enquanto outras na mesma situação exata, como `One Piece`, `Pokemon` e `Hunter x Hunter (2011)`, ficaram descartadas como "não encontradas". O padrão mais provável nos casos que falham: sufixos que só existem no MAL para desambiguar remakes (`Hunter x Hunter (2011)`, `Fairy Tail (2014)`, `Suzumiya Haruhi no Yuuutsu (2009)`) não batem com o título oficial sem o ano; e apareceu pelo menos um caso (`Initial D Third Stage`, um filme) com **os dois ids preenchidos** e mesmo assim não encontrado — sinal de que, para filmes, o Refract pode nem usar o campo `tvdb` (a TVDB não é uma base de filmes fiável). Isto acontece do lado do Refract, fora do nosso controlo — o fix acima só garante que não estamos a jogar fora informação boa antes de lá chegar. Quantos títulos ficam "não encontrados" no teu caso depende inteiramente da tua lista — os nomes acima são só exemplos que apareceram durante os testes, não uma lista fixa.

## 5. Como correr

```bash
# 1. Exportar do MAL: https://myanimelist.net/panel.php?go=export
#    (com sessão iniciada) → "Anime List" → sai um .xml ou .xml.gz
#    Coloca o ficheiro em private/mal/ (ver private/mal/README.md)

python3 mal_to_refract.py
# escreve private/output/tvtime-series-<hoje>.json e tvtime-movies-<hoje>.json
```

O mapeamento `anime-list-full.json` (~7.5MB) é descarregado automaticamente para junto do script na primeira execução — não o guardes num repo público, é só cache e fica desatualizado.

Resultado de um teste real: **360 entradas do MAL → 237 séries + 52 filmes** (157 séries fundidas em shows reais da TVDB, 80 mantidas sem `tvdb_id`). Carregado no Refract (Import do TV Time, Passo 2) sem qualquer erro de formato — os dois ficheiros ficaram prontos a importar de imediato.

## Conclusão

O script (`mal_to_refract.py`) está pronto a partilhar, e o formato que produz está **confirmado** contra o import real do Refract, não é só uma reconstrução informada. Resolve o problema de normalização temporada-a-temporada corretamente, separa filmes de séries como o TV Time faz, e é reaproveitável para qualquer combinação MAL → TV Time Liberator.
