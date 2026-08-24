# CBRE Break – F-Droid Integration Handoff

**Datum:** 2026-08-24  
**Status:** Build blockiert durch RAM-Mangel, Fortsetzung auf anderem Rechner erforderlich

---

## Was bereits erledigt ist

### 1. Projektdateien vorbereitet
- ✅ `LICENSE` – GPL-3.0 Lizenztext hinzugefügt
- ✅ `requirements.txt` – `flet==0.86.5`
- ✅ `.gitignore` – Runtime-Dateien, Build-Artefakte, IDE ausgeschlossen
- ✅ `DOCUMENTATION.md` – F-Droid-Integration dokumentiert (Version 0.4.0)
- ✅ `main.py` – "Made by M.M" Footer hinzugefügt

### 2. Build-Umgebung eingerichtet
- ✅ Flet-CLI installiert: `flet-cli==0.86.5` (via `pip install --break-system-packages`)
- ✅ Flutter SDK: `/home/dosenkohl/flutter/3.44.8` (Channel stable 3.44.8)
- ✅ Java JDK 17: `/home/dosenkohl/java/17.0.13+11/bin/java`
- ✅ Android SDK: `/home/dosenkohl/Android/sdk`
  - Platform 36 installiert
  - Build-Tools 36.0.0 installiert
  - Build-Tools 35.0.0 installiert (für Gradle-Kompatibilität)
  - NDK 28.2.13676358 installiert
  - Lizenzen akzeptiert
- ✅ Bundle-ID korrigiert: `de.cbre.breakapp` (ursprünglich `de.cbre.break` war ein Java-Keyword)

### 3. Build-Konfiguration angepasst
- `build/flutter/android/gradle.properties`:
  ```properties
  org.gradle.jvmargs=-Xmx1G -XX:MaxMetaspaceSize=256m -XX:ReservedCodeCacheSize=128m -XX:+HeapDumpOnOutOfMemoryError
  ```
- Build-Befehl (final, getestet):
  ```bash
  export GRADLE_OPTS="-Xmx512m -XX:MaxMetaspaceSize=128m -XX:ReservedCodeCacheSize=64m -Dorg.gradle.daemon=false"
  flet build apk --yes \
    --bundle-id de.cbre.breakapp \
    --product "CBRE Break" \
    --build-version 1.0 \
    --build-number 1 \
    --org de.cbre \
    --project CBRE_BREAK .
  ```

---

## Aktuelles Problem

### RAM-Mangel
- **Verfügbarer RAM:** 3,4 GiB
- **Benötigt für erfolgreichen Build:** ≥6–8 GiB
- **Symptome:**
  - Gradle Daemon stürzt ab mit `OutOfMemoryError: Metaspace`
  - Build hängt in der Kotlin-Kompilierung
  - System wird instabil (RAM-Auslastung >94%, Swap voll)

### Fehler, die aufgetreten sind
1. `Namespace 'de.cbre.break' is not a valid Java package name as 'break' is a Java keyword` → **Behoben durch Umbenennung zu `de.cbre.breakapp`**
2. `Gradle build daemon disappeared unexpectedly` → **RAM-Mangel, nicht behebbar auf diesem System**
3. `R8: java.lang.OutOfMemoryError: Metaspace` → **RAM-Mangel**

---

## Was als Nächstes zu tun ist

### Option A: Build auf anderem Rechner fortsetzen (EMPFOHLEN)

**Voraussetzungen auf dem anderen Rechner:**
- Linux/macOS/Windows
- ≥8 GB RAM (16 GB empfohlen)
- Python 3.14+
- Git
- Internetverbindung

**Schritte:**

1. **Projektordner kopieren** auf den anderen Rechner:
   ```bash
   # Auf dem anderen Rechner:
   git clone <GITLAB-REPO-URL> cbre-break
   # Oder Ordner per USB/Cloud kopieren
   ```

2. **Abhängigkeiten installieren:**
   ```bash
   pip install flet==0.86.5 flet-cli==0.86.5
   ```

3. **Android SDK einrichten:**
   - Android Studio installieren ODER
   - Nur Command-line Tools installieren und SDK-Komponenten hinzufügen:
     ```bash
     sdkmanager "platforms;android-36" "build-tools;36.0.0" "ndk;28.2.13676358"
     yes | flutter doctor --android-licenses
     ```

4. **APK bauen:**
   ```bash
   cd cbre-break
   export GRADLE_OPTS="-Xmx2G -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=256m -Dorg.gradle.daemon=false"
   flet build apk --yes \
     --bundle-id de.cbre.breakapp \
     --product "CBRE Break" \
     --build-version 1.0 \
     --build-number 1 \
     --org de.cbre \
     --project CBRE_BREAK .
   ```

