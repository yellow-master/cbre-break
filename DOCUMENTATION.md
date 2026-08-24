# CBRE Break App – Dokumentation

## Status

| Datum | Version | Änderung |
|-------|---------|----------|
| 2026-08-21 | 0.1.0 | Projektstart: Flet installiert, Plan erstellt, Grundgerüst angelegt |
| 2026-08-21 | 0.1.1 | Hauptanwendung implementiert: main.py mit allen Kernfunktionen |
| 2026-08-21 | 0.1.2 | App getestet und gestartet; DeprecationWarnings behoben |
| 2026-08-21 | 0.1.3 | Gesamtpreis berechnet nur noch nicht-bezahlte Einträge |
| 2026-08-21 | 0.2.0 | Person hinzufügen, Namens-Autovervollständigung, Touch-Optimierung, Android-Kompatibilität |
| 2026-08-21 | 0.2.1 | Loading-Screen hinzugefügt, Startup optimiert für Android |
| 2026-08-21 | 0.2.2 | Absoluter Datenpfad, Desktop-Verknüpfung repariert |
| 2026-08-21 | 0.2.3 | Bearbeiten-Modus für Liste, Person/Produkt hinzufügen repariert, Button umbenannt |
| 2026-08-21 | 0.2.4 | Produkt/Person-Verwaltung als Listenansicht mit Hinzufügen/Entfernen/Speichern |
| 2026-08-21 | 0.2.5 | Icon-Referenzen korrigiert (ft.icons.Icons.*), Fehler beim Hinzufügen behoben |
| 2026-08-21 | 0.2.6 | Debug-Logs, Auto-Save in Verwaltung, Removebar, stabilere GUI-Updates |
| 2026-08-21 | 0.2.7 | Flet-API-Fixes (Colors, Padding), stabiles Hinzufügen/Entfernen in Verwaltung |
| 2026-08-21 | 0.3.0 | Neue Liste behält Personen/Produkte, Mengenfeld, Gesamtpreis mit Menge, Auto-Save repariert |
| 2026-08-21 | 0.3.1 | Autocomplete auf Anfangsbuchstaben, entfernte Vorschläge werden nicht mehr angezeigt |
| 2026-08-21 | 0.3.2 | Neue Liste erstellt leere Liste ohne Eingabezwang, Zeilen-Klick schaltet Bezahl-Status um, Vorschläge als untereinander liegende Auswahl-Buttons ohne Feldbeeinflussung, Eintragserstellung stabilisiert, Produkte bleiben bei neuer Liste erhalten |
| 2026-08-24 | 0.4.0 | F-Droid-Integration gestartet: LICENSE (GPL-3.0), requirements.txt, .gitignore, GitLab-Hosting vorbereitet, APK-Build mit Flet vorbereitet, Bundle-ID auf `de.cbre.breakapp` korrigiert, Android SDK 36 + Build-Tools + NDK installiert, Build läuft |

## Aufbau

- `main.py` – Hauptanwendung (Flet)
- `DOCUMENTATION.md` – Diese Datei
- `Plan` – Ursprünglicher Anforderungsplan
- `cbre_break_data.json` – Laufzeitdatei für Produkte, Personen und aktuelle Liste
- `LICENSE` – GPL-3.0 Lizenz
- `requirements.txt` – Python-Abhängigkeiten (`flet==0.86.5`)
- `.gitignore` – Ausschlüsse für Git (Runtime-Dateien, Build-Artefakte, IDE)
- `metadata/` – F-Droid-Metadaten (wird erstellt)
- `FDROID_HANDOFF.md` – Ausführliche Anleitung zur Fortsetzung der F-Droid-Integration auf einem Rechner mit ≥8 GB RAM

## Technische Details

- Framework: **Flet 0.86.5**
- Python: **3.14.4**
- Plattform: Linux (PC-Test), optimiert für Android/Touch
- Datenhaltung: Lokale JSON-Datei (`cbre_break_data.json`)
- Lizenz: **GPL-3.0**
- Application ID: **de.cbre.breakapp**
- F-Droid-Build-Modus: **Pre-Distributions** (APK wird lokal gebaut, F-Droid signiert und verteilt)
- Git-Hosting: **GitLab.com** (vorbereitet)
- Android SDK: **36.0.0** mit Build-Tools 36.0.0 und NDK 28.2.13676358

