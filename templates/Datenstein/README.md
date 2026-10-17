# Vorlage: neuer Datenstein

Diese Vorlage ist ein Arbeitsordner für die Vorbereitung eines neuen Datensteins. Kopiere den **gesamten Ordner** nach `data/drafts/<Dn-ID>/`, zum Beispiel `data/drafts/DnF03/`. Bereite Daten und Dateien dort an einem Ort vor. Der Build liest Entwürfe nicht ein.

## Vorbereitung

1. `token-entry.json` in `<Dn-ID>.json` umbenennen und die Platzhalter ausfüllen. Die Datei ist **nur der Datenbankeintrag für einen Token**; zum Einpflegen wird ihr Inhalt später unter `tokens` in `data/database.json` eingefügt.
2. Den unveränderten NFCTools-Export als `nfctools-export.json` in diesem Entwurfsordner ablegen. So bleibt die Quelldatei getrennt vom angepassten Webseiteneintrag.
3. Design-Dateien in `3d/Design01/` innerhalb des Entwurfsordners ablegen. Die erwarteten veröffentlichten Dateinamen sind `<Dn-ID>.glb`, `<Dn-ID>_vorne.webp` und `<Dn-ID>_hinten.webp`. STL-Dateien sind optionale Blender-Eingaben. Die Bilder sollten 512 × 512 Pixel groß sein.
4. Wenn es mehrere Designs gibt, weitere Ordner `3d/Design02/`, `3d/Design03/` usw. anlegen und für jedes Design ein Objekt in `designs` ergänzen.
5. Wenn der Datenstein bereit ist, den Entwurfsordner zur Übernahme geben. Dabei werden Linkdefinitionen und IDs geprüft, der Eintrag in `database.json` ergänzt und die Dateien in ihre endgültigen Ablagen `data/nfctools/` und `3d/<Dn-ID>/` übernommen. Danach kann die Website mit `python tools/build_site.py` neu erzeugt werden.

## Vor dem Übergeben prüfen

- Dn-ID ist korrekt und noch nicht vergeben; Jahr und Token-Kategorie stimmen.
- `nfcText.original` entspricht dem Text auf dem NFC-Tag und enthält die Tag-URL.
- `links` enthält die IDs der Ziele aus dem NFC-Datensatz. Neue Ziele brauchen zusätzlich je eine passende Definition im zentralen `links`-Verzeichnis der `database.json`.
- Beschreibungen dürfen zunächst `{}` sein. `shortLabel.de` sollte für die Übersicht ausgefüllt sein.
- Dateinamen, Design-IDs und Bildbeschreibungen stimmen. Fehlende Medien werden auf der Seite nicht angezeigt.

Im Entwurfsordner liegen `nfctools-export.json`, `<Dn-ID>.json` und `3d/Design01/`. Das `3d/`-Verzeichnis hier ist ein vorbereiteter Ablageort im Entwurf; im fertigen Projekt kommt die Dn-ID als zusätzliche Ordnerebene dazu: `3d/<Dn-ID>/Design01/`. Details zum Datenbankschema stehen in `data/README.md`, zum Medienaufbau in `3d/README.md`.
