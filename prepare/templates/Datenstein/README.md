# Vorlage: neuer Datenstein

Kopiere diesen Ordner nach `prepare/incoming/<Dn-ID>/`. Fülle `token_info.json` aus, lege STL-Dateien direkt in `Design01/` ab und folge [der Ablaufanleitung](../../incoming/README.md).

Der NFCTools-Originalexport ist optional und heißt `<Dn-ID>.json`, zum Beispiel `DnF03.json`. Er bleibt im lokalen, von Git ignorierten Eingangsordner erhalten; in `content/token_archive/` legt der Importer nur eine bereinigte Archivkopie unter demselben Dateinamen ab. Der Import vergleicht die Eingaben mit Datenbank und Medien, zeigt Änderungen zunächst nur an und übernimmt sie erst mit `--apply` und Bestätigung. Die Website wird danach separat mit `python tools/build_site.py` generiert.