## Implementierte Features

 1. **Startbildschirm** – Zeigt die aktuelle Liste mit Name, Produkt, Preis und Bezahl-Status an.
 2. **Bearbeiten** – Schaltet den Editier-Modus ein; alle Felder der Liste werden zu bearbeitbaren Textfeldern, Einträge können gelöscht werden.
  3. **Neue Liste** – Eigenes Bestätigungs-Overlay: leert nur die aktuelle Liste, Personen und Produkte bleiben erhalten. Automatischer Wechsel zur Eingabemaske bei Bestätigung.
  4. **Eingabemaske** – Nacheinander: Name, Produkt (mit Autovervollständigung aus Einstellungen), Preis, Menge (Standard 1).
  5. **Produkt-Autovervollständigung** – Bei Eingabe im Produktfeld werden passende Produkte aus den Einstellungen **mit gleichem Anfangsbuchstaben** als untereinander liegende Auswahl-Buttons vorgeschlagen; Auswahl übernimmt Preis. Entfernte Produkte erscheinen nicht mehr in Vorschlägen. Das Textfeld wird während des Tippens nicht verändert.
  6. **Weiter** – Speichert den aktuellen Eintrag und ermöglicht die Eingabe weiterer Personen/Produkte.
  7. **Fertig** – Schließt die Eingabe ab und zeigt die Liste an.
  8. **Produkt verwalten** – Oben rechts; öffnet eine Listenansicht zum Hinzufügen/Entfernen von Produkten (mit Preis). Gespeicherte Produkte werden für die Autovervollständigung genutzt.
  9. **Person verwalten** – Oben rechts; öffnet eine Listenansicht zum Hinzufügen/Entfernen von Personen. Gespeicherte Personen werden für die Namens-Autovervollständigung genutzt.
 10. **Verwaltungs-UI** – Oben: Schließen-Button; Mitte: Liste mit Einträgen und Lösch-Icon; Unten: Eingabefelder + Hinzufügen-Button.
 11. **Auto-Save** – Hinzufügen und Entfernen in der Verwaltung speichert automatisch in die JSON-Datei.
 12. **Removebar** – Das Minus-Icon hinten in der Verwaltungsliste entfernt den Eintrag direkt und speichert automatisch.
 13. **Debug-Logging** – Alle wichtigen Aktionen und Fehler werden in `cbre_break_log.txt` protokolliert.
 14. **Namens-Autovervollständigung** – Bei Eingabe im Namensfeld werden passende Personen aus den Einstellungen **mit gleichem Anfangsbuchstaben** als untereinander liegende Auswahl-Buttons vorgeschlagen. Entfernte Personen erscheinen nicht mehr in Vorschlägen. Das Textfeld wird während des Tippens nicht verändert.
 15. **Hauptmenü** – Spaltenweise Anzeige: Name, Produkt (mit Mengenanzeige z. B. "2x Cola"), Preis (Menge * Einzelpreis); darunter Gesamtpreis.
 16. **Bezahl-Status** – Tippen auf die gesamte Zeile schaltet den Bezahl-Status um (ausgegraut = bezahlt). Im Bearbeiten-Modus bleibt die Checkbox anklickbar.
 17. **Touch-optimiert** – Große Buttons, Felder und Touch-Targets für Handy-Bedienung.
 18. **Android-Format** – Fenstergröße auf 400x800 (Handy-Format) eingestellt, portabel auf Android-Geräte.
 19. **Loading-Screen** – Zeigt sofort einen Lade-Indikator, während die App initialisiert wird.
 20. **Listen-Eintrag löschen** – Im Bearbeiten-Modus kann jeder Eintrag über ein Papierkorb-Icon gelöscht werden.

## Start

- **Terminal:** `python3 /home/dosenkohl/Dokumente/CBRE-BREAK/main.py`
- **Schreibtisch:** Doppelklick auf `CBRE Break.desktop` im Ordner `Schreibtisch`

## Build-Status (F-Droid-Integration)

- ✅ **LICENSE** erstellt (GPL-3.0)
- ✅ **requirements.txt** erstellt (`flet==0.86.5`)
- ✅ **.gitignore** erstellt (Runtime-Dateien, Build-Artefakte, IDE)
- ✅ **Flet-CLI** installiert (`flet-cli==0.86.5`)
- ✅ **Android SDK 36** installiert (Platform 36, Build-Tools 36.0.0, NDK 28.2.13676358)
- ✅ **SDK-Lizenzen** akzeptiert
- ✅ **Bundle-ID** korrigiert: `de.cbre.break` → `de.cbre.breakapp` (Java-Keyword-Problem)
- ⚠️ **APK-Build BLOCKIERT** – RAM-Mangel (3,4 GiB verfügbar, ≥6 GiB benötigt)
  - Gradle Daemon stürzt ab mit `OutOfMemoryError: Metaspace`
  - Build muss auf Rechner mit ≥8 GB RAM fortgesetzt werden
  - Siehe `FDROID_HANDOFF.md` für vollständige Anleitung zur Fortsetzung

**Erwartetes APK (nach erfolgreichem Build):** `build/flutter/android/app/release/app-release.apk`

**Empfohlener Build-Befehl (auf Rechner mit ≥8 GB RAM):**
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

## Nächste Schritte (F-Droid-Integration)

Siehe `FDROID_HANDOFF.md` für vollständige Anleitung.

Kurzübersicht:
1. Build auf Rechner mit ≥8 GB RAM fortsetzen
2. APK testen
3. Git-Repo zu GitLab pushen
4. GitLab-Release mit APK erstellen
5. F-Droid Metadaten erstellen (`metadata/de.cbre.breakapp.yml`)
6. Merge Request an `fdroiddata` erstellen
7. Review abwarten und App im F-Droid Katalog veröffentlichen
