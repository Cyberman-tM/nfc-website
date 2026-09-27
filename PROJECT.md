# NFC-Website: Projekt- und Architekturleitfaden

Diese Datei beschreibt die dauerhaften Projektregeln und die geplante Website-Architektur. Sie ist eine Arbeitsgrundlage für Maintainer und KI-Assistenten. Bei Änderungen zuerst diese Datei und `data/README.md` lesen.

## Quellen und Zuständigkeiten

- `data/database.json` ist die handgepflegte Inhaltsdatenbank für Sprachen, Kategorien, Links und Datensteine. Sie ist die Quelle für diese Inhaltsdaten.
- `data/README.md` beschreibt das aktuelle Datenbankschema.
- `tools/build_site.py` erzeugt die statischen HTML-Seiten aus der Inhaltsdatenbank; die Standardausgabe liegt unter `site/`.
- Diese Datei beschreibt Verhalten, URL-Regeln, Gestaltungsziele und offene Architekturentscheidungen.
- Ausgelieferte Seiten sollen statisches HTML und CSS sein. Ein Build darf Dateien aus Quelldaten erzeugen; im Browser wird die Seite nicht erst dynamisch aufgebaut.
- Keine CMS-, Datenbankserver- oder Website-Laufzeit-Abhängigkeit ist vorgesehen. Der Generator ist `tools/build_site.py` (Python-Standardbibliothek); er erzeugt statische Ausgabedateien in `site/`.

## Zweck und Grundprinzip

