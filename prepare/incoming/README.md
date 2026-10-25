# Neue Datensteine vorbereiten

Lege für jeden Datenstein einen Ordner `prepare/incoming/<Dn-ID>/` an und kopiere den Inhalt aus `prepare/templates/Datenstein/` hinein. Die Eingaben bleiben dort als lokale Rohquelle erhalten. Datenstein-Ordner werden nicht in Git eingecheckt: NFCTools-Daten können private Angaben enthalten.

## Ablauf

1. `token_info.json` mit den redaktionellen Informationen über den Datenstein ausfüllen. Die Datei verwendet dasselbe Schema wie ein Eintrag unter `tokens` in `content/database.json`.
2. STL-Dateien pro Design direkt in `Design01/`, `Design02/` usw. ablegen. Optional den NFCTools-Originalexport als `<Dn-ID>.json` dazulegen, zum Beispiel `DnF03.json`. Diese Rohdatei bleibt lokal in `prepare/incoming/`.
3. Optional Animation und Farben prüfen: Öffne `tools/build_models.py` im Blender-Script-Editor und führe es aus. STL-Dateien aus `prepare/incoming/` werden verarbeitet; GLB und WebP landen neben den Eingaben.
4. Änderungsvorschau ansehen: `python tools/import_tokens.py <Dn-ID>`. Der Import zeigt Token-Felder, Linkdefinitionen und Medienänderungen.
5. Nach Prüfung übernehmen: `python tools/import_tokens.py <Dn-ID> --apply`. Bei erkannten E-Mail-Adressen fragt der Import vor der Übernahme; in öffentlichen Daten wird die Adresse durch einen Platzhalter ersetzt.
6. Website separat generieren: `python tools/build_site.py`.

Der Import aktualisiert einen bestehenden Datenstein anhand seiner ID, legt keine doppelten Token an und entfernt keine unbenutzten Linkdefinitionen. Er baut die Website nicht. Änderungen an der Rohquelle bleiben durch erneutes Ausführen des Vorschau-Befehls erkennbar.

`<Dn-ID>.json` ist der optionale NFCTools-Originalexport. Bei der Übernahme wird daraus eine bereinigte Archivkopie unter `content/token_archive/<Dn-ID>.json` geschrieben. Die Originaldatei bleibt unverändert im lokalen, von Git ignorierten Eingangsordner und wird nicht mitveröffentlicht.
