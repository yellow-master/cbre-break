# CBRE Break – F-Droid Integration Handoff

**Datum:** 2026-08-24  
**Status:** Git vorbereitet, CI konfiguriert, Build muss auf anderem Rechner oder via GitLab CI durchgeführt werden

---

## Was bereits erledigt ist

### 1. Projektdateien vorbereitet
- ✅ `LICENSE` – GPL-3.0 Lizenztext hinzugefügt
- ✅ `requirements.txt` – `flet==0.86.5`
- ✅ `.gitignore` – Runtime-Dateien, Build-Artefakte, IDE ausgeschlossen
- ✅ `DOCUMENTATION.md` – F-Droid-Integration dokumentiert (Version 0.4.0)
- ✅ `main.py` – "Made by M.M" Footer hinzugefügt
- ✅ `.gitlab-ci.yml` – GitLab CI/CD Konfiguration für automatischen APK-Build
- ✅ `build_apk.sh` – Build-Skript für anderen Rechner (ausführbar)
- ✅ `metadata/de.cbre.breakapp.yml` – F-Droid Metadaten (vorbereitet)

### 2. Git-Repository
- ✅ Git initialisiert und committet (2 Commits)
- ✅ Branch: `master`
- ✅ Dateien im Repo: main.py, LICENSE, requirements.txt, .gitignore, DOCUMENTATION.md, FDROID_HANDOFF.md, .gitlab-ci.yml, build_apk.sh, metadata/

### 3. Build-Konfiguration
- Bundle-ID: `de.cbre.breakapp`
- Build-Befehl (getestet):
  ```bash
  export GRADLE_OPTS="-Xmx2G -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=256m -Dorg.gradle.daemon=false"
  flet build apk --yes \
    --bundle-id de.cbre.breakapp \
    --product "CBRE Break" \
    --build-version 1.0 \
    --build-number 1 \
    --org de.cbre \
    --project CBRE_BREAK .
  ```

---

## Optionen zur APK-Erstellung

### Option A: GitLab CI/CD (EMPFOHLEN)

Der Build läuft automatisch auf GitLab-Servern. Kein lokaler Build nötig.

**Schritte:**

1. **GitLab-Repo erstellen:**
   - Auf https://gitlab.com ein neues Repository `cbre-break` erstellen (öffentlich oder privat)
   - Lokal pushen:
     ```bash
     git remote add origin https://gitlab.com/<DEIN_USERNAME>/cbre-break.git
     git branch -M main
     git push -u origin main
     ```

2. **CI-Pipeline auslösen:**
   - Die Pipeline läuft automatisch bei Push auf `main`
   - Oder manuell auslösen unter **CI/CD → Pipelines → Run pipeline**

3. **APK herunterladen:**
   - Nach erfolgreichem Build unter **Jobs → build_apk → Artifacts** die `app-release.apk` herunterladen

**Hinweis:** Die `.gitlab-ci.yml` ist bereits konfiguriert und baut das APK mit Flutter 3.44.8 und Flet 0.86.5.

### Option B: Lokaler Build auf anderem Rechner

**Voraussetzungen:**
- Linux/macOS/Windows
- ≥8 GB RAM (16 GB empfohlen)
- Python 3.14+
- Flutter SDK 3.44.8
- Java JDK 17
- Android SDK 36

**Schritte:**

1. **Projektordner kopieren** auf den anderen Rechner (USB, Cloud, Git)

2. **Build-Skript ausführen:**
   ```bash
   chmod +x build_apk.sh
   ./build_apk.sh
   ```

3. **APK verifizieren:**
   ```bash
   ls -lh build/flutter/android/app/release/app-release.apk
   ```

4. **APK zurückschicken** an diesen PC

---

## Nach erfolgreichem Build (auf diesem PC fortsetzen)

### 1. APK zu GitLab Release hinzufügen
```bash
git tag v1.0
git push origin v1.0
```
- Auf GitLab unter **Releases** → `v1.0` erstellen
- `app-release.apk` hochladen
- Download-URL notieren

### 2. F-Droid Metadaten anpassen
In `metadata/de.cbre.breakapp.yml` die Platzhalter `<DEIN_USERNAME>` durch den tatsächlichen GitLab-Benutzernamen ersetzen.

### 3. Merge Request an fdroiddata
```bash
git clone https://gitlab.com/fdroid/fdroiddata.git
cd fdroiddata
git remote add myfork https://gitlab.com/<DEIN_USERNAME>/fdroiddata.git
git checkout -b add-cbre-break
cp -r /pfad/zu/cbre-break/metadata/de.cbre.breakapp metadata/
git add metadata/de.cbre.breakapp.yml
git commit -m "Add CBRE Break app"
git push myfork add-cbre-break
```
- Merge Request auf GitLab erstellen

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
| CI-Konfiguration | `.gitlab-ci.yml` |
| Build-Skript | `build_apk.sh` |
| F-Droid Metadaten | `metadata/de.cbre.breakapp.yml` |
| Dokumentation | `DOCUMENTATION.md` |
| Handoff | `FDROID_HANDOFF.md` (diese Datei) |

---

## Bekannte Einschränkungen

1. **APK-Größe:** Flet-Apps sind groß (50–100 MB) wegen der Flutter-Engine. Im Pre-Distributions-Modus erlaubt.
2. **RAM-Anforderung:** Lokaler Build benötigt ≥6 GB RAM. GitLab CI umgeht dieses Problem.
3. **Java-Keyword:** Bundle-ID `de.cbre.breakapp` (ursprünglich `break` war ein Java-Keyword).

---

## Kontakt

Bei Fragen zur Integration: Siehe `DOCUMENTATION.md` oder F-Droid-Dokumentation: https://docs.f-droid.org/