Die Website unter `https://nfc.tlhIngan.at/` ist ein langfristig wartbares, mehrsprachiges Informationsverzeichnis für physische NFC-Datensteine (Klingonisch: De' nagh).

Leitprinzip: **write and forget**. Veröffentlichtes Token-Material dokumentiert einen festgelegten Stand von Inhalt und Design. Wesentliche Änderungen werden als neue Datensteine beziehungsweise neue Stände hinzugefügt; bestehende historische URLs werden nicht stillschweigend auf neuere Inhalte umgeleitet oder überschrieben. Jahrgangsseiten bleiben nach Veröffentlichung statisch. Sie dürfen als Vorlage für spätere Jahrgänge dienen.

Der Jahrgang bezeichnet den Stand im Zyklus zwischen den jährlichen qepHoms (Treffen im November in Saarbrücken), nicht zwingend das Kalender- oder Produktionsjahr. Alles, was für ein qepHom vorbereitet wird, gehört zu dessen Jahrgang; alles nach dem Treffen gehört zum nächsten Jahrgang. Beispiel: Vor dem qepHom 2026 erstellte Datensteine gehören zu 2026, danach erstellte zu 2027.

## Identitäten und IDs

- Eine Datenstein-ID hat das Format `DnXYZ`: festes Präfix `Dn`, ein hexadezimales Kategoriezeichen `X` (`0` bis `F`) und zwei hexadezimale Nummernzeichen `YZ` (`00` bis `FF`). Beispiel: `DnF01`.
- Es gibt 16 mögliche Kategorien mit 256 Nummern je Kategorie. IDs sind unveränderlich, werden nie wiederverwendet; Nummerierungslücken sind zulässig.
- Die ID identifiziert einen Datenstein, nicht einen einzelnen physischen Chip. Mehrere physische Exemplare desselben Datensteins dürfen dieselbe ID und URL verwenden.
- Für den aktuellen Jahrgang sind zunächst Kategorien `0` (Allgemein) und `F` (Freiform) vorgesehen. Freiform umfasst Datensteine, die sich nicht in die anderen Kategorien einordnen lassen, sowie Datensteine, die für andere erstellt wurden. Kategorien `1` bis `E` werden für spätere Jahrgänge gesammelt.
- Es ist noch offen, ob unterschiedliche Designs mit gleichem Inhalt eigene Dn-IDs bekommen und wie solche Varianten intern verknüpft werden. Die bevorzugte Richtung ist, für jedes Design einen eigenen Datenstein-Link zu haben; die Entscheidung steht aus.
- Ein Wechsel des NFC-Chiptyps soll nach aktueller Planung eine neue Dn-ID erhalten: Ein neuer Chiptyp wäre Teil eines neu entworfenen beziehungsweise verbesserten Tokens und damit effektiv ein neuer Datenstein.

## URL-Struktur

Die Subdomain ist `nfc.tlhIngan.at`; in den Pfaden wird kein zusätzliches `/nfc/` verwendet.

- `/` – Einstieg und Erklärung
- `/years/` – Übersicht der vorhandenen Jahrgänge
- `/tokens/` – statische Übersicht aller Datensteine, aufsteigend nach ID sortiert
- `/YYYY/` – Übersicht der Datensteine dieses Jahrgangs
- `/YYYY/DnXYZ` – Seite eines Datensteins, zum Beispiel `/2026/DnF01`
- `/links/` – laufend aktualisierte globale Übersicht aller bisher verwendeten externen Ziel-URLs
- `/links/categories/<link-category-id>/` – statische Ansicht aller URLs einer Link-Kategorie; Kategorien in `/links/` verlinken auf diese Seiten.
- `/categories/` – regelmäßig aktualisierte Übersicht der Datenstein-Kategorien.

Die Startseite ist eine knappe Verwaltungsübersicht für neugierige Besucher und Maintainer. Sie zeigt beim Build aus `database.json` berechnete Gesamtzahlen für Datensteine, Jahrgänge, definierte Kategorien (mit Zahl belegter Kategorien) und Linkziele sowie aufgeschlüsselte Listen der Jahrgänge, Kategorien und Datensteine. Diese Anzeigen sind einfache Links auf die jeweiligen statischen Übersichts- oder Detailseiten; die Startseite benötigt dafür kein JavaScript.

`/tokens/` ist in der Hauptnavigation vorerst nicht verlinkt, damit der zentrierte pIqaD-Schriftzug dort Platz behält. Die Seite ist erreichbar und wird vorerst über die Tabellenüberschrift „Datenstein“ im Linkverzeichnis verlinkt; weitere Verweise können später ergänzt werden.

URLs aus veröffentlichten Seiten und auf NFC-Tags sind dauerhaft zu erhalten. Bereits im Umlauf befindliche frühere/falsch geschriebene Token-URLs werden in `legacyIds` dokumentiert und beim Build auf die gültige Seite weitergeleitet. Die tatsächlich verwendete frühere ID `DnF001` muss deshalb dauerhaft auf `DnF01` weiterleiten. Weiterleitungen dürfen historische Datensätze nicht auf inhaltlich neue Datensteine umleiten.

## Token-Inhalt und NFC-Daten

- Die Webseite enthält ausführlichere Informationen als der NFC-Chip: Beschreibung, Zweck, externe Links, Zusatzinformationen sowie bei Bedarf Medien und technische/historische Hinweise.
- Im NFC-Tag steht zuerst ein kurzer Texteinsatz, der die URL als Text enthält, danach der explizite URL-Eintrag. Ein Android-Test zeigte, dass die Übersicht nur dann angezeigt wurde, wenn der Texteinsatz zuerst kommt. Diese Reihenfolge ist eine praktische Vorgabe aus dem Test.
- NFCTools-JSON-Exporte sind Referenz-/Quelldaten und können je Datenstein-ID im Repository abgelegt werden. Ihr Format ist nicht das verbindliche Website-Datenbankschema und kann sich noch ändern.
- Mehrere physische Exemplare mit demselben Inhalt und Design können dieselbe Dn-ID haben. Ob gleiche Inhalte mit unterschiedlichen Designs eigene IDs bekommen, ist noch offen. Der Nutzer tendiert zu einem eigenen Datenstein-Link je Design.
- Auf Token-Seiten sind sichtbare Verweise auf Datensteine mit gleichem Inhalt oder gleichem Design erwünscht. Eine kompakte Infobox oder ein Abschnitt „Verwandte Datensteine“ ist eine mögliche Darstellung; Datenbankschema und genaue Darstellung sind offen.
- Der optionale Chiptyp wird im Token-Datensatz im Feld `chipType` geführt und in den Details angezeigt. Für `DnF01` ist `NXP NTAG216` eingetragen. Ein anderer Chiptyp soll voraussichtlich als neuer Datenstein mit neuer ID behandelt werden.

## Links und Kategorien

- Links dürfen und sollen in der globalen Linkübersicht wiederverwendet werden. Eine zentrale Linkdefinition mit URL und Beschreibung vermeidet inkonsistente Beschreibungen.
- `database.json` enthält bereits getrennte Verzeichnisse für `tokenCategories` und `linkCategories`, automatische `categoryRules`, Links und Tokens. Kategorien werden zentral definiert, damit weitere Kategorien ergänzt werden können, ohne Seiten einzeln umzuschreiben.
- `/links/` ist ein lebendes Verzeichnis. Es kann bei neuen Tokens ergänzt und neu generiert werden. Ein Eintrag soll nach Möglichkeit Ziel-URL, Beschreibung/Zweck, verwendete Jahrgänge und zugehörige Dn-IDs zeigen.
- Die Linkliste ist beim Laden standardmäßig aufsteigend nach Datenstein sortiert. Die Tabellenüberschriften Datenstein, Jahrgang und Kategorie verlinken auf die jeweilige Gesamtübersicht (`/tokens/`, `/years/`, `/categories/`).
- Link-Kategorie-Tags in `/links/` sind direkte Links auf die jeweilige statische Kategorieübersicht. Diese listet alle Links, die manuell oder durch eine Kategorie-Regel dieser Link-Kategorie zugeordnet sind.
- Die Überschrift „Verwendete Links“ verwendet `--identity-accent`; ein zusätzliches Label „Lebendes Verzeichnis“ entfällt.
- Neben jeder sortierbaren Tabellenüberschrift stehen die Unicode-Textzeichen `▲` und `▼` als Sortierknöpfe. Die aktive Richtung nutzt `--identity-accent`, die inaktive Richtung `--muted`. Eine separate sichtbare Sortierzeile entfällt. `aria-sort`, zugängliche Button-Beschriftungen und eine nur für Hilfstechnologien sichtbare Statusmeldung nennen die Sortierrichtung ebenfalls.
- Token-Seiten sind davon unabhängige historische Dokumentation. Gleiche Inhalte auf mehreren Seiten sind grundsätzlich in Ordnung; Wiederholung soll nur bei großen Mengen oder vielen Bildern technisch vermieden werden.
- URLs nur dann automatisch zusammenführen, wenn die Identität des Ziels eindeutig ist. Zum Beispiel `http`/`https`, `www`/ohne `www` oder unterschiedliche Query-Parameter nicht ungeprüft als gleich behandeln.
- Die Kategorienübersicht wird aus `tokenCategories` generiert und bei Änderungen neu veröffentlicht. Sie ist eine der wenigen regelmäßig aktualisierten Übersichtsseiten.

## Mehrsprachigkeit

- Deutsch und Englisch werden auf jeden Fall benötigt. Klingonisch (`tlh`) ist möglich; weitere Sprachen können später ergänzt werden.
- Empfohlene technische Richtung: nicht die erzeugten HTML-Seiten übersetzen oder direkt bearbeiten. Übersetzbare Inhaltsfelder bleiben in den Quelldaten mehrsprachig; Oberflächentexte (Navigation, Buttons, Überschriften, Meldungen) kommen in einen zentralen Katalog je Sprache. Der Generator verwendet dieselben Templates und erzeugt daraus vollständige statische Seiten pro Sprache.
- Für Englisch darf eine maschinelle Rohübersetzung als Arbeitsentwurf dienen, die anschließend manuell geprüft und überarbeitet wird. Die Rohübersetzung soll nicht zur Laufzeit des Builds erstellt werden. Klingonische Texte werden ausschließlich von Menschen übersetzt und geprüft.
- Jede Sprachfassung soll als eigenständige statische Seite verfügbar sein und mit den anderen Fassungen verlinken. Eine fehlende Übersetzung darf als nicht verfügbar ausgewiesen werden, statt unvollständigen Text vorzutäuschen.
- Das HTML-Wurzelelement erhält den gültigen Sprachcode, zum Beispiel `<html lang="de">`, `<html lang="en">` oder `<html lang="tlh">`. Abweichende Sprachabschnitte bekommen ein eigenes `lang`-Attribut.
- Klingonische Übersetzungen dürfen nicht maschinell erzeugt werden; es fehlt dafür ausreichend Primärmaterial. Übersetzungen müssen von sachkundigen Menschen erstellt oder geprüft werden.
- Die vorhandenen deutschen URLs bleiben aus Gründen der Dauerhaftigkeit bestehen. Als naheliegender Vorschlag können weitere Sprachen eigene Präfixe wie `/en/` und später `/tlh/` bekommen; Sprachpfade, Ablageort des UI-Katalogs und Behandlung unterschiedlicher Übersetzungsstände sind noch festzulegen.

## Gestaltung, Zugänglichkeit und Kompatibilität

Funktionale Lesbarkeit auf möglichst vielen Geräten und für möglichst viele Menschen hat Vorrang vor dekorativer Wirkung. Die Gestaltung soll trotzdem eine erkennbare klingonische Identität entwickeln.

### Festgelegte Farbrollen

Die Farben sind in `tools/build_site.py` als CSS-Variablen definiert und werden in die generierte `site/assets/site.css` übernommen. Komponenten sollen diese Variablen statt eigener, wiederholter Farbwerte verwenden:

- `--identity-accent` (`#f46855`): kräftige Markenfarbe für Signet/Markenzeichen, zentrale pIqaD-Dekoration, Datenstein-ID im Siegel sowie wichtige kleine Überschriften wie „Text auf dem Chip“, „Einträge“ und „Details“.
- `--accent` (`#ff8068`): normaler warmer Rot-/Korallton, unter anderem für Siegelumrandungen und Akzente.
- `--accent-soft` (`#ffb19d`): hellerer Akzent, unter anderem für Links.
- `--muted` (`#c4bcb0`): zurückhaltende warme Graufarbe für sekundäre Angaben. Im Siegel steht die Kategorie (zum Beispiel „Freiform“) in dieser Farbe und bleibt kleiner als die Datenstein-ID.

Die Infobox selbst behält ihre vorhandene Fläche und Umrandung; nur ihre Überschrift „Details“ erhält `--identity-accent`.

### Festgelegte Anordnung der Datenstein-Seite

- Im Kopfbereich des Datensteins stehen Siegel mit ID und Kategorie links, die Beschreibung mittig und die optionale 3D-Darstellung mit Pause-Schaltfläche rechts. ID und 3D-Darstellung werden von oben aus auf gleiche optische Größe abgestimmt; der Pause-Text zählt dabei nicht zur Höhe des Modells.
- Die Beschreibung steht ohne eigene sichtbare Überschrift zwischen Siegel und 3D-Darstellung. Sie nutzt den verfügbaren Platz und ist zentriert. Bei wenig Breite rücken die Symbole zusammen; die Beschreibung wechselt darunter. Bei mehrzeiliger Beschreibung wachsen der Bereich und die Symbole bleiben vertikal mittig.
- Die Infobox heißt „Details“ und beginnt auf gleicher Höhe wie der Bereich „Text auf dem Chip“. Sie behält ihre dunkle Fläche und Umrandung; ihre Überschrift verwendet die Markenfarbe.
- „Text auf dem Chip“ ist ein fester, oberer Inhaltsbereich und nimmt die verfügbare Textbreite ein. Die durchgehende Linie darunter trennt diesen oberen Bereich von den variablen Einträgen; zwischen Beschreibung und Chiptext gibt es keine Trennlinie.
- „Einträge“ ist der erste variable Inhaltsbereich. Auf breiten Ansichten umfließt dieser Block die seitlich stehende Infobox, sodass er zunächst die freie linke Fläche nutzt und nach dem Ende der Infobox die volle Breite einnimmt (L-förmiger Textfluss). Der freie Platz unterhalb der Infobox wird dadurch nicht dauerhaft blockiert.
- Auf schmalen Ansichten werden die Bereiche ohne feste Seitenbreite untereinander angeordnet; die Lesereihenfolge bleibt Beschreibung, Chiptext, Details, Einträge.
- Diese Anordnung ist die festgelegte Grundgestaltung. Kleinere visuelle Anpassungen sind möglich, sollen aber die Hierarchie und Reihenfolge nicht ohne erneute Abstimmung verändern.

### Jahrgangsübersicht

- Datensteine eines Jahrgangs werden unter eigenen Kategorieüberschriften gruppiert; die Kategorie steht nicht zusätzlich in jeder einzelnen Datenstein-Karte.
- Kategorien erscheinen nach ihrem Hexwert aufsteigend (`0` bis `F`). Innerhalb einer Kategorie werden Datensteine nach ihrer ID aufsteigend sortiert.
- `/tokens/` verwendet dieselben visuellen Datenstein-Karten ohne Kategoriegruppen und listet alle Datensteine aufsteigend nach ID.
- Die Jahrgangsseite zeigt die Jahreszahl ohne zusätzliches Label „Jahrgang“ und mit geringerem Abstand zur Breadcrumb-Navigation: links größer in `--identity-accent`, rechts dekorativ dieselbe Jahreszahl in pIqaD, gleicher CSS-Schriftgrad und gleiche Farbe. Die pIqaD-Dekoration darf bei schmalen Ansichten entfallen.
- In einer Kategorieüberschrift ist das einzelne Kategoriezeichen etwa 1,5-mal so groß wie der ausgeschriebene Kategoriename und verwendet `--identity-accent`.
- Eine Datenstein-Karte kann links ein Siegel mit der ID, in der Mitte die Kurzbeschreibung und rechts statische Vorder- und Rückseitenbilder zeigen. Die Kategorie ist bereits durch die Gruppenüberschrift erkennbar.
- Vorschaubilder erhalten feste `width`- und `height`-Werte, beschreibende Alternativtexte und auf schmalen Ansichten eine eigene Zeile.

### Startseite

- Die Hauptüberschrift „Datensteine. Dokumentiert für später.“ bleibt als prägnanter, leicht humorvoller Einstieg erhalten.
- Der erklärende Satz über die Verbindung zwischen physischen Datensteinen und Ressourcen entfällt.
- Darunter steht ein administrativer Bereich mit der Überschrift „Bestand“ und Build-Zahlen für Datensteine, Jahrgänge, definierte Kategorien (zusätzlich mit Zahl der belegten Kategorien) und Linkziele. Es folgen direkte Aufschlüsselungen nach Jahrgang, Kategorie und Datenstein; die Einträge führen zu den statischen Detail- und Übersichtsseiten. Der Abschnittstitel „Datensteine“ selbst verlinkt auf `/tokens/`.
- Im Hero stehen keine zusätzlichen Schnelllinks oder erklärenden Verbindungssätze; der Zugang zu Übersichten liegt im Bestandsbereich und in der Hauptnavigation.
- Der Bestandsbereich heißt schlicht „Bestand“; ein zusätzlicher Untertitel „Schneller Überblick“ entfällt. Die Überschrift „Datensteine“ ist selbst der Link zu `/tokens/`; ein zusätzlicher „Alle IDs ansehen“-Link entfällt.
- Die letzte Datensteinzeile hat keine zusätzliche Trennlinie am Ende des Bestandsbereichs.
- Das pIqaD-Siegel bleibt dekorativ. Beide Wortteile „De’“ und „nagh“ sollen sichtbar gleich groß wirken; auf schmalen Ansichten darf es verschwinden. Der obere Bereich ist etwas kompakter und höher angeordnet als zuvor.

### Kategorien- und Linkverzeichnis

- `/categories/` zeigt die Hauptüberschrift „Kategorien“ in `--identity-accent`; das kleine Label „Ordnungssystem“ entfällt.
- `/links/` zeigt die Hauptüberschrift „Verwendete Links“ in `--identity-accent`; das Label „Lebendes Verzeichnis“ entfällt.
- Im Linkverzeichnis sind „Datenstein“, „Jahrgang“ und „Kategorie“ als Tabellenüberschriften mit Links auf `/tokens/`, `/years/` und `/categories/` gestaltet.
- Die Tabelle ist beim ersten Laden statisch und dynamisch aufsteigend nach Datenstein sortiert. Neben jeder sortierbaren Überschrift gibt es zwei Textzeichen-Sortierknöpfe: `▲` und `▼`. Die aktive Richtung ist in `--identity-accent`, die andere in `--muted`. Die Buttons werden erst mit JavaScript eingeblendet; ohne JavaScript bleibt die nach Datenstein sortierte Tabelle lesbar.
- Eine separate sichtbare Sortierzeile und ein sichtbarer erklärender Tabellen-Caption-Text entfallen. Screenreader erhalten Tabellen-Caption, `aria-sort`, beschriftete Sortierknöpfe und eine Statusmeldung.
- Auf schmalen Viewports bleibt der Tabellenkopf sichtbar; die Tabelle kann innerhalb ihres Rahmens horizontal gescrollt werden, damit Sortierknöpfe und Spaltenüberschriften erreichbar bleiben.

### Hauptnavigation und Browser-Icon

- Die Hauptnavigation enthält derzeit Jahrgänge, Kategorien und Linkverzeichnis. Der Link zu `/tokens/` bleibt vorerst aus der Navigation entfernt, damit der pIqaD-Schriftzug mittig bleiben kann.
- Das Browser-Icon ist `tools/assets/favicon.svg`; es greift dunkle Fläche, Rautenrahmen und Flammensignet des Markenzeichens auf. Der Build veröffentlicht es unter `site/assets/favicon.svg` und bindet es in alle Seiten ein.

- Ziel ist WCAG 2.2 Level AA als praktische Gestaltungsleitlinie.
- Farbe ist nie der einzige Informationsträger; Text und Bedienelemente benötigen ausreichenden Kontrast.
- Layout ist flexibel statt auf eine feste Bildschirmbreite ausgelegt. Vergrößerter Text und schmale Viewports dürfen weder Inhalte abschneiden noch Funktionen unzugänglich machen.
- Semantische HTML-Elemente, sinnvolle Überschriftenhierarchie, aussagekräftige Linktexte und Tastaturbedienbarkeit unterstützen Screenreader und andere Hilfsmittel.
- Inhaltliche Bilder bekommen beschreibende Alternativtexte, dekorative Bilder `alt=""`; Dateinamen sind keine Alternativtexte.
- Bei Bildern sollen `width` und `height` angegeben werden, damit der Browser den Platz vor dem Laden reservieren kann.
- Token-3D-Ansichten verwenden optional das externe `<model-viewer>`-Webcomponent. Statische Bilder bleiben sichtbar, bis das Modell erfolgreich geladen ist, und dienen als Fehler-Fallback. Die Wiedergabe berücksichtigt reduzierte Bewegung und bietet eine bedienbare Umschaltung der automatischen Drehung.
- Die STL-Quelldateien und Blender-Scripts dienen ausschließlich der Medienerzeugung. Der Website-Build veröffentlicht daraus nur das ID-benannte GLB-Modell und die ID-benannten Vorschaubilder.
- KApIqaD ist eine dekorative pIqaD-Schrift; Inhaltstexte bleiben in normaler Schrift und lesbarer Umschrift. Provenienz und Hinweis zur Umschrift stehen in `tools/assets/README.md`.
- pIqaD-Elemente sind standardmäßig rein dekorativ, für Hilfstechnologien verborgen und dürfen bei Platzmangel entfallen. Sie tragen keine notwendige Information; eine Ausnahme muss ausdrücklich festgelegt werden.
- Moderne, standardkonforme HTML- und CSS-Techniken verwenden; keine Browser-Hacks. JavaScript bleibt minimal und optional.
- Für die sortierbare Linkliste darf JavaScript als progressive Verbesserung eingesetzt werden. Ohne JavaScript muss die Liste in ihrer Grundform weiterhin vollständig lesbar sein.

## Bilder und Token-Varianten

Ein Datenstein kann eine achteckige Münze mit wiederkehrendem Design auf einer Seite und unterschiedlichen Designs auf der anderen Seite sein. Eine Galerie von Vorder-/Rückseiten oder Varianten ist vorgesehen, falls sie zum endgültigen ID-Modell passt. Gemeinsamen Text nicht allein zur Vermeidung kleiner Wiederholungen zentralisieren.

## Build- und Änderungsregeln

1. Vor Änderungen `PROJECT.md`, `data/README.md` und die betroffenen Daten in `data/database.json` lesen.
2. Quelldaten und erzeugte Ausgabedateien klar unterscheiden. Quelldaten bleiben im Repository; veröffentlichte Dateien sind statische Artefakte.
3. Eine Änderung an der Datenquelle soll den nötigen Build/Regenerierungsschritt nachvollziehbar machen. Build-Schritte dürfen keine manuelle Webserver-Datenbank benötigen.
4. Vorhandene URLs und Inhalte nicht entfernen oder stillschweigend umwidmen. Alte Tippfehler-URLs nur mit expliziter Legacy-Zuordnung behandeln.
5. Der Generator ist ein einfaches Python-Skript mit Standardbibliothek (`tools/build_site.py`), das nach `site/` schreibt. Lokal dient dieser Ordner der Vorschau und bleibt von Git ausgeschlossen. GitHub Actions baut ihn bei Änderungen auf `main` und veröffentlicht ihn mit GitHub Pages. Die vorläufige Projektseiten-Adresse ist `https://Cyberman-tM.github.io/nfc-website/`; es wird vorerst keine benutzerdefinierte Domain/CNAME konfiguriert.
6. Erklärende Kommentare sind in Quelldaten, Build-Code und Projektdateien willkommen, wenn sie einen Grund oder eine Maintainer-Entscheidung festhalten. Kommentare in ausgeliefertem HTML sind nur für seitenbezogene Hinweise gedacht.

## Aktuelle Abgleichspunkte

Diese Punkte bei Datenänderungen weiterhin gegen die Inhaltsdatenbank und die endgültigen Projektentscheidungen prüfen:

- Kategorie `F` ist als `Freiform` festgelegt. Die Definition soll sowohl nicht anderweitig einordenbare Datensteine als auch für andere erstellte Datensteine umfassen.
- `data/database.json` führt aktuell nur `de` und `en` als unterstützte Sprachen; `tlh` ist geplant, aber noch nicht als veröffentlichte Übersetzung festgelegt.
- Die Kategorie-Regel für F, Tokenbeschreibungen und Linkbeschreibungen sind noch zu prüfen und gegebenenfalls zu ergänzen.
- Die ID `DnF001` ist falsch formatiert; gültig ist `DnF01`. `DnF001` wurde tatsächlich auf einem NFC-Tag verwendet und muss daher als dauerhafte Weiterleitung auf `DnF01` erhalten bleiben.
- Die Jahrgangsgrenze ist festgelegt: Alles vor dem jeweiligen November-qepHom gehört zu diesem qepHom-Jahrgang, alles danach zum nächsten.

## Noch offene Entscheidungen

- Namen und Beschreibungen für die noch nicht vergebenen Kategorien `1` bis `E`; Planung weiterer Kategorien voraussichtlich nach dem qepHom
- Sprachpfade, Übersetzungskatalog für Oberflächentexte und Verknüpfung der Sprachfassungen
- Regel für eigene IDs bei gleicher Inhaltsbasis und unterschiedlichem Design; der Nutzer bevorzugt einen eigenen Datenstein-Link je Design
- Schema für Inhalts-/Design-Beziehungen und sichtbare Verweise
- abschließende Bestätigung der Regel: ein Wechsel des Chiptyps ergibt eine neue Dn-ID
- Galerieaufbau für Vorder- und Rückseiten
- Veröffentlichungsablauf; zuerst wird die lokale Website fertiggestellt, Hosting/DNS folgt später
