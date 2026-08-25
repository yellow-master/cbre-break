# CBRE Break – F-Droid Integration Handoff

**Datum:** 2026-08-25  
**Status:** GitHub Actions Workflow konfiguriert, APK-Build läuft online

---

## Was bereits erledigt ist

### 1. Projektdateien vorbereitet
- ✅ `LICENSE` – GPL-3.0 Lizenztext hinzugefügt
- ✅ `requirements.txt` – `flet==0.86.5`
- ✅ `.gitignore` – Runtime-Dateien, Build-Artefakte, IDE ausgeschlossen
- ✅ `DOCUMENTATION.md` – F-Droid-Integration dokumentiert (Version 0.4.0)
- ✅ `main.py` – "Made by M.M" Footer hinzugefügt
- ✅ `.github/workflows/build-apk.yml` – GitHub Actions Workflow für automatischen APK-Build
- ✅ `build_apk.sh` – Build-Skript für lokalen Build (ausführbar)
- ✅ `metadata/de.cbre.breakapp.yml` – F-Droid Metadaten mit GitHub-URLs

### 2. Git-Repository
- ✅ Git initialisiert und committet (3 Commits)
- ✅ Branch: `master`
- ✅ GitHub-Username: `yellow-master`
- ✅ Dateien im Repo: main.py, LICENSE, requirements.txt, .gitignore, DOCUMENTATION.md, FDROID_HANDOFF.md, .github/workflows/build-apk.yml, build_apk.sh, metadata/

### 3. GitHub Actions CI/CD
- Workflow-Datei: `.github/workflows/build-apk.yml`
- Trigger: Push auf `main` oder Tags `v*`
- Build-Umgebung: ubuntu-latest mit Flutter 3.44.8, Java 17, Android SDK
- RAM-Einstellungen: `GRADLE_OPTS="-Xmx2G -XX:MaxMetaspaceSize=512m -XX:ReservedCodeCacheSize=256m -Dorg.gradle.daemon=false"`
- Bundle-ID: `de.cbre.breakapp`

---

## Nächste Schritte (einfach, online)

### 1. Repository auf GitHub erstellen und pushen

```bash
# Auf diesem Rechner ausführen:
git remote add origin https://github.com/yellow-master/cbre-break.git
git branch -M main
git push -u origin main
```

### 2. GitHub Actions Pipeline auslösen

Der Build startet **automatisch** beim Push auf `main`.

Du kannst ihn auch manuell starten:
- GitHub Repo öffnen → **Actions** → **Build CBRE Break APK** → **Run workflow**

### 3. APK herunterladen

**Option A: Als Artifact (bei jedem Build)**
- Actions → Laufenden/abgeschlossenen Workflow öffnen
- Job `build-apk` → **Artifacts** → `cbre-break-apk` herunterladen
- Enthält: `app-release.apk`

**Option B: Als GitHub Release (bei Tag-Push)**
```bash
git tag v1.0
git push origin v1.0
```
- GitHub Repo → **Releases** → `v1.0` öffnen
- `app-release.apk` direkt downloaden

---

## Nach erfolgreichem Build: F-Droid Release

### 1. APK zu GitHub Release hinzufügen (falls nicht automatisch)

```bash
git tag v1.0
git push origin v1.0
```

Die GitHub Actions Workflow erstellt automatisch einen Release mit der APK.

### 2. F-Droid Metadaten prüfen

Die Datei `metadata/de.cbre.breakapp.yml` ist bereits mit GitHub-URLs konfiguriert:
- SourceCode: `https://github.com/yellow-master/cbre-break`
- IssueTracker: `https://github.com/yellow-master/cbre-break/issues`
- APK-URL: `https://github.com/yellow-master/cbre-break/releases/download/v1.0/app-release.apk`

**Wichtig:** Die URL zeigt auf `v1.0`. Wenn du eine neuere Version baust, musst du:
1. Einen neuen Tag erstellen (z.B. `v1.1`)
2. Die `versionName` und `versionCode` in der Workflow-Datei anpassen
3. Die URL in der F-Droid-Metadatei aktualisieren

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
| GitHub Actions Workflow | `.github/workflows/build-apk.yml` |
| Build-Skript (lokal) | `build_apk.sh` |
| F-Droid Metadaten | `metadata/de.cbre.breakapp.yml` |
| Dokumentation | `DOCUMENTATION.md` |
| Handoff | `FDROID_HANDOFF.md` (diese Datei) |

---

## Bekannte Einschränkungen

1. **APK-Größe:** Flet-Apps sind groß (50–100 MB) wegen der Flutter-Engine. Im Pre-Distributions-Modus erlaubt.
2. **RAM-Anforderung:** Lokaler Build benötigt ≥6 GB RAM. GitHub Actions hat 7 GB, was ausreichen sollte.
3. **Java-Keyword:** Bundle-ID `de.cbre.breakapp` (ursprünglich `break` war ein Java-Keyword).
4. **GitHub Release URL:** Die APK-URL in den F-Droid-Metadaten muss bei jeder neuen Version aktualisiert werden.

---

## Kontakt

Bei Fragen zur Integration: Siehe `DOCUMENTATION.md` oder F-Droid-Dokumentation: https://docs.f-droid.org/

