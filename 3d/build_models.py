import bpy
import os
import math
from mathutils import Matrix, Vector


# ============================================================
# EINSTELLUNGEN
# ============================================================

RENDER_BILDER = True
RENDER_AUFLÖSUNG = 512
RENDER_MARGIN = 1.15
RENDER_QUALITY = 90
RENDER_TRANSPARENT = True

DRACO_AKTIV = True
DRACO_LEVEL = 6
DRACO_POSITION_QUANTISIERUNG = 10
DRACO_NORMAL_QUANTISIERUNG = 10
DRACO_TEXCOORD_QUANTISIERUNG = 12
DRACO_FARBE_QUANTISIERUNG = 10
DRACO_GENERIC_QUANTISIERUNG = 12


# ============================================================
# STAMMORDNER ERMITTELN
# ============================================================

def ermittle_stammordner():
    """
    Versucht zuerst __file__ zu verwenden.
    Falls Blender dort keinen brauchbaren Pfad liefert,
    wird der gespeicherte Pfad des Textblocks build_models.py
    verwendet.
    """

    try:
        script_pfad = os.path.abspath(__file__)

        if os.path.isfile(script_pfad):
            return os.path.dirname(script_pfad)

    except NameError:
        pass

    for text in bpy.data.texts:
        if (
            text.filepath
            and os.path.basename(text.filepath).lower() == "build_models.py"
        ):
            return os.path.dirname(os.path.abspath(text.filepath))

    raise RuntimeError(
        "Der Pfad von build_models.py konnte nicht ermittelt werden. "
        "Bitte die Datei in Blender als gespeicherte Datei öffnen."
    )


STAMMORDNER = ermittle_stammordner()


# ============================================================
# MATERIALIEN
# ============================================================

MATERIALIEN = {}