5. **APK verifizieren:**
   ```bash
   ls -lh build/flutter/android/app/release/app-release.apk
   ```

6. **APK auf Android-Gerät testen:**
   ```bash
   adb install build/flutter/android/app/release/app-release.apk
   ```

### Option B: GitLab CI/CD für Build nutzen

Falls kein leistungsstarker Rechner verfügbar ist:

1. GitLab-Repo erstellen und pushen
2. `.gitlab-ci.yml` mit Flet-Build-Job konfigurieren
3. GitLab CI baut das APK automatisch
4. APK als GitLab-Release veröffentlichen

### Option C: Cloud-Build-Service

- Flet bietet einen Cloud-Build-Service (kostenpflichtig)
- Alternativ: GitHub Actions/GitLab CI mit Android-Build-Image

---

## Nach erfolgreichem Build

### 1. Git-Repository initialisieren und pushen
```bash
cd /home/dosenkohl/Dokumente/CBRE-BREAK
git init
git add .
git commit -m "Initial commit: CBRE Break v1.0 - F-Droid ready"
git remote add origin https://gitlab.com/<DEIN_USERNAME>/cbre-break.git
git branch -M main
git push -u origin main
```

### 2. GitLab Release erstellen
```bash
git tag v1.0
git push origin v1.0
```
- Auf GitLab unter **Releases** → `v1.0` erstellen
- `app-release.apk` hochladen
- Download-URL notieren: `https://gitlab.com/<DEIN_USERNAME>/cbre-break/-/releases/v1.0/downloads/app-release.apk`

### 3. F-Droid Metadaten erstellen
Verzeichnis: `metadata/de.cbre.breakapp/`  
Datei: `metadata/de.cbre.breakapp.yml`

```yaml
Categories:
  - Productivity
License: GPL-3.0-only
AutoName: CBRE Break
Summary: Break-Bestellungen verwalten
Description: CBRE Break hilft bei der Verwaltung von Break-Bestellungen bei CBRE.
SourceCode: https://gitlab.com/<DEIN_USERNAME>/cbre-break
IssueTracker: https://gitlab.com/<DEIN_USERNAME>/cbre-break/issues
RepoType: PreDistributions
PreDistributions:
  - name: F-Droid
    url: https://gitlab.com/<DEIN_USERNAME>/cbre-break/-/releases/v1.0/downloads/app-release.apk
    versionCode: 1
    versionName: 1.0
    signConfig: fdroid
```

### 4. Merge Request an fdroiddata
```bash
git clone https://gitlab.com/fdroid/fdroiddata.git
cd fdroiddata
git remote add myfork https://gitlab.com/<DEIN_USERNAME>/fdroiddata.git
git checkout -b add-cbre-break
# Metadatenverzeichnis kopieren
cp -r /pfad/zu/metadata/de.cbre.breakapp metadata/
git add metadata/de.cbre.breakapp.yml
git commit -m "Add CBRE Break app"
git push myfork add-cbre-break
```
- Merge Request auf GitLab von `<DEIN_USERNAME>/fdroiddata` nach `fdroid/fdroiddata` erstellen

---

## Wichtige Pfade und Dateien

| Zweck | Pfad |
|-------|------|
| Projektordner | `/home/dosenkohl/Dokumente/CBRE-BREAK/` |
| Haupt-App | `main.py` |
| Daten | `cbre_break_data.json` |
| Logs | `cbre_break_log.txt` |
| Lizenz | `LICENSE` |
| Dependencies | `requirements.txt` |
| Git-Ausschlüsse | `.gitignore` |
| Build-Ausgabe | `build/flutter/android/app/release/app-release.apk` |
| Gradle-Config | `build/flutter/android/gradle.properties` |
| F-Droid Metadaten | `metadata/de.cbre.breakapp.yml` (noch zu erstellen) |
| Dokumentation | `DOCUMENTATION.md` |

---

## Bekannte Einschränkungen

1. **APK-Größe:** Flet-Apps sind groß (50–100 MB) wegen der Flutter-Engine. Im Pre-Distributions-Modus erlaubt, aber ungewöhnlich für F-Droid.
2. **RAM-Anforderung:** Build benötigt ≥6 GB RAM. Auf diesem System (3,4 GB) nicht möglich.
3. **Java-Keyword:** Bundle-ID darf kein Java-Schlüsselwort enthalten (daher `breakapp` statt `break`).

---

## Kontakt

Bei Fragen zur Integration: Siehe `DOCUMENTATION.md` oder F-Droid-Dokumentation: https://docs.f-droid.org/
