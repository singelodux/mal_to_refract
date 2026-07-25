# Recuperar dados do TV Time via storage do browser (Plano B) — beco sem saída

*[Read in English](README.en.md)*

**TL;DR:** Tentámos recuperar o histórico do TV Time a partir do que o browser guardou localmente (Cache Storage, IndexedDB, Local Storage). Encontrámos um token de sessão real e válido e o perfil completo da conta em Local Storage — mais do que se esperava. Mesmo assim, é um beco sem saída: os dois hosts de API conhecidos (`api2.tozelabs.com` e `api.tvtime.com`) estão ambos mortos, cada um de forma diferente, e nenhum responde a pedidos de dados, com token ou sem ele.

Objetivo: em vez do telemóvel, tentar recuperar o histórico a partir do que o **browser** guardou localmente da web app (`https://app.tvtime.com/`) — Cache Storage, IndexedDB e Local Storage — já que uma screenshot do DevTools mostrava ~20.5MB de dados guardados ali, apesar da watchlist aparecer vazia com "a network error occurred".

Testado no Brave (Chromium). Resultado: **há dados reais da conta em cache localmente, mas são inúteis** — o backend não está no ar para os aceitar, mesmo com uma sessão válida e não expirada.

## 1. Localizar o storage por origem, sem abrir o DevTools

Cada tipo de storage do Chromium vive num sítio próprio no perfil, e nem todos indexam pelo nome do site de forma óbvia:

- **IndexedDB** — uma pasta por origem, fácil de encontrar:

  ```bash
  find ~/.config/BraveSoftware/Brave-Browser -iname "*tvtime*"
  # .../Default/IndexedDB/https_app.tvtime.com_0.indexeddb.leveldb
  ```

- **Cache Storage** (usado por service workers) — pastas com nome em hash, sem relação óbvia com a origem. A origem real está em texto simples dentro do `index.txt` de cada pasta:

  ```bash
  CS=~/.config/BraveSoftware/Brave-Browser/Default/"Service Worker"/CacheStorage
  grep -a -rl "tvtime" "$CS"/*/index.txt
  ```

- **Local Storage** — **um único leveldb partilhado por todas as origens do perfil inteiro**, não uma pasta por site. Uma pesquisa de texto aqui pode facilmente atribuir um valor ao site errado (aconteceu neste projeto: um JWT de um serviço completamente diferente foi confundido com um token do TV Time só por estar próximo no ficheiro). Para atribuição correta por chave é preciso um parser leveldb próprio (ex: `plyvel` em Python), não `strings`/`grep`.

## 2. O que estava lá, por tipo

- **Cache Storage**: só `flutter-app-manifest` e `flutter-app-cache` — a web app é uma PWA em Flutter, e isto é só o "app shell" (JS/assets estáticos para funcionar offline), não dados de conta.
- **IndexedDB**: sobretudo cache do Firebase Remote Config (feature flags tipo `age_gating`, `auth_providers`) e tokens — mas, decodificando os JWTs corretamente (payload em base64, não achismo por proximidade de texto), são tokens **internos do Firebase** (Installations / Auth do Google), usados só para telemetria/config, não um token de sessão da API do TV Time.
- **Local Storage**: nada atribuível ao TV Time com confiança na primeira passagem (ver aviso acima sobre o leveldb partilhado) — **mas isto mudou** depois de a app conseguir autenticar numa visita seguinte (ver secção 3).

### Aviso: ler o leveldb em disco enquanto o browser está aberto pode mentir

Na primeira tentativa, uma leitura direta dos ficheiros do leveldb não encontrou nenhuma chave `flutter.jwtToken` / `flutter.isLoggedIn`. Pouco depois, com o DevTools aberto ao vivo na mesma sessão, essas chaves apareciam claramente no painel **Application → Local Storage**. A causa: o Chromium mantém escritas recentes em memória antes de as sincronizar para disco, e ler os ficheiros por fora enquanto o browser está a correr pode apanhar um estado desatualizado. **Se o browser estiver aberto, confia no DevTools, não numa leitura de ficheiro por fora.** Para capturar o estado atual de forma fiável sem essa corrida, usa a consola do próprio DevTools:

```js
copy(JSON.stringify(Object.fromEntries(Object.entries(localStorage)), null, 2))
```

Isto corre só no browser, não envia nada para lado nenhum, e dá-te o `localStorage` exato daquele momento para colares num ficheiro.

## 3. O que apareceu depois de autenticar com sucesso

