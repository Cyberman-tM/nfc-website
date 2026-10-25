# Quelldaten

`content/database.json` ist die zentrale, handpflegbare Datenquelle für den späteren Website-Build.

- `links` ist die unabhängige Liste aller Links. Jeder Link steht genau einmal darin. Die Schlüssel sind stabile IDs; `descriptions` enthält optionale Texte nach Sprachcode, zum Beispiel `"de": "..."` und `"en": "..."`.
- `url` ist immer die aktuell zu verwendende Adresse. Wenn sich die Adresse ändert, bleibt die Link-ID gleich und optional kommt `legacyUrl` mit der früheren Adresse dazu. Beim Einlesen eines NFC-JSON werden sowohl `url` als auch `legacyUrl` derselben Link-ID zugeordnet; neu erstellte Datensteine verwenden `url`. `legacyUrl` wird nur bei tatsächlichen URL-Änderungen eingetragen.
- `tokenCategories` und `linkCategories` sind getrennte Kategorienverzeichnisse. Die Trennung verhindert, dass eine Token-Kategorie versehentlich als Link-Kategorie interpretiert wird. Token-Kategorien können neben `labels` auch lokalisierte `descriptions` enthalten.
- Jeder Datenstein hat genau ein `categoryId`, das auf `tokenCategories` verweist. Jeder Link hat ein `categories`-Array mit null oder mehr IDs aus `linkCategories`.
- `categoryRules` enthält automatisch zugewiesene Kategorien. Eine Regel für Links setzt `linkCategoryId`; eine Regel für Datensteine setzt `tokenCategoryId`. Der Website-Build wertet Regeln zusätzlich zu den manuell gesetzten Kategorien aus.
- Die globale Linkübersicht zeigt externe Ziel-URLs. URLs auf `nfc.tlhIngan.at` bleiben den Datensteinseiten zugeordnet, werden aber aus dieser Übersicht ausgeblendet.
- `tokens` enthält Datensteine. `links` verweist auf Link-IDs, damit Beschreibungen nicht pro Datenstein dupliziert werden müssen.
- `tokens.*.descriptions` enthält die lokalisierten Texte zum Datenstein.
- `tokens.*.title` enthält einen optionalen lokalisierten Titel. Er wird auf der Detailseite angezeigt und im Browser-Seitentitel nach der Dn-ID verwendet.
- `tokens.*.shortLabel` enthält eine kurze, lokalisierbare Bezeichnung, die auf Detailseiten und in Datenstein-Auflistungen zusätzlich zur ausführlichen Beschreibung erscheint. Wenn kein eigener `title` eingetragen ist, ergänzt `shortLabel` den Browser-Seitentitel.
- `tokens.*.designs[].altTexts` enthält optionale, lokalisierte Alternativtexte für `model`, `front` und `back` des jeweiligen Designs. Sie beschreiben den Bildinhalt, nicht den Dateinamen; fehlt ein Text, erzeugt der Website-Build einen allgemeinen Ersatztext.
- `tokens.*.year` enthält das Jahr des Datensteins.
- `tokens.*.designs` listet die Designs desselben Inhalts. Jedes Design hat eine stabile `id` (Verzeichnisname wie `Design01`) und einen separat gepflegten `name`. Fehlt das Feld bei älteren Einträgen, gilt `Design01` als einziges Design.
- Design-IDs sind innerhalb einer Dn-ID eindeutig und numerisch fortlaufend. Die Nummer wird mindestens zweistellig formatiert (`Design01` … `Design99`, danach `Design100` usw.); eine zusammengesetzte ID aus Datenstein- und Design-ID wird nicht gespeichert.
- Medien liegen unter `content/media/<Dn-ID>/<Design-ID>/`. Dort bleiben STL-Quellen und erzeugte GLB/WebP-Dateien pro Design zusammen. Die Website veröffentlicht nur GLB und WebP. Die Dn-ID-Seite bleibt für alle Designs dieselbe; Übersichten und Bestandszahlen zählen Inhalte/Dn-IDs, nicht Designs.
- `tokens.*.chipType` enthält den Typ des verwendeten NFC-Chips, falls bekannt, zum Beispiel `NXP NTAG216`.
- `defaultChipType` legt den vorläufigen Chiptyp für Datensteine ohne eigenen Eintrag fest. Aktuell ist das `NXP NTAG216`; ein explizites `tokens.*.chipType` überschreibt den Standard.
- `nfcText` hält den Text-Eintrag vom Tag getrennt von den redaktionellen Beschreibungen der Website. `original` bewahrt den aus dem NFC-JSON gelesenen Text.
- Der Importer legt NFCTools-Exporte bereinigt unter `content/token_archive/<Token-ID>.json` ab. Die lokale Rohquelle bleibt in `prepare/incoming/<Token-ID>/`; dieser Ordner wird nicht veröffentlicht oder eingecheckt.
- `supportedLanguages` und `languages` legen die angebotenen Sprachen fest. Neue Sprachcodes können dort ergänzt und in den jeweiligen `descriptions`-Objekten verwendet werden.
- `legacyIds` dokumentiert frühere/falsch geschriebene Token-Adressen. Für DnF01 ist DnF001 eingetragen; diese ID wurde auf einem NFC-Tag verwendet. Der Website-Build muss die Weiterleitung auf DnF01 deshalb dauerhaft erzeugen.

Leere Beschreibungen sind absichtlich als leere Objekte (`{}`) angelegt. Damit ist noch kein Übersetzungstext festgelegt.

## Neuen Datenstein vorbereiten und übernehmen

Kopiere `prepare/templates/Datenstein/` nach `prepare/incoming/<Dn-ID>/`. Der Vorschau- und Importbefehl steht in [incoming/README.md](../prepare/incoming/README.md). `python tools/import_tokens.py <Dn-ID>` zeigt die Änderungsvorschau; mit `--apply` wird nach Bestätigung in `content/database.json`, `content/token_archive/` und `content/media/` übernommen. Vorhandene Linkdefinitionen bleiben erhalten, auch wenn sie gerade nicht verwendet werden.

## Website erzeugen

`tools/build_site.py` erzeugt ausschließlich aus `content/database.json` und den freigegebenen Medien eine statische Vorschau im Ordner `site/`. Der Import und der Website-Build sind getrennte Schritte. Mit `python tools/build_site.py` werden die Seiten neu erzeugt.

Der Build prüft außerdem die erzeugten Hauptseiten, alle Datensteinseiten und deren lokale HTML-Verweise. Ein fehlendes lokales Ziel lässt den Build fehlschlagen.
