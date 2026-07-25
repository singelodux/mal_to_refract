# Recursos (fontes de terceiros)

Recolha organizada do que a comunidade partilhou sobre o encerramento do TV Time — Reddit, gists, o Discord do Refract. Isto é matéria-prima; as conclusões e testes próprios deste projeto estão em [`../`](../) (Planos A/B/C).

## Recuperar o cache nativo da app (`DioCache.db`)

A app guarda as respostas da API num cache HTTP local, `DioCache.db`. O desafio é sempre o mesmo: tirar esse ficheiro do telemóvel.

**Android** — depende muito do fabricante:

- Xiaomi: `Definições → Sobre o telefone → Cópia de segurança e restauro`, criar um backup; dentro do zip está um `TV Time(com.tozelabs.tvshowtime).bak`.
- Pixel e Samsung: provavelmente não é possível tirar um backup não encriptado (confirmado neste projeto para Android 12+, ver [../unrooted-android](../unrooted-android/) — não é só "provavelmente", está mesmo bloqueado ao nível do sistema).
- Com root: o ficheiro está em `/storage/emulated/0/Android/data/com.tozelabs.tvshowtime/`.
- Sem root, em versões mais antigas: Shizuku + Solid Explorer pode funcionar.
- Ferramenta de referência: [tvtime_recover (ajoemag)](https://ajoemag.github.io/tvtime_recover/)

**iOS** (testado pela comunidade, não neste projeto — ver [thread original](https://www.reddit.com/r/TVTime/comments/1v46tkm/how_to_recover_your_tv_time_data_using_imazing/)):

1. Desliga a rede (modo avião), abre a app, `Perfil → Favorite shows → Add favorite shows` — mostra a lista completa de séries seguidas (incluindo "not started"/"watch later"), mas não os episódios vistos.
2. Alternativa não confirmada: abrir `tvst://profile/favorite_shows` no Safari em modo avião.
3. Para recuperar mais do que a lista de séries (via backup do iPhone num Mac):
   - Ligar o iPhone ao Mac, criar um backup não encriptado (app Ficheiros → `[Geral]`).
   - Abrir esse backup no [iMazing](https://imazing.com/), ir a `Data → File System → Apps → TVTime → Documents`, e copiar o `DioCache.db` (o maior ficheiro da pasta) para o Mac.
   - Correr o `tvtime_recover.py` deste repo sobre esse ficheiro (o script aqui é uma versão própria, reescrita para ser mais completa que o [script original citado pela comunidade](https://gist.github.com/xjki/1ed43f7f12ee29bd34f5e6805ac6e93a), partilhado nesta [thread](https://www.reddit.com/r/TVTime/comments/1v0tzgl/tvtime_data_recovery_script_from_iphone_app_using/)).
   - Ver também: [tvtime-cache-parser](https://github.com/ssjsamir/tvtime-cache-parser), outra tentativa da comunidade de fazer o mesmo parsing, discutida [aqui](https://www.reddit.com/r/TVTime/comments/1v2h5v8/is_there_anyway_to_import_the_diocachedb_to/).

## Antes do encerramento: truque para marcar filmes na web app

A pesquisa na app parou de funcionar antes do encerramento oficial. Havia uma forma de marcar filmes na mesma ([thread original](https://www.reddit.com/r/TVTime/comments/1ux5qv8/track_movies_you_watched_on_tv_time_in_the_past/)), navegando diretamente para a página do filme pelo ID do TheTVDB:

```text
https://app.tvtime.com/movie/<tvdb-id>
```

O `<tvdb-id>` encontra-se pesquisando o filme em thetvdb.com (aparece como "Movie #12345" junto ao ano). Só funciona autenticado no browser.

## Comportamento do import no Refract (relatos da comunidade)

- No início, o Refract só aceitava ficheiros **JSON**, não os `.csv` que o export GDPR do TV Time realmente produz — utilizadores tinham de passar primeiro pelo Trakt (que aceita o GDPR diretamente) e só depois exportar do Trakt para o Refract. Os devs confirmaram estar a trabalhar para aceitar o ficheiro GDPR diretamente, sem ETA.
- Importar de múltiplas fontes faz *merge*, não duplica: um utilizador perguntou o que acontece ao importar TV Time e depois IMDb com sobreposição de séries/filmes — confirmado pelos moderadores que os registos se fundem; só há substituição ao importar duas vezes **da mesma fonte**.
- Durante o pico de migração pós-encerramento do TV Time, o Refract teve filas de import lentas/travadas por sobrecarga nos servidores — segundo o próprio anúncio da equipa, temporário e não indicava perda de dados.

## Comparação de alternativas

Levantamento informal (não testes próprios) feito enquanto se decidia para onde migrar.

| App | Comunidade? | Comentários? | Estabilidade | Risco de desaparecer |
| --- | --- | --- | --- | --- |
| **Simkl** | Sim, ativa, crescente | Comentários por episódio/filme | Projeto maduro (anos) | Baixo (modelo híbrido) |
| **Trakt.tv** | Gigantesca, mais "séria" | Tem, mas menos "meme" | Muito estável (>10 anos) | Baixo (consolidado) |
| **Sofatime** | Promete, só iOS e Web | Não lançou Android ainda | Muito jovem | Alto (pode desaparecer) |
| **Bingers** | Lançamento previsto | Desconhecido | Feito pelo mesmo fundador do TV Time | Muito alto (mesmo padrão de abandono) |
| **Refract** | Migração em massa, app novo | Poucos ainda | Recente, sem histórico | Médio |

Comparação mais aprofundada entre os três finalistas, por critério:

- **Comunidade/comentários**: Simkl tinha a vibe mais próxima do TV Time (comentários por episódio, comunidade a crescer com refugiados do TV Time); Trakt é gigante mas mais "sério"/menos caótico; Refract ainda tinha poucos comentários por ser recente.
- **Estabilidade**: Trakt (>10 anos) e Simkl (também antigo, modelo híbrido grátis+pago) sem histórico de abandono; Refract é o mais recente e sem histórico — maior risco, mas também maior margem para evoluir depressa.
- **App/interface**: Simkl tem app nativo Android moderno; o app oficial do Trakt é datado (a comunidade recomenda clientes terceiros como SeriesGuide/CineTrak); Refract tem visual elogiado mas ainda em desenvolvimento ativo (funcionalidades em falta).
- **Cobertura de conteúdo**: Trakt trata anime como séries normais (numeração por temporada da TMDB); Simkl trata anime como categoria própria, com datas de estreia no Japão; Refract cobre filmes/séries/anime igualmente e promete adicionar livros e jogos no futuro.
- **Automação**: Trakt tem scrobbling automático via Plex/Kodi/Stremio (destaque forte se usas algum media server); Simkl faz scrobble via extensão de browser (Netflix/Crunchyroll/Hulu); Refract é manual — sem scrobbling automático por agora.

## Comentários reais de emigrantes do TV Time (Play Store)

Amostra de reviews de utilizadores vindos do TV Time, recolhidos nas páginas de cada app na Play Store — sinal direto da experiência de migração de quem já passou por isso.

**Trakt** ("TV Time To Watch"):

- "Vim do TV Time e fui obrigado a assinar para transferir os dados, a interface do app é muito poluída [...] o maior problema do app é realmente a praticidade pra usar."
- "This app almost imported all my data from Tive Time, I just have to check a few shows and movies, so far I am satisfied using this one."
- "Horrível e confuso! no TV TIME tinha como marcar todos os episódios anteriores de uma vez, nesse tem que marcar um por um."
- "Migrei pro Trakt depois do triste anúncio do Tv time [...] consegui exportar todos os meus dados de filmes e séries bem tranquilo [...] diria que até melhor que o Tv time em alguns aspectos [...] 10/10."
- "Então é aqui que os viúvos(a) do TV time estão se reunindo?"

**Simkl** ("Simkl Lists: TV, Anime, Movies"):

- "salvou minha vida pós o fim do tvtime. importou tudo rapidamente [...] mas o simkl poderia imitar algumas coisinhas do tvtime pra pegar o público viúvo. algo muito legal do tvtime era a comunidade [...] os comentários dos episódios."
- "Baixei para ser substituto do finado tvtime... mas a função de importação dos dados do tvtime tem que pagar... vou tentar outro."
- "We've run out of capacity and had to disable the free imports. Our datacenters are actively looking for the needed hardware, due to RAM/NVME shortages and 4X prices as well as holidays." (resposta oficial da Simkl a um utilizador, sobre limites de import gratuito)
- "não dá para trocar para português - Sorry, only English is currently supported."

**Refract** ("Refract: Filmes, TV e Anime"):

- "testei vários apps pra substituir o tv time, e esse foi o que mais me agradou [...] app muito bom."
- "Achei o app bem bonito e fácil de usar, porém a minha importação do tv time está na fila há uma semana e não sai do lugar... Desisti de tentar usar."
- "gostei da ambientação do app, o problema é [...] a importação dos dados está praticamente parada em uma fila gigantesca!! [...] Edit: Alguns dias depois [...] o app melhorou muito. Tá bem mais estável, e minhas importações já foram partes [...] acho que o app tem muito potencial."
- "A equipe de desenvolvimento é bastante ativa e receptiva com os feedbacks da comunidade. A infraestrutura escalou para acomodar todos os usuários que estão migrando do TVTime."

Padrão comum aos três: filas/lentidão de import durante o pico de migração logo a seguir ao encerramento do TV Time — não parece ser sinal de perda de dados, mas sim de sobrecarga temporária nos servidores de quem recebeu a vaga de utilizadores de uma vez.

## Modelo de email de pedido de dados (GDPR)

Rascunho usado para pedir os dados diretamente à Whip Media, depois do portal de autoatendimento (`gdpr.tvtime.com`) ter ficado com DNS morto. Enviar para `support@whipmedia.freshdesk.com` e `support@tvtime.com`; recomenda-se a versão em inglês, por serem uma empresa dos EUA.

**Assunto:** `GDPR Data Access Request - User [SEU_USERNAME]`

> Dear Whip Media Team,
>
> I have been a loyal TV Time user for years. I was caught off guard by the abrupt shutdown of the app. The self-service GDPR portal (`gdpr.tvtime.com`) is already offline, making it impossible for me to retrieve my data.
>
> Under **Article 15 of the GDPR**, I formally request a full export of all my personal data associated with my account, including:
>
> - Full watch history (with timestamps)
> - Ratings and reviews
> - Custom lists
> - Comments and social interactions
>
> My registered email is: [YOUR EMAIL]
> My username is: [YOUR USERNAME]
>
> Please send the data in a machine-readable format (CSV/JSON) within the maximum 30-day deadline required by law.
>
> Sincerely,
> [YOUR FULL NAME]

Nota realista: a chance de resposta é baixa, sobretudo depois de a empresa desmantelar a infraestrutura técnica (ver [docs/browser-storage](../browser-storage/) para a evidência disso) — mas não custa nada tentar, e legalmente têm até 30 dias para responder.

## Ver também

Outras threads do r/TVTime relacionadas, guardadas mas ainda por resumir aqui:

- [Your TV Time watch history is safe, but your...](https://www.reddit.com/r/TVTime/comments/1v2y3kc/your_tv_time_watch_history_is_safe_but_your/)
- ["No, no, no"](https://www.reddit.com/r/TVTime/comments/1uycbh4/no_no_no/)
- ["Had no idea"](https://www.reddit.com/r/TVTime/comments/1v0xdbj/had_no_idea/)