def material_erstellen(name, farbe, metallic=0.0, roughness=0.45):
    if name in MATERIALIEN:
        return MATERIALIEN[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes.get("Principled BSDF")

    if bsdf:
        bsdf.inputs["Base Color"].default_value = (
            farbe[0],
            farbe[1],
            farbe[2],
            1.0,
        )

        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness

    MATERIALIEN[name] = mat
    return mat


def materialien_initialisieren():
    material_erstellen(
        "Schwarz",
        (0.008, 0.008, 0.008, 1),
        metallic=0.05,
        roughness=0.35,
    )

    material_erstellen(
        "Weiss",
        (0.85, 0.85, 0.85, 1),
        metallic=0.0,
        roughness=0.4,
    )

    material_erstellen(
        "Rot",
        (0.65, 0.015, 0.015, 1),
        metallic=0.0,
        roughness=0.38,
    )

    material_erstellen(
        "Hellgold",
        (0.83, 0.52, 0.08, 1),
        metallic=0.75,
        roughness=0.28,
    )

    material_erstellen(
        "Mattgold",
        # Deutlich dunkleres Bronze-Gold, damit das helle Dreieck abhebt.
        (0.40, 0.22, 0.035, 1),
        metallic=0.65,
        roughness=0.42,
    )

    material_erstellen(
        "Gold",
        (0.83, 0.55, 0.12, 1),
        metallic=0.8,
        roughness=0.25,
    )

    material_erstellen(
        "Silber",
        (0.65, 0.68, 0.72, 1),
        metallic=0.8,
        roughness=0.25,
    )


def farbe_aus_dateiname(dateiname):
    name = os.path.basename(dateiname).lower()

    if "hellgold" in name:
        return "Hellgold"

    if "mattgold" in name:
        return "Mattgold"

    if "schwarz" in name:
        return "Schwarz"

    if "weiss" in name:
        return "Weiss"

    if "rot" in name:
        return "Rot"

    if "silber" in name:
        return "Silber"

    if "gold" in name:
        return "Gold"

    return "Mattgold"


# ============================================================
# SZENE LEEREN
# ============================================================

def szene_leeren():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


# ============================================================
# STL IMPORT
# ============================================================

def stl_importieren(pfad):
    bpy.ops.object.select_all(action="DESELECT")

    bpy.ops.wm.stl_import(
        filepath=pfad
    )

    objekte = list(bpy.context.selected_objects)

    if not objekte:
        raise RuntimeError(
            f"STL konnte nicht importiert werden: {pfad}"
        )

    obj = objekte[0]

    material_name = farbe_aus_dateiname(pfad)
    material = MATERIALIEN[material_name]

    obj.data.materials.clear()
    obj.data.materials.append(material)

    obj.name = os.path.splitext(os.path.basename(pfad))[0]

    return obj


# ============================================================
# KOERPER / RAND DUENNEN
# ============================================================

def objekt_z_duennen(obj, faktor=0.98):
    """
    Verkleinert Koerper und Rand in lokaler Z-Richtung
    symmetrisch um deren geometrisches Zentrum.
    """

    name = obj.name.lower()

    if "koerper" not in name and "rand" not in name:
        return

    if not obj.data or not hasattr(obj.data, "vertices"):
        return

    if not obj.data.vertices:
        return

    z_werte = [v.co.z for v in obj.data.vertices]

    z_min = min(z_werte)
    z_max = max(z_werte)
    z_mitte = (z_min + z_max) / 2.0

    for vertex in obj.data.vertices:
        vertex.co.z = (
            z_mitte
            + (vertex.co.z - z_mitte) * faktor
        )


# ============================================================
# BOUNDING BOX
# ============================================================

def bounding_box_world(objekte):
    ecken = []

    for obj in objekte:
        for corner in obj.bound_box:
            ecken.append(
                obj.matrix_world @ Vector(corner)
            )

    if not ecken:
        return None, None

    min_v = Vector((
        min(v.x for v in ecken),
        min(v.y for v in ecken),
        min(v.z for v in ecken),
    ))

    max_v = Vector((
        max(v.x for v in ecken),
        max(v.y for v in ecken),
        max(v.z for v in ecken),
    ))

    return min_v, max_v


# ============================================================
# ANIMATION
# ============================================================

def animation_erstellen(objekte, pivot):
    """
    Datenstein auf die Kante stellen und in zehn Sekunden um Z drehen.
    """

    pivot.rotation_mode = "XYZ"
    # Die STL-Flächen liegen in XY; 90° um X stellt die Münze auf die Kante.
    pivot.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    pivot.keyframe_insert(
        data_path="rotation_euler",
        index=2,
        frame=1,
    )

    pivot.rotation_euler.z = math.radians(360.0)

    pivot.keyframe_insert(
        data_path="rotation_euler",
        index=2,
        frame=301,
    )

    if pivot.animation_data and pivot.animation_data.action:

        action = pivot.animation_data.action

        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    for fcurve in channelbag.fcurves:
                        for point in fcurve.keyframe_points:
                            point.interpolation = "LINEAR"


# ============================================================
# KAMERA
# ============================================================

def kamera_erstellen():
    camera_data = bpy.data.cameras.new("RenderCamera")
    kamera = bpy.data.objects.new("RenderCamera", camera_data)

    bpy.context.collection.objects.link(kamera)

    camera_data.type = "ORTHO"
    camera_data.clip_start = 0.01
    camera_data.clip_end = 1000.0

    return kamera


# ============================================================
# LICHT
# ============================================================

def area_light_erstellen(
    name,
    position,
    energy,
    size,
):
    light_data = bpy.data.lights.new(
        name=name,
        type="AREA",
    )

    light_data.energy = energy
    light_data.shape = "DISK"
    light_data.size = size

    light = bpy.data.objects.new(
        name=name,
        object_data=light_data,
    )

    bpy.context.collection.objects.link(light)
    light.location = position

    return light


def licht_auf_punkt_ausrichten(light, punkt):
    richtung = Vector(punkt) - light.location
    light.rotation_euler = richtung.to_track_quat(
        "-Z",
        "Y",
    ).to_euler()

def render_umgebung_erstellen(objekte):
    """
    Robuste Beleuchtung für die Produktbilder.
    SUN-Lights sind unabhängig von der Modellgröße.
    """

    # Bestehende Renderlichter entfernen
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)

    scene = bpy.context.scene

    # --------------------------------------------------------
    # Grundhelligkeit über die Welt
    # --------------------------------------------------------

    world = scene.world

    if world is None:
        world = bpy.data.worlds.new("RenderWorld")
        scene.world = world

    world.use_nodes = True

    bg = world.node_tree.nodes.get("Background")

    if bg:
        bg.inputs["Color"].default_value = (
            0.8,
            0.8,
            0.8,
            1.0,
        )

        bg.inputs["Strength"].default_value = 0.35

    # --------------------------------------------------------
    # Hauptlicht
    # --------------------------------------------------------

    licht_data = bpy.data.lights.new(
        name="Render_Sun",
        type="SUN",
    )

    licht_data.energy = 2.0
    licht_data.angle = math.radians(25.0)

    licht = bpy.data.objects.new(
        name="Render_Sun",
        object_data=licht_data,
    )

    bpy.context.collection.objects.link(licht)

    # Von vorne/oben auf das Objekt
    licht.rotation_euler = (
        math.radians(25),
        math.radians(-20),
        math.radians(-25),
    )

    # --------------------------------------------------------
    # Zweites, schwächeres Aufhelllicht
    # --------------------------------------------------------

    licht2_data = bpy.data.lights.new(
        name="Render_Fill",
        type="SUN",
    )

    licht2_data.energy = 1.2
    licht2_data.angle = math.radians(35.0)

    licht2 = bpy.data.objects.new(
        name="Render_Fill",
        object_data=licht2_data,
    )

    bpy.context.collection.objects.link(licht2)

    licht2.rotation_euler = (
        math.radians(-35),
        math.radians(25),
        math.radians(150),
    )

