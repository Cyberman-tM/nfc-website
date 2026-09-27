# Quelldaten

`database.json` ist die zentrale, handpflegbare Datenquelle für den späteren Website-Build.

- `links` ist die unabhängige Liste aller Links. Jeder Link steht genau einmal darin. Die Schlüssel sind stabile IDs; `descriptions` enthält optionale Texte nach Sprachcode, zum Beispiel `"de": "..."` und `"en": "..."`.
- `url` ist immer die aktuell zu verwendende Adresse. Wenn sich die Adresse ändert, bleibt die Link-ID gleich und optional kommt `legacyUrl` mit der früheren Adresse dazu. Beim Einlesen eines NFC-JSON werden sowohl `url` als auch `legacyUrl` derselben Link-ID zugeordnet; neu erstellte Datensteine verwenden `url`. `legacyUrl` wird nur bei tatsächlichen URL-Änderungen eingetragen.
- `tokenCategories` und `linkCategories` sind getrennte Kategorienverzeichnisse. Die Trennung verhindert, dass eine Token-Kategorie versehentlich als Link-Kategorie interpretiert wird. Token-Kategorien können neben `labels` auch lokalisierte `descriptions` enthalten.
- Jeder Datenstein hat genau ein `categoryId`, das auf `tokenCategories` verweist. Jeder Link hat ein `categories`-Array mit null oder mehr IDs aus `linkCategories`.
- `categoryRules` enthält automatisch zugewiesene Kategorien. Eine Regel für Links setzt `linkCategoryId`; eine Regel für Datensteine setzt `tokenCategoryId`. Der Website-Build wertet Regeln zusätzlich zu den manuell gesetzten Kategorien aus.
- Die globale Linkübersicht zeigt externe Ziel-URLs. URLs auf `nfc.tlhIngan.at` bleiben den Datensteinseiten zugeordnet, werden aber aus dieser Übersicht ausgeblendet.
- `tokens` enthält Datensteine. `links` verweist auf Link-IDs, damit Beschreibungen nicht pro Datenstein dupliziert werden müssen.
- `tokens.*.descriptions` enthält die lokalisierten Texte zum Datenstein.
- `tokens.*.shortLabel` enthält eine kurze, lokalisierbare Bezeichnung, die auf Detailseiten und in Datenstein-Auflistungen zusätzlich zur ausführlichen Beschreibung erscheint.
- `tokens.*.media.altTexts` enthält optionale, lokalisierte Alternativtexte für `model`, `front` und `back`. Sie beschreiben den Bildinhalt, nicht den Dateinamen; fehlt ein Text, erzeugt der Website-Build einen allgemeinen Ersatztext.
- `tokens.*.year` enthält das Jahr des Datensteins.
- `tokens.*.chipType` enthält den Typ des verwendeten NFC-Chips, falls bekannt, zum Beispiel `NXP NTAG216`.
- `defaultChipType` legt den vorläufigen Chiptyp für Datensteine ohne eigenen Eintrag fest. Aktuell ist das `NXP NTAG216`; ein explizites `tokens.*.chipType` überschreibt den Standard.
- `nfcText` hält den Text-Eintrag vom Tag getrennt von den redaktionellen Beschreibungen der Website. `original` bewahrt den aus dem NFC-JSON gelesenen Text.
- Unveränderte NFCTools-Exporte werden unter `data/nfctools/<Token-ID>.json` archiviert. Sie sind Referenzmaterial; die Website wird weiterhin aus den normalisierten Einträgen in `database.json` erzeugt.
- `supportedLanguages` und `languages` legen die angebotenen Sprachen fest. Neue Sprachcodes können dort ergänzt und in den jeweiligen `descriptions`-Objekten verwendet werden.
- `legacyIds` dokumentiert frühere/falsch geschriebene Token-Adressen. Für DnF01 ist DnF001 eingetragen; diese ID wurde auf einem NFC-Tag verwendet. Der Website-Build muss die Weiterleitung auf DnF01 deshalb dauerhaft erzeugen.

Leere Beschreibungen sind absichtlich als leere Objekte (`{}`) angelegt. Damit ist noch kein Übersetzungstext festgelegt.

## Website erzeugen

`tools/build_site.py` erzeugt aus dieser Datenbank eine statische Vorschau im Ordner `site/`. Der Generator benötigt nur die Python-Standardbibliothek. Mit `python tools/build_site.py` werden die Seiten neu erzeugt.
