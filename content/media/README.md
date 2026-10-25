# Medien und 3D-Quellen

`content/media/<Dn-ID>/<Design-ID>/` enthält die Medien eines Datensteins. STL-Quelldateien und daraus erzeugte GLB/WebP-Dateien liegen gemeinsam pro Design. Die Dateien werden hier dauerhaft als freigegebene Projektquellen aufbewahrt.

```text
content/media/
├── README.md
└── DnF01/
    ├── Design01/
    │   ├── *.stl
    │   ├── DnF01.glb
    │   ├── DnF01_vorne.webp
    │   └── DnF01_hinten.webp
    └── Design02/
```

Die Design-ID ist der Verzeichnisname und wird zusätzlich in `content/database.json` gepflegt. IDs werden pro Datenstein fortlaufend vergeben, mindestens zweistellig (`Design01` … `Design99`, danach `Design100`).

Das Blender-Script liegt unter `tools/build_models.py`. Es verarbeitet STL-Designs aus `prepare/incoming/<Dn-ID>/<Design-ID>/` und schreibt GLB sowie WebP neben die Rohdateien. Wenn dort keine STL-Designs liegen, verarbeitet es die STL-Dateien unter `content/media/`. Der Import übernimmt die vorbereiteten Dateien nach `content/media/<Dn-ID>/<Design-ID>/`.

Die Materialdefinition enthält Farbname, Blender-Material und Materialparameter an einer Stelle. Der Farbname wird am Dateiende erkannt; unbekannte Namen erzeugen eine Fehlermeldung.

Der Website-Build kopiert nur GLB und WebP der in `content/database.json` aufgeführten Designs nach `site/media/<Dn-ID>/<Design-ID>/`. STL-Dateien werden nicht veröffentlicht. Token-Seiten verwenden die Vorschaubilder als Fallback für die optionale 3D-Ansicht.