# ============================================================
# BILD RENDERN
# ============================================================

def bild_rendern(
    scene,
    kamera,
    objekte,
    zielpfad,
    richtung,
):
    min_v, max_v = bounding_box_world(objekte)

    if min_v is None:
        return

    mitte = (min_v + max_v) / 2.0

    breite = max_v.x - min_v.x
    hoehe = max_v.y - min_v.y

    ortho = max(breite, hoehe) * RENDER_MARGIN

    kamera.data.ortho_scale = ortho

    abstand = max(ortho * 4.0, 10.0)

    kamera.location = (
        mitte.x,
        mitte.y,
        mitte.z + richtung * abstand,
    )

    kamera.rotation_euler = (
        Vector(mitte - kamera.location)
        .to_track_quat("-Z", "Y")
        .to_euler()
    )

    scene.camera = kamera

    scene.render.resolution_x = RENDER_AUFLÖSUNG
    scene.render.resolution_y = RENDER_AUFLÖSUNG
    scene.render.resolution_percentage = 100

    scene.render.image_settings.file_format = "WEBP"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.quality = RENDER_QUALITY

    scene.render.film_transparent = RENDER_TRANSPARENT

    scene.render.filepath = zielpfad

    bpy.ops.render.render(write_still=True)


# ============================================================
# VORNE / HINTEN RENDERN
# ============================================================

def render_vorne_hinten(scene, objekte, ordner, datenstein_id):
    kamera = kamera_erstellen()

    render_umgebung_erstellen(objekte)

    # --------------------------------------------------------
    # VORNE
    #
    # Standardisierte Seite
    # --------------------------------------------------------

    vorne_pfad = os.path.join(
        ordner,
        f"{datenstein_id}_vorne.webp",
    )

    bild_rendern(
        scene,
        kamera,
        objekte,
        vorne_pfad,
        richtung=-1,
    )

    # --------------------------------------------------------
    # HINTEN
    #
    # Individuelle Seite, bei Peter mit Hut
    # --------------------------------------------------------

    hinten_pfad = os.path.join(
        ordner,
        f"{datenstein_id}_hinten.webp",
    )

    bild_rendern(
        scene,
        kamera,
        objekte,
        hinten_pfad,
        richtung=1,
    )

    bpy.data.objects.remove(
        kamera,
        do_unlink=True,
    )

# ============================================================
# GLB EXPORT
# ============================================================

def glb_exportieren(objekte, pfad, pivot=None):
    bpy.ops.object.select_all(action="DESELECT")

    export_objekte = list(objekte)
    if pivot is not None:
        export_objekte.append(pivot)

    for obj in export_objekte:
        obj.select_set(True)

    bpy.context.view_layer.objects.active = objekte[0]

    export_kwargs = {
        "filepath": pfad,
        "use_selection": True,
        "export_animations": True,
    }

    if DRACO_AKTIV:
        export_kwargs.update({
            "export_draco_mesh_compression_enable": True,
            "export_draco_mesh_compression_level": DRACO_LEVEL,
            "export_draco_position_quantization": DRACO_POSITION_QUANTISIERUNG,
            "export_draco_normal_quantization": DRACO_NORMAL_QUANTISIERUNG,
            "export_draco_texcoord_quantization": DRACO_TEXCOORD_QUANTISIERUNG,
            "export_draco_color_quantization": DRACO_FARBE_QUANTISIERUNG,
            "export_draco_generic_quantization": DRACO_GENERIC_QUANTISIERUNG,
        })

    bpy.ops.export_scene.gltf(
        export_format="GLB",
        **export_kwargs,
    )


# ============================================================
# DREIECKE ZÄHLEN
# ============================================================

def dreiecke_zaehlen(obj):
    if not obj.data:
        return 0

    mesh = obj.data

    return sum(
        len(poly.vertices) - 2
        for poly in mesh.polygons
    )


# ============================================================
# EINEN DATENSTEIN VERARBEITEN
# ============================================================

