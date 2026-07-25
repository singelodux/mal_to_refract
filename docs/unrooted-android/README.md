# Recuperar dados da app TV Time num Android sem root (Plano A) — beco sem saída

*[Read in English](README.en.md)*

**TL;DR:** Tentámos extrair o `DioCache.db` do TV Time de um Android sem root via `adb backup`. O manifesto da app permite backup e o `adb` liga-se sem problemas, mas o resultado é sempre um `.ab` de 47 bytes vazio — desde o Android 12, o `adb backup` completo para apps de terceiros está bloqueado ao nível do sistema em builds de produção, independentemente da configuração da app. Sem root ou build `debuggable`, não há forma de contornar isto.

Objetivo: extrair a cache local do TV Time (`DioCache.db`, dentro da pasta privada `Documents/` da app) de um telemóvel Android **sem root**, usando `adb backup`.

Testado num Samsung Galaxy S22 (SM-S901E), Android 16, TV Time `com.tozelabs.tvshowtime` v10.11.0. Resultado: **não é possível**, por razões que se aplicam a qualquer app não-debuggable num Android 12+ sem root — não é específico deste telemóvel nem desta app.

## 1. Verificar se a app sequer permite backup

Antes de mexer no telemóvel, vale a pena verificar o manifesto da app — não precisa de telemóvel nenhum, só do APK:

```bash
# a partir de um .apk, ou do base.apk extraído de um bundle .apkm/.xapk
aapt dump xmltree base.apk AndroidManifest.xml | grep -A3 'application'
```

Procurar por `android:allowBackup` (tem de ser `true`/`0xffffffff`, não `0x0`) e por `android:fullBackupContent`, que aponta para um recurso XML que pode `<exclude>` caminhos específicos do backup. Resolve-se assim:

```bash
aapt dump --values resources base.apk | grep -B5 '<id do recurso obtido acima>'
aapt dump xmltree base.apk res/xml/<nome_resolvido>.xml
```

No caso do TV Time, `allowBackup="true"` e as únicas exclusões eram dados próprios do SDK da AppsFlyer (shared prefs/db) — a pasta de dados da própria app não estava excluída. No papel, um backup completo devia ter funcionado.

## 2. Fazer o `adb` reconhecer o telemóvel (Linux/Fedora)

Se o `lsusb` mostra o telemóvel (vendor id `04e8` = Samsung) mas o `adb devices` não mostra nada, é uma regra de udev em falta, não um problema do telemóvel:

```bash
rpm -q android-udev-rules   # não existe como pacote no Fedora
rpm -ql android-tools | grep rules.d   # android-tools traz o adb mas nenhuma regra de udev
```

Correção, instalar as regras da comunidade:

```bash
sudo curl -L -o /etc/udev/rules.d/51-android.rules \
  https://raw.githubusercontent.com/M0Rf30/android-udev-rules/main/51-android.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Voltar a ligar o cabo USB. O `adb devices -l` deve agora mostrar o aparelho como `unauthorized`; aceitar o pedido da chave RSA no ecrã do telemóvel, e passa a `device`.

## 3. Tentativa de backup

```bash
adb backup -f tvtime_backup.ab -noapk com.tozelabs.tvshowtime
```

O telemóvel mostra um ecrã de confirmação ("Fazer backup dos meus dados", com password de encriptação opcional). Confirmado todas as vezes — e o ficheiro `.ab` resultante ficou sempre com um tamanho fixo de **47 bytes** (só o cabeçalho do arquivo, sem dados nenhuns), sempre.

## 4. Porquê: o `adb backup` está morto para apps de terceiros desde o Android 12

Isto não é uma má configuração. A partir do Android 12, o backup completo via `adb backup` para apps de terceiros foi bloqueado ao nível do framework em builds de produção ("user") — o ecrã de confirmação continua a aparecer por compatibilidade, mas a cópia de dados em si é recusada, independentemente da flag `allowBackup` do manifesto da app. Só funcionava mesmo em builds `userdebug`/`eng` ou em telemóveis rooted. Nenhum telemóvel de consumo vem com build `userdebug`, por isso este caminho está fechado em qualquer telemóvel sem root a correr Android 12+.

Duas alternativas que contornariam isto, verificadas e descartadas aqui:

- **`run-as <package>`** (funciona sem root se a app for `android:debuggable`) — o build de produção do TV Time não é debuggable, portanto também é um beco sem saída.
- **Root** (Magisk, etc.) daria acesso direto ao sistema de ficheiros em `/data/data/<package>/`, o que *funcionaria* — mas fazer root a um telemóvel do dia a dia é uma decisão à parte, bem maior (perde garantia, risco de bootloop, exposição de segurança), fora do âmbito de uma tentativa de recuperação "sem root".

## Conclusão

Num telemóvel sem root a correr Android 12+, não há forma de extrair o armazenamento privado de outra app via `adb backup`, seja qual for a configuração do manifesto da app alvo. Se estiveres a tentar isto para o teu próprio projeto de recuperação de dados: verifica primeiro a versão do Android — se for 12+ e o telemóvel não tiver root, nem vale a pena tentar o `adb backup`, vai passar em todas as verificações e mesmo assim falhar silenciosamente.