Assim que a app conseguiu autenticar (`flutter.isLoggedIn: "true"`), o `localStorage` continha, entre outras chaves com o prefixo `flutter.`:

- `flutter.jwtToken` / `flutter.jwtRefreshToken` — tokens de sessão reais, assinados pela própria TV Time (`iss`/`aud`: `http://www.tvtime.com`), não tokens genéricos de terceiros.
- `flutter.user` — um JSON com o perfil completo da conta: nome, email, fuso-horário, data de criação da conta, e contadores como `followed_show_count`, `for_later_show_count`, `stats.time_spent`, `stats.nb_likes`.
- Vários `flutter.*_last_action_time` — timestamps de última atividade por categoria (séries, filmes, comentários, etc.).
- `flutter.seriesToSkipWatchPreviousEpisodes` — uma lista de IDs de séries.

Isto contraria a conclusão inicial: a app web **guarda**, sim, um resumo útil da conta localmente uma vez autenticada — só não guarda o histórico completo episódio-a-episódio como o `DioCache.db` da app nativa.

## 4. Descobrir o host da API real (a partir do bundle da app)

Vale a pena confirmar se o backend ainda está no ar, com ou sem token. O host da API não está em lado nenhum óbvio — mas aparece em texto simples dentro dos próprios ficheiros JS/wasm que o service worker guardou em cache:

```bash
CS=~/.config/BraveSoftware/Brave-Browser/Default/"Service Worker"/CacheStorage/<hash-encontrado-no-passo-1>/<subpasta-da-cache>
strings -n 8 "$CS"/*_0 | grep -oE "https?://[a-zA-Z0-9._-]*tozelabs[a-zA-Z0-9._/-]*"
# -> https://api2.tozelabs.com/v2
```

## 5. Testar se o backend ainda responde

```bash
curl -v --max-time 10 https://api2.tozelabs.com/v2
```

Resultado: o DNS resolve normalmente, mas a ligação na porta 443 falha ("no route to host") — o servidor da API está mesmo desligado, não é só um erro de autenticação. Em contraste, o frontend estático continua a responder:

```bash
curl -o /dev/null -w "%{http_code}\n" https://app.tvtime.com/
# -> 200
```

Isto explica o "network error" na screenshot: a página (frontend estático, provavelmente ainda servida por um CDN) carrega normalmente, mas não há nenhum servidor do outro lado para responder aos pedidos de dados.

## 6. Mesmo com um token válido, o outro host também está morto

O JWT (secção 3) tem `iss`/`aud` a apontar para `www.tvtime.com`, um host diferente de `api2.tozelabs.com`. Vale a pena testar esse também antes de desistir — e ele responde, ao contrário do outro:

```bash
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 8 https://api.tvtime.com/v2/user/me
# -> HTTP 404
```

Um 404 podia ser só o endpoint errado. Mas os headers da resposta contam outra história:

```bash
curl -s -D - --max-time 8 https://api.tvtime.com/v2/user/me
# HTTP/2 404
# server: awselb/2.0
# content-length: 0
```

`server: awselb/2.0` é um Elastic Load Balancer da AWS a responder sozinho, com corpo vazio — sinal de que o balanceador ainda existe (o DNS aponta para ele, a infraestrutura não foi totalmente desligada), mas **não há nenhum servidor de aplicação registado atrás dele** para processar o pedido, seja qual for o endpoint ou o token usado. Testar vários caminhos (`/v2/user/{id}`, `/follows`, `/followed-shows`, etc.) com um `Authorization: Bearer <jwtToken>` real e ainda válido deu sempre o mesmo 404 vazio — não é um problema de autenticação, é a ausência total de aplicação por trás do load balancer.

## Conclusão

Encontrámos um token de sessão real e válido, e o perfil completo da conta guardado localmente — mais do que se esperava a meio desta investigação. Mas isso não chega: as duas infraestruturas de API conhecidas (`api2.tozelabs.com` e `api.tvtime.com`) estão ambas mortas, cada uma de forma diferente (uma recusa a ligação, a outra responde vazia a partir de um load balancer sem destino). Não há como recuperar dados de conta pela via do browser, por mais válido que o token seja.

Se procuras algo assim para o teu próprio projeto: confirma sempre se o *backend* (não só o frontend, e não só "o DNS resolve") ainda responde com um servidor de aplicação real por trás — um 404 vazio de um load balancer da AWS não é o mesmo que um 404 de uma API a funcionar, e nenhum dos dois significa que vale a pena insistir com um token.