def datenstein_verarbeiten(ordner):
    datenstein_id = os.path.basename(
        os.path.normpath(ordner)
    )

    print("")
    print("=" * 70)
    print(f"Verarbeite Datenstein: {datenstein_id}")
    print(f"Ordner: {ordner}")
    print("=" * 70)

    stl_dateien = sorted(
        [
            os.path.join(ordner, datei)
            for datei in os.listdir(ordner)
            if datei.lower().endswith(".stl")
        ]
    )

    if not stl_dateien:
        print("Keine STL-Dateien gefunden.")
        return

    szene_leeren()
    materialien_initialisieren()

    objekte = []

    for stl in stl_dateien:
        print(f"Importiere: {os.path.basename(stl)}")

        obj = stl_importieren(stl)

        objekt_z_duennen(obj)

        objekte.append(obj)

    if not objekte:
        return

    # --------------------------------------------------------
    # Gemeinsamen Pivot erzeugen
    # --------------------------------------------------------

    pivot_data = bpy.data.objects.new(
        f"{datenstein_id}_Pivot",
        None,
    )

    bpy.context.collection.objects.link(pivot_data)

    min_v, max_v = bounding_box_world(objekte)
    if min_v is None:
        return

    pivot_center = (min_v + max_v) / 2.0
    pivot_data.location = pivot_center

    pivot = pivot_data

    # STL-Meshes enthalten die Geometrie bereits in Weltkoordinaten.
    # In lokale Pivot-Koordinaten verschieben, sonst exportiert glTF
    # die absoluten Vertex-Koordinaten zusätzlich zur Pivot-Translation.
    for obj in objekte:
        obj.data.transform(obj.matrix_world.copy())
        for vertex in obj.data.vertices:
            vertex.co -= pivot_center
        obj.matrix_world = Matrix.Identity(4)
        obj.parent = pivot

    animation_erstellen(
        objekte,
        pivot,
    )

    # --------------------------------------------------------
    # Szene / Render
    # --------------------------------------------------------

    scene = bpy.context.scene

    scene.frame_start = 1
    scene.frame_end = 301
    scene.render.fps = 30

    scene.frame_set(1)

    # --------------------------------------------------------
    # GLB
    # --------------------------------------------------------

    glb_pfad = os.path.join(
        ordner,
        f"{datenstein_id}.glb",
    )

    print(f"Exportiere GLB: {glb_pfad}")

    glb_exportieren(
        objekte,
        glb_pfad,
        pivot=pivot,
    )

    # --------------------------------------------------------
    # WebP
    # --------------------------------------------------------

    if RENDER_BILDER:
        print("Rendere Vorschaubilder ...")

        # Die Vorschaubilder zeigen die Flächen direkt; nur das GLB wird
        # auf die Kante gestellt animiert.
        stand_rotation = pivot.rotation_euler.copy()
        pivot.rotation_euler.x = 0.0

        render_vorne_hinten(
            scene,
            objekte,
            ordner,
            datenstein_id,
        )

        pivot.rotation_euler = stand_rotation

    # --------------------------------------------------------
    # Statistik
    # --------------------------------------------------------

    print("")
    print("Dreiecke:")

    gesamt = 0

    for obj in objekte:
        count = dreiecke_zaehlen(obj)
        gesamt += count

        print(
            f"  {obj.name}: {count:,}"
        )

    print(
        f"  GESAMT: {gesamt:,}"
    )

    print("")
    print(f"Fertig: {datenstein_id}")


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():
    print("")
    print("=" * 70)
    print("Datenstein Batch Builder")
    print("=" * 70)

    print(f"Stammordner: {STAMMORDNER}")

    if not os.path.isdir(STAMMORDNER):
        raise RuntimeError(
            f"Stammordner existiert nicht: {STAMMORDNER}"
        )

    unterordner = []

    for name in sorted(os.listdir(STAMMORDNER)):
        pfad = os.path.join(
            STAMMORDNER,
            name,
        )

        if not os.path.isdir(pfad):
            continue

        stl_dateien = [
            datei
            for datei in os.listdir(pfad)
            if datei.lower().endswith(".stl")
        ]

        if stl_dateien:
            unterordner.append(pfad)

    if not unterordner:
        print("Keine Datenstein-Ordner mit STL-Dateien gefunden.")
        return

    print("")
    print("Gefundene Datensteine:")

    for ordner in unterordner:
        print(
            f"  {os.path.basename(ordner)}"
        )

    for ordner in unterordner:
        datenstein_verarbeiten(ordner)

    print("")
    print("=" * 70)
    print("ALLE DATENSTEINE FERTIG")
    print("=" * 70)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
