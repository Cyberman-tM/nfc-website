# 3D-Modelle

Hier liegen Blender-Eingaben und erzeugte Dateien nach Datenstein und Design geordnet. Die Dn-ID bezeichnet den Inhalt; verschiedene Gestaltungen desselben Inhalts bekommen eigene Design-Unterordner.

```text
3d/
├── build_models.py
├── README.md
└── DnF01/
    ├── Design01/
    │   ├── *.stl
    │   ├── DnF01.glb
    │   ├── DnF01_vorne.webp
    │   └── DnF01_hinten.webp
    └── Design02/
        └── *.stl
```

Jeder Designordner enthält die STL-Eingaben und – sofern erzeugt – das GLB-Modell sowie die beiden 512 × 512 Pixel großen Ansichten. Die Design-ID ist der Verzeichnisname und steht zusätzlich mit einem separat gepflegten Namen in `data/database.json`. IDs werden pro Datenstein fortlaufend vergeben und mindestens zweistellig geschrieben; nach `Design99` kann `Design100` folgen.

`build_models.py` verarbeitet STL-Dateien in Design-Unterordnern. Der Website-Build veröffentlicht nur GLB und WebP aus den in `database.json` aufgeführten Designs unter `site/media/<Dn-ID>/<Design-ID>/`; Blender-Scripts und STL-Quellen werden nicht veröffentlicht.

Die Datensteinseite bleibt unter `/YYYY/<Dn-ID>/` und bietet bei mehreren Designs einen Umschalter. Eine Design-Auswahl wird als `?design=Design02` in der Seitenadresse festgehalten. Jahrgangs- und Gesamtübersichten führen den Datenstein einmal und zeigen das erste Design als Vorschau.

Die Token-Seite nutzt optional das `<model-viewer>`-Webcomponent. Statische Ansichten bleiben verfügbar, solange ein Modell lädt oder falls es nicht geladen werden kann. Modelle mit Pivot-Animation können abgespielt und pausiert werden; ohne Animation dreht sich die Ansicht automatisch, sofern Bewegung nicht reduziert werden soll.
