# 3D-Modelle

Hier liegen die Blender-Eingaben und die daraus erzeugten Dateien für Datensteine. Jeder Datenstein bekommt einen Unterordner, dessen Name seiner ID entspricht. Das Blender-Script wird in diesem Verzeichnis gestartet und verarbeitet die Datenstein-Unterordner.

```text
3d/
├── build_models.py       # Blender-Script, verarbeitet die ID-Unterordner
├── README.md
├── DnF01/
│   ├── *.stl             # Eingabedateien; interne Namen sind scriptabhängig
│   ├── DnF01.glb         # erzeugtes 3D-Modell
│   ├── DnF01_vorne.webp  # erzeugte Vorderansicht
│   └── DnF01_hinten.webp # erzeugte Rückansicht
└── DnF02/
    └── *.stl             # Eingabedateien, Ordner für neue 3D-Dateien vorbereitet
```

Die Blender-Erzeugung ist ein separater, bei Bedarf wiederholbarer Schritt. Sie exportiert das animierte Pivot zusammen mit den Meshes ins GLB. Beim Website-Build werden ausschließlich die exakt nach der Datenstein-ID benannte GLB-Datei und die beiden WebP-Ansichten in `site/media/<ID>/` kopiert. STL-Dateien und Blender-Scripts werden nie veröffentlicht.

## DnF01

Der Ordner enthält die STL-Eingaben sowie das mit `build_models.py` erzeugte GLB-Modell und die beiden WebP-Ansichten. Die Ansichten sind 512 × 512 Pixel groß; `vorne` zeigt die standardisierte Seite, `hinten` das individuelle Motiv. Die Token-Seite versucht, das Draco-komprimierte GLB mit dem optionalen `<model-viewer>`-Webcomponent anzuzeigen. Enthält das GLB die Modellanimation, kann sie abgespielt und pausiert werden; ansonsten dreht sich die Ansicht automatisch um das Modell. Bis das Modell geladen ist oder wenn Laden/Decodieren fehlschlägt, bleiben die beiden Standbilder als Fallback verfügbar. JavaScript und der externe Webcomponent sind nur für die interaktive 3D-Ansicht nötig.

Das eingecheckte `DnF01.glb` enthält die Pivot-Animation `DnF01_PivotAction` und die erforderliche Draco-Kompression. STL-Meshes müssen vor dem Parentieren in lokale Pivot-Koordinaten verschoben werden, damit ihre bereits absoluten Vertex-Koordinaten nicht zusätzlich zur Pivot-Translation exportiert werden. Für die 3D-Ansicht wird die Münze auf ihre schmale Kante gestellt und in zehn Sekunden einmal gedreht; die statischen Ansichten zeigen weiterhin die Vorder- und Rückseite face-on. Die Website spielt die Modellanimation im 3D-Viewer ab; automatische Ansichtsdrehung dient nur als Rückfall für Modelle ohne eingebettete Animation. Nach einer Änderung an `build_models.py` die GLB-Dateien in Blender neu erzeugen und die Vorschau prüfen.

## DnF02

Der Ordner enthält die STL-Eingaben sowie das erzeugte `DnF02.glb` und die Ansichten `DnF02_vorne.webp` und `DnF02_hinten.webp`. Der Website-Build übernimmt nur GLB und WebP-Dateien in die statische Ausgabe. Das Token wird in `data/database.json` als DnF02, Jahrgang 2026, Kategorie F geführt. Die Kurzbezeichnung ist „Datenstein Lieven“; der NFCTools-Text und die Linkziele sind erfasst. Die ausführliche Beschreibung ist noch offen. Als Chiptyp gilt `NXP NTAG216`.

Die eigenständige Vorschau unter `preview/` lädt die Quelldateien direkt aus diesem Ordner.
