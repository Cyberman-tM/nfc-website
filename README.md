# nfc-website

Statische, mehrsprachige Dokumentationswebsite für NFC-Datensteine (De' nagh).

## Ordnerübersicht

- `prepare/` enthält Arbeitsmaterial: Vorlagen, lokale Rohdaten und eine Designvorschau.
- `content/` enthält die freigegebenen Quelldaten, das Token-Archiv und Medien.
- `site/` enthält die automatisch erzeugte Website.
- `tools/` enthält Import-, Blender- und Website-Scripts.

Weiterführend: [Datenbankschema](content/README.md), [Vorlage](prepare/templates/Datenstein/README.md), [Arbeitsablauf](prepare/incoming/README.md), [Architekturentscheidungen](PROJECT.md).

## Datenstein vorbereiten und übernehmen

Kopiere `prepare/templates/Datenstein/` nach `prepare/incoming/<Dn-ID>/`. Ergänze `token_info.json`, lege STL-Dateien in `Design01/` ab und folge [der Ablaufanleitung](prepare/incoming/README.md).

Änderungen erst ansehen, dann übernehmen:

```powershell
python tools/import_tokens.py DnF04
python tools/import_tokens.py DnF04 --apply
```

Die Website wird getrennt aus den freigegebenen Daten generiert:

```powershell
python tools/build_site.py
```

Die fertigen Dateien liegen danach unter `site/`. GitHub Actions baut und veröffentlicht sie bei Pushes auf `main` mit GitHub Pages.
