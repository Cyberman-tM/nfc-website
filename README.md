# nfc-website

Statische, mehrsprachige Dokumentationswebsite für NFC-Datensteine (De' nagh).

- [Projekt- und Architekturleitfaden](PROJECT.md)
- [Quelldaten und Datenbankschema](data/README.md)

## Vorschau erzeugen

Mit Python 3 die statischen Seiten aus den Quelldaten generieren:

```powershell
python tools/build_site.py
```

Die fertigen Dateien liegen anschließend unter `site/`. Für die lokale Vorschau kann dort ein einfacher statischer HTTP-Server gestartet werden.

## GitHub Pages

Die Website wird beim Push auf `main` über GitHub Actions aus den Quelldaten neu gebaut und als statische Seite veröffentlicht. Die vorgesehene Projektseiten-Adresse ist `https://Cyberman-tM.github.io/nfc-website/`. In den Repository-Einstellungen muss unter **Settings → Pages → Build and deployment** als Quelle **GitHub Actions** ausgewählt sein. Es wird keine benutzerdefinierte Domain konfiguriert.
