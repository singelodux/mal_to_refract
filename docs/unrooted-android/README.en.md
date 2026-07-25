# Recovering TV Time app data from an unrooted Android phone (Plan A) — dead end

*[Leia em português](README.md)*

**TL;DR:** We tried to pull TV Time's `DioCache.db` off an unrooted Android phone via `adb backup`. The app's manifest allows backup and `adb` connects fine, but the result is always an empty 47-byte `.ab` file — since Android 12, full `adb backup` for third-party apps is blocked at the OS level on production builds, regardless of the app's own configuration. Without root or a debuggable build, there's no way around it.

Goal: pull TV Time's local cache (`DioCache.db`, under the app's private `Documents/` folder) off an Android phone **without root**, using `adb backup`.

Tested on a Samsung Galaxy S22 (SM-S901E), Android 16, TV Time `com.tozelabs.tvshowtime` v10.11.0. Result: **not possible**, for reasons that apply to any modern (Android 12+) unrooted, non-debuggable app — not specific to this phone or this app.

## 1. Check whether the app even allows backup

Before touching a device, it's worth checking the app's manifest — no phone needed, just the APK:

```bash
# from an .apk or the base.apk extracted from an .apkm/.xapk bundle
aapt dump xmltree base.apk AndroidManifest.xml | grep -A3 'application'
```

Look for `android:allowBackup` (must be `true`/`0xffffffff`, not `0x0`) and `android:fullBackupContent`, which points to an XML resource that can `<exclude>` specific paths from the backup. Resolve it with:

```bash
aapt dump --values resources base.apk | grep -B5 '<the resource id from above>'
aapt dump xmltree base.apk res/xml/<resolved_name>.xml
```

In TV Time's case, `allowBackup="true"` and the only exclusions were an AppsFlyer SDK's own shared prefs/db — the app's own data directory was not excluded. On paper, a full backup should have worked.

## 2. Getting `adb` to see the phone (Linux/Fedora)

If `lsusb` shows the phone (vendor id `04e8` = Samsung) but `adb devices` shows nothing, it's a missing udev rule, not a phone-side problem:

```bash
rpm -q android-udev-rules   # not a real package on Fedora
rpm -ql android-tools | grep rules.d   # android-tools ships adb but no udev rules either
```

Fix, install the community rules:

```bash
sudo curl -L -o /etc/udev/rules.d/51-android.rules \
  https://raw.githubusercontent.com/M0Rf30/android-udev-rules/main/51-android.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Replug the USB cable. `adb devices -l` should now show the device as `unauthorized`; accept the RSA key prompt on the phone's screen, and it flips to `device`.

## 3. Attempting the backup

```bash
adb backup -f tvtime_backup.ab -noapk com.tozelabs.tvshowtime
```

The phone shows a confirmation screen ("Back up my data", optional encryption password). Confirmed it every time — and the resulting `.ab` file was still a fixed **47-byte stub** (just the archive header, no payload), every single time.

## 4. Why: `adb backup` is dead for third-party apps since Android 12

This isn't a misconfiguration. Starting with Android 12, full-data backup via `adb backup` for third-party apps was locked down at the framework level on production ("user") builds — the confirmation dialog still shows for compatibility, but the actual data copy is refused regardless of the app's `allowBackup` manifest flag. It only ever worked on `userdebug`/`eng` builds or rooted devices. No consumer phone ships a `userdebug` build, so this path is closed on any unrooted phone running Android 12+.

Two things that would bypass this, checked and ruled out here:

- **`run-as <package>`** (works without root if the app is `android:debuggable`) — TV Time's release build is not debuggable, so this is a dead end too.
- **Root** (Magisk etc.) would give direct filesystem access to `/data/data/<package>/`, which *would* work — but rooting a daily-driver phone is a separate, much bigger decision (voids warranty, bootloop risk, security exposure) and out of scope for a "no root" recovery attempt.

## Conclusion

On an unrooted phone running Android 12+, there is no way to extract another app's private storage via `adb backup`, no matter how the target app's manifest is configured. If you're trying this for your own app-recovery project: check the Android version first — if it's 12+ and the phone isn't rooted, don't bother with `adb backup` at all, it will pass every check and still fail silently.
