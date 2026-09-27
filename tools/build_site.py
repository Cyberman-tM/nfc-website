#!/usr/bin/env python3
"""Build the static preview/site from data/database.json using only Python's stdlib."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "database.json"
TOKEN_ID = re.compile(r"^Dn[0-9A-F]{3}$")
LEGACY_ID = re.compile(r"^Dn[0-9A-F]{4}$")
# Make browser caches refresh generated CSS whenever the generator/style source changes.
ASSET_VERSION = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_page(out: Path, relative: str, title: str, description: str, body: str, *, sort_links: bool = False, token_viewer: bool = False) -> None:
    relative_path = Path(relative)
    depth = len(relative_path.parent.parts) if relative_path.parent != Path(".") else 0
    prefix = "../" * depth or "./"
    extra_scripts = []
    if sort_links:
        extra_scripts.append(f'<script src="{prefix}assets/links-sort.js" defer></script>')
    if token_viewer:
        extra_scripts.extend([
            '<script type="module" async src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.3.1/model-viewer.min.js"></script>',
            f'<script src="{prefix}assets/token-viewer.js" defer></script>',
        ])
    page = f'''<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <title>{esc(title)} · De' nagh</title>
  <link rel="icon" type="image/svg+xml" href="{prefix}assets/favicon.svg">
  <link rel="stylesheet" href="{prefix}assets/site.css?v={ASSET_VERSION}">
  {''.join(extra_scripts)}
</head>
<body>
  <a class="skip-link" href="#main">Zum Inhalt springen</a>
  <header class="site-header">
    <a class="brand" href="{prefix}index.html" aria-label="De' nagh – Startseite">
      <span class="brand-mark" aria-hidden="true"><span class="pIqaD-glyph">d</span></span>
      <span><span class="brand-name">De' nagh</span><span class="brand-caption">NFC-Datensteine</span></span>
    </a>
    <span class="header-insignia pIqaD-glyph" aria-hidden="true">dez nag</span>
    <div class="header-tools">
      <nav class="language-switch" aria-label="Sprachauswahl">
        <span lang="de" aria-current="page">DE</span>
        <span class="language-unavailable" lang="en" aria-disabled="true" title="Englische Fassung noch nicht verfügbar">EN</span>
      </nav>
      <nav class="primary-nav" aria-label="Hauptnavigation">
        <a href="{prefix}years/">Jahrgänge</a>
        <a href="{prefix}categories/">Kategorien</a>
        <a href="{prefix}links/">Linkverzeichnis</a>
      </nav>
    </div>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site-footer">
    <p>Statische Dokumentation für De' nagh · pIqaD-Schrift: <a href="https://hol.kag.org/page/piqadsupport.html">KApIqaD von Hol ’ampaS</a></p>
  </footer>
</body>
</html>
'''
    target = out / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8", newline="\n")


def category_name(db: dict, category_id: str, language: str = "de") -> str:
    category = db.get("tokenCategories", {}).get(category_id, {})
    labels = category.get("labels", {})
    return labels.get(language) or labels.get("de") or f"Kategorie {category_id}"


def localized(value: dict, language: str = "de") -> str:
    return value.get(language) or value.get("de") or ""


def short_label(token: dict) -> str:
    """Return a token's localized short label, if one is available."""
    return localized(token.get("shortLabel", {}))


def token_reference(token_id: str, token: dict) -> str:
    """Render a token link whose tooltip identifies it without repeating the label visibly."""
    label = short_label(token)
    attributes = f' title="{esc(label)}" aria-label="{esc(token_id)} – {esc(label)}"' if label else ""
    return f'<a href="../{esc(token["year"])}/{esc(token_id)}/"{attributes}>{esc(token_id)}</a>'


def copy_token_media(token_id: str, out: Path) -> dict[str, bool]:
    """Publish only the named GLB and fallback images; never copy Blender/STL sources."""
    source = ROOT / "3d" / token_id
    target = out / "media" / token_id
    files = {
        "model": f"{token_id}.glb",
        "front": f"{token_id}_vorne.webp",
        "back": f"{token_id}_hinten.webp",
    }
    found = {kind: (source / filename).is_file() for kind, filename in files.items()}
    if any(found.values()):
        target.mkdir(parents=True, exist_ok=True)
        for kind, filename in files.items():
            if found[kind]:
                shutil.copyfile(source / filename, target / filename)
    return found


def token_card(token_id: str, token: dict, context: str = "", href_target: str | None = None) -> str:
    """Render a linked visual card for a token in an index or year listing."""
    alt_texts = token.get("media", {}).get("altTexts", {})
    thumbnails = []
    for side, filename, fallback_alt, caption in (
        ("front", f"{token_id}_vorne.webp", f"Vorderseite des Datensteins {token_id}", "Vorderseite"),
        ("back", f"{token_id}_hinten.webp", f"Rückseite des Datensteins {token_id}", "Rückseite"),
    ):
        if (ROOT / "3d" / token_id / filename).is_file():
            alt = localized(alt_texts.get(side, {})) or fallback_alt
            thumbnails.append(f'<figure><img src="../media/{esc(token_id)}/{esc(filename)}" alt="{esc(alt)}" width="512" height="512"><figcaption>{caption}</figcaption></figure>')
    gallery = f'<div class="year-card-gallery">{"".join(thumbnails)}</div>' if thumbnails else ""
    context_markup = f'<span class="eyebrow">{esc(context)}</span>' if context else ""
    label = short_label(token)
    label_markup = f'<span class="year-card-short-label">{esc(label)}</span>' if label else ""
    description = localized(token.get("descriptions", {})) or "Beschreibung noch nicht eingetragen."
    target = href_target or f"../{token['year']}/{token_id}/"
    return f'''<a class="record-card year-token-card" href="{esc(target)}">
  <span class="year-card-seal"><strong>{esc(token_id)}</strong></span>
  <span class="year-card-copy">{context_markup}{label_markup}<span class="year-card-description">{esc(description)}</span></span>
  {gallery}
</a>'''


def effective_link_categories(db: dict, link_id: str, link: dict) -> list[str]:
    result = list(link.get("categories", []))
    hostname = (urlparse(link.get("url", "")).hostname or "").lower()
    for rule in db.get("categoryRules", []):
        if rule.get("appliesTo") != "link":
            continue
        condition = rule.get("condition", {})
        if condition.get("field") == "url.hostname" and hostname in [h.lower() for h in condition.get("matchesAny", [])]:
            category_id = rule.get("linkCategoryId")
            if category_id and category_id not in result:
                result.append(category_id)
    return result


def validate(db: dict) -> None:
    for token_id, token in db.get("tokens", {}).items():
        if not TOKEN_ID.fullmatch(token_id):
            raise ValueError(f"Ungültige Datenstein-ID: {token_id!r}; erwartet Dn plus drei Hex-Zeichen")
        if token.get("categoryId") not in db.get("tokenCategories", {}):
            raise ValueError(f"Unbekannte Token-Kategorie bei {token_id}: {token.get('categoryId')!r}")
        for link_id in token.get("links", []):
            if link_id not in db.get("links", {}):
                raise ValueError(f"Unbekannte Link-ID bei {token_id}: {link_id!r}")
        for legacy_id in token.get("legacyIds", []):
            if not LEGACY_ID.fullmatch(legacy_id):
                raise ValueError(f"Ungültige Legacy-ID bei {token_id}: {legacy_id!r}")


def render(out: Path, db: dict) -> None:
    validate(db)
    tokens = db.get("tokens", {})
    links = db.get("links", {})
    # Token URLs stay on each token page, but the global directory focuses on external targets.
    public_links = {
        link_id: link for link_id, link in links.items()
        if (urlparse(link.get("url", "")).hostname or "").lower() != "nfc.tlhingan.at"
    }
    years = sorted({int(token["year"]) for token in tokens.values() if token.get("year") is not None})
    token_usage: dict[str, list[tuple[str, dict]]] = {link_id: [] for link_id in links}
    for token_id, token in tokens.items():
        for link_id in token.get("links", []):
            token_usage.setdefault(link_id, []).append((token_id, token))

    token_cards = []
    for token_id, token in sorted(tokens.items()):
        label = short_label(token)
        label_markup = f'<span class="token-card-short-label">{esc(label)}</span>' if label else ""
        token_cards.append(f'''<a class="record-card" href="{esc(token['year'])}/{esc(token_id)}/">
  <span class="eyebrow">{esc(token['year'])} · {esc(category_name(db, token['categoryId']))}</span>
  <strong>{esc(token_id)}</strong>
  {label_markup}
  <span>{esc(localized(token.get('descriptions', {})) or 'Beschreibung noch nicht eingetragen.')}</span>
</a>''')
    latest_year = years[-1] if years else None
    category_counts = {category_id: sum(1 for token in tokens.values() if token.get("categoryId") == category_id) for category_id in db.get("tokenCategories", {})}
    home_year_rows = "".join(
        f'<li><a href="{year}/"><span>{year}</span><span>{sum(1 for token in tokens.values() if int(token["year"]) == year)} Datensteine <span aria-hidden="true">↗</span></span></a></li>'
        for year in reversed(years)
    )
    home_category_rows = "".join(
        f'<li><a href="categories/#category-{esc(category_id)}"><span><strong>{esc(category_id)}</strong> {esc(category_name(db, category_id))}</span><span>{count} Datensteine <span aria-hidden="true">↗</span></span></a></li>'
        for category_id, count in sorted(category_counts.items(), key=lambda item: int(item[0], 16))
    )
    home_token_rows = "".join(
        f'<li><a href="{esc(token["year"])}/{esc(token_id)}/"><span><strong>{esc(token_id)}</strong><small>{esc(short_label(token) or category_name(db, token["categoryId"]))}</small></span><span>{esc(token["year"])} <span aria-hidden="true">↗</span></span></a></li>'
        for token_id, token in sorted(tokens.items())
    )
    home_content = f'''<section class="hero">
  <p class="eyebrow">Ein kleines Verzeichnis mit langer Lebensdauer</p>
  <h1>Datensteine.<br><span>Dokumentiert für später.</span></h1>
  <div class="hero-stamp" aria-hidden="true"><span>dez</span><b>nag</b><i></i></div>
</section>
<section class="home-dashboard" aria-labelledby="overview-title">
  <div class="section-heading"><h2 id="overview-title">Bestand</h2></div>
  <div class="overview-stats">
    <a class="overview-stat" href="tokens/"><span>Datensteine</span><strong>{len(tokens)}</strong></a>
    <a class="overview-stat" href="years/"><span>Jahrgänge</span><strong>{len(years)}</strong><small>Jahrgangsseiten öffnen ↗</small></a>
    <a class="overview-stat" href="categories/"><span>Kategorien</span><strong>{len(db.get("tokenCategories", {}))}</strong><small>{sum(1 for count in category_counts.values() if count)} belegt · Übersicht ↗</small></a>
    <a class="overview-stat" href="links/"><span>Linkziele</span><strong>{len(public_links)}</strong><small>Verzeichnis öffnen ↗</small></a>
  </div>
  <div class="overview-breakdown">
    <section><div class="section-heading"><h3><a href="years/">Jahrgänge</a></h3></div><ul class="overview-list">{home_year_rows or '<li class="empty-state">Noch keine Jahrgänge eingetragen.</li>'}</ul></section>
    <section><div class="section-heading"><h3><a href="categories/">Kategorien</a></h3></div><ul class="overview-list">{home_category_rows or '<li class="empty-state">Noch keine Kategorien eingetragen.</li>'}</ul></section>
  </div>
  <section class="overview-token-section"><div class="section-heading"><h3><a href="tokens/">Datensteine</a></h3></div><ul class="overview-list" id="home-token-list">{home_token_rows or '<li class="empty-state">Noch keine Datensteine eingetragen.</li>'}</ul></section>
</section>'''
    write_page(out, "index.html", "Datensteine", "Statische Dokumentation der NFC-Datensteine De' nagh.", home_content)

    all_token_cards = []
    for token_id, token in sorted(tokens.items()):
        category_id = token["categoryId"]
        context = f"Jahrgang {token['year']} · Kategorie {category_id} · {category_name(db, category_id)}"
        all_token_cards.append(token_card(token_id, token, context))
    token_index_content = f'''<header class="page-heading tokens-page-heading"><h1>Datensteine</h1><p>Alle Datensteine, aufsteigend nach ihrer ID geordnet.</p></header>
<section class="section-block"><div class="record-grid token-index-grid">{"".join(all_token_cards) or '<p class="empty-state">Noch keine Datensteine eingetragen.</p>'}</div></section>'''
    write_page(out, "tokens/index.html", "Datensteine", "Übersicht aller Datensteine, nach ID sortiert.", token_index_content)

    # The year index lives at /years/, while each year page lives at /YYYY/.
    year_items = "".join(f'<li><a href="../{year}/"><span>{year}</span><span class="arrow" aria-hidden="true">↗</span></a></li>' for year in reversed(years))
    years_content = f'''<header class="page-heading"><p class="eyebrow">Archiv</p><h1>Jahrgänge</h1><p>Ein Jahrgang hält den Stand eines Datenstein-Zyklus fest. Bestehende Jahrgänge bleiben dauerhaft erreichbar.</p></header>
<section class="section-block"><ul class="link-list">{year_items or '<li class="empty-state">Noch keine Jahrgänge eingetragen.</li>'}</ul></section>'''
    write_page(out, "years/index.html", "Jahrgänge", "Übersicht der dokumentierten Datenstein-Jahrgänge.", years_content)

    cats = db.get("tokenCategories", {})
    category_items = []
    for category_id, category in sorted(cats.items()):
        label = category_name(db, category_id)
        member_ids = [token_id for token_id, token in tokens.items() if token.get("categoryId") == category_id]
        members = "".join(
            f'<a class="tag" href="../{esc(tokens[token_id]["year"])}/{esc(token_id)}/">{esc(token_id + (" · " + short_label(tokens[token_id]) if short_label(tokens[token_id]) else ""))}</a>'
            for token_id in sorted(member_ids)
        )
        descriptions = localized(category.get("descriptions", {})) or "Beschreibung folgt."
        category_items.append(f'''<article class="category-card" id="category-{esc(category_id)}"><div class="category-number">{esc(category_id)}</div><div class="category-copy"><p class="eyebrow">Kategorie {esc(category_id)}</p><h2>{esc(label)}</h2><p>{esc(descriptions)}</p><div class="tag-list">{members or '<span class="muted">Noch keine Datensteine</span>'}</div></div></article>''')
    categories_content = f'''<header class="page-heading categories-page-heading"><h1>Kategorien</h1><p>Die Kategorie ist das erste Zeichen der Dn-ID. Neue Kategorien können ergänzt werden, ohne bestehende Datensteine umzubenennen.</p></header>
<section class="category-grid">{''.join(category_items)}</section>
<p class="footnote">Für jede Kategorie stehen 256 zweistellige Hex-Nummern zur Verfügung.</p>'''
    write_page(out, "categories/index.html", "Kategorien", "Kategorien der NFC-Datensteine.", categories_content)

    for year in years:
        year_tokens = [(token_id, token) for token_id, token in tokens.items() if int(token["year"]) == year]
        tokens_by_category: dict[str, list[tuple[str, dict]]] = {}
        for token_id, token in year_tokens:
            tokens_by_category.setdefault(token["categoryId"], []).append((token_id, token))
        category_sections = []
        for category_id in sorted(tokens_by_category, key=lambda value: int(value, 16)):
            cards = []
            for token_id, token in sorted(tokens_by_category[category_id], key=lambda item: item[0]):
                cards.append(token_card(token_id, token, href_target=f"{token_id}/"))
            label_id = f"year-{year}-category-{category_id}"
            category_sections.append(f'''<section class="year-category" aria-labelledby="{label_id}">
  <h2 id="{label_id}"><span class="year-category-id">{esc(category_id)}</span>{esc(category_name(db, category_id))}</h2>
  <div class="record-grid">{"".join(cards)}</div>
</section>''')
        body = f'''<nav class="breadcrumbs" aria-label="Brotkrumennavigation"><a href="../years/">Jahrgänge</a><span aria-hidden="true">/</span><span aria-current="page">{year}</span></nav>
<header class="page-heading year-page-heading"><div class="year-heading-line"><h1>{year}</h1><span class="year-insignia pIqaD-glyph" aria-hidden="true">{year}</span></div><p>Dieser Jahrgang dokumentiert die Datensteine und ihre Inhalte in diesem Stand.</p></header>
<div class="year-categories">{"".join(category_sections) if category_sections else '<p class="empty-state">Für diesen Jahrgang sind noch keine Datensteine eingetragen.</p>'}</div>'''
        write_page(out, f"{year}/index.html", str(year), f"Datensteine des Jahrgangs {year}.", body)

    for token_id, token in sorted(tokens.items()):
        year = int(token["year"])
        category_id = token["categoryId"]
        media = copy_token_media(token_id, out)
        media_root = f"../../media/{token_id}"
        alt_texts = token.get("media", {}).get("altTexts", {})
        figures = []
        for side, filename, fallback_text in (
            ("front", f"{token_id}_vorne.webp", f"Vorderseite des Datensteins {token_id}"),
            ("back", f"{token_id}_hinten.webp", f"Rückseite des Datensteins {token_id}"),
        ):
            if media[side]:
                alt = localized(alt_texts.get(side, {})) or fallback_text
                caption = "Vorderseite" if side == "front" else "Rückseite"
                figures.append(f'''<figure><img src="{media_root}/{esc(filename)}" alt="{esc(alt)}" width="512" height="512"><figcaption>{caption}</figcaption></figure>''')
        fallback_gallery = "".join(figures) or '<p class="media-empty">Keine statischen Ansichten hinterlegt.</p>'
        if media["model"]:
            model_alt = localized(alt_texts.get("model", {})) or f"Interaktive 3D-Ansicht des Datensteins {token_id}; mit Maus oder Touch drehbar."
            media_content = f'''<div class="model-stage">
  <model-viewer class="data-stone-viewer" src="{media_root}/{token_id}.glb" alt="{esc(model_alt)}" camera-controls interaction-prompt="none" rotation-per-second="18deg" shadow-intensity="1" exposure="1" touch-action="pan-y" style="visibility:hidden" aria-hidden="true" inert></model-viewer>
  <div class="viewer-fallback" id="viewer-fallback">{fallback_gallery}</div>
</div>
<div class="viewer-controls viewer-controls-compact" id="viewer-controls" hidden><button class="motion-toggle" id="motion-toggle" type="button" aria-label="Animation starten" aria-pressed="false"><span class="motion-icon" aria-hidden="true"></span><span id="motion-label">Animation starten</span></button></div>
<p class="viewer-status viewer-status-compact visually-hidden" id="viewer-status" role="status" aria-live="polite">Statische Ansicht. 3D-Modell wird geladen …</p>'''
            media_content = media_content.replace('<div class="model-stage">', '<div class="model-stage model-stage-compact">')
            heading_visual = f'<div class="token-visual">{media_content}</div>'
            media_section = ""
        elif figures:
            media_content = f'<div class="viewer-fallback static-gallery">{fallback_gallery}</div>'
            media_section = f'''<section class="content-section media-section"><p class="eyebrow">Gestaltung</p><h2>Ansichten und Varianten</h2>{media_content}</section>'''
            heading_visual = ""
        else:
            media_content = '<p class="empty-state">Für diesen Datenstein ist noch keine 3D-Datei oder Bildansicht hinterlegt.</p>'
            media_section = f'''<section class="content-section media-section"><p class="eyebrow">Gestaltung</p><h2>Ansichten und Varianten</h2>{media_content}</section>'''
            heading_visual = ""
        token_links = []
        for link_id in token.get("links", []):
            link = links[link_id]
            url = link["url"]
            label = localized(link.get("descriptions", {})) or url
            token_links.append(f'<li><a href="{esc(url)}">{esc(label)}</a></li>')
        nfc_text = token.get("nfcText", {}).get("original", "")
        chip_type = token.get("chipType") or db.get("defaultChipType") or "Noch nicht angegeben"
        label = short_label(token)
        label_markup = f'<p class="token-hero-short-label">{esc(label)}</p>' if label else ""
        description = localized(token.get("descriptions", {}))
        detail = f'<p class="token-description">{esc(description)}</p>' if description else '<p class="empty-state">Die ausführliche Beschreibung für diesen Datenstein ist noch nicht eingetragen.</p>'
        nfc_block = f'<pre class="nfc-text">{esc(nfc_text)}</pre>' if nfc_text else '<p class="muted">Kein Text-Eintrag in den Quelldaten hinterlegt.</p>'
        body = f'''<nav class="breadcrumbs" aria-label="Brotkrumennavigation"><a href="../../years/">Jahrgänge</a><span aria-hidden="true">/</span><a href="../">{year}</a><span aria-hidden="true">/</span><span aria-current="page">{esc(token_id)}</span></nav>
<header class="token-heading"><div class="token-identity"><div class="token-seal"><h1>{esc(token_id)}</h1><span>{esc(category_name(db, category_id))}</span></div></div><div class="token-hero-description">{label_markup}{detail}</div>{heading_visual}</header>
<div class="token-content token-flow"><aside class="token-aside"><p class="eyebrow">Details</p><dl><dt>ID</dt><dd><code>{esc(token_id)}</code></dd><dt>Jahrgang</dt><dd><a href="../">{year}</a></dd><dt>Kategorie</dt><dd><a href="../../categories/">{esc(category_name(db, category_id))} ({esc(category_id)})</a></dd><dt>Chiptyp</dt><dd>{esc(chip_type)}</dd></dl><a class="text-link" href="../../links/">Im Linkverzeichnis ansehen <span aria-hidden="true">→</span></a></aside>
<section class="content-section nfc-section"><p class="eyebrow">Text auf dem Chip</p>{nfc_block}</section>
<section class="content-section entries-section"><p class="eyebrow">Einträge</p><ul class="resource-list">{''.join(token_links) or '<li>Keine Einträge vorhanden.</li>'}</ul></section>
{media_section}</div>'''
        write_page(out, f"{year}/{token_id}/index.html", token_id, f"Dokumentation für Datenstein {token_id}, Jahrgang {year}.", body, token_viewer=media["model"])
        for legacy_id in token.get("legacyIds", []):
            legacy_target = f"../{token_id}/"
            legacy_body = f'''<header class="page-heading"><p class="eyebrow">Frühere Adresse</p><h1>{esc(legacy_id)}</h1><p>Diese Adresse wurde früher verwendet. Der Datenstein ist jetzt unter <a href="{esc(legacy_target)}">{esc(token_id)}</a> dokumentiert.</p></header>
<p><a class="button button-primary" href="{esc(legacy_target)}">Zur gültigen Datenstein-Seite</a></p>'''
            relative = Path(str(year)) / legacy_id / "index.html"
            depth_prefix = "../../"
            target = out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            redirect = f'''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0; url={esc(legacy_target)}"><link rel="canonical" href="{esc(legacy_target)}"><title>Adresse aktualisiert · De' nagh</title><link rel="icon" type="image/svg+xml" href="{depth_prefix}assets/favicon.svg"><link rel="stylesheet" href="{depth_prefix}assets/site.css?v={ASSET_VERSION}"></head>
<body><a class="skip-link" href="#main">Zum Inhalt springen</a><main id="main" class="legacy-page">{legacy_body}</main></body></html>'''
            target.write_text(redirect, encoding="utf-8", newline="\n")

    rows = []
    for link_id, link in public_links.items():
        url = link.get("url", "")
        parsed = urlparse(url)
        uses = token_usage.get(link_id, [])
        sorted_uses = sorted(uses)
        used_tokens = ", ".join(token_id for token_id, _ in sorted_uses) or "—"
        token_links = ", ".join(token_reference(token_id, token) for token_id, token in sorted_uses) or "—"
        used_labels = ", ".join(label for _, token in sorted_uses if (label := short_label(token)))
        used_labels_markup = f'<small class="token-label-values">{esc(used_labels)}</small>' if used_labels else ""
        years_used = sorted({int(token["year"]) for _, token in uses})
        used_years = ", ".join(str(year) for year in years_used) or "—"
        year_links = ", ".join(f'<a href="../{year}/">{year}</a>' for year in years_used) or "—"
        categories_used = {
            token["categoryId"]: category_name(db, token["categoryId"])
            for _, token in uses
        }
        sorted_categories = sorted(categories_used.items(), key=lambda item: item[1].casefold())
        used_cats = [label for _, label in sorted_categories]
        category_labels = ", ".join(used_cats) or "—"
        category_links = ", ".join(
            f'<a href="../categories/#category-{esc(category_id)}">{esc(label)}</a>'
            for category_id, label in sorted_categories
        ) or "—"
        description = localized(link.get("descriptions", {})) or "Noch keine Beschreibung eingetragen."
        effective_cats = effective_link_categories(db, link_id, link)
        pills = " ".join(
            f'<a class="tag" href="categories/{esc(cat)}/">{esc(db.get("linkCategories", {}).get(cat, {}).get("labels", {}).get("de", cat))}</a>'
            for cat in effective_cats
        )
        row = f'''<tr data-token="{esc(used_tokens.lower())}" data-year="{esc(used_years)}" data-category="{esc(category_labels.lower())}">
  <td><a class="url-value" href="{esc(url)}">{esc(url)}</a>{f'<div class="tag-list">{pills}</div>' if pills else ''}</td>
  <td>{esc(description)}</td>
  <td><span class="sort-value">{token_links}</span>{used_labels_markup}</td>
  <td><span class="sort-value">{year_links}</span></td>
  <td><span class="sort-value">{category_links}</span></td>
</tr>'''
        rows.append((used_tokens.casefold(), row))
    link_rows = "".join(row for _, row in sorted(rows, key=lambda item: item[0]))
    token_word = "Datenstein" if len(tokens) == 1 else "Datensteine"
    links_content = f'''<header class="page-heading links-page-heading"><h1>Verwendete Links</h1><p>Diese Übersicht sammelt externe Ziel-URLs, die in den NFC-Datensteinen verwendet werden, und zeigt ihre Zuordnung zu Datensteinen und Jahrgängen.</p><p class="count-label">{len(public_links)} URLs · {len(tokens)} {token_word} in der Quelldatenbank</p></header>
<section class="section-block"><div class="table-wrap"><table id="links-table"><caption class="visually-hidden">Linkziele mit zugehörigen Datensteinen, Jahrgängen und Kategorien</caption><thead><tr><th scope="col">Ziel-URL</th><th scope="col">Beschreibung</th><th scope="col" data-sort-column="token" aria-sort="ascending"><span class="sortable-heading"><a href="../tokens/">Datenstein</a><span class="sort-arrows"><button class="sort-button" type="button" data-sort="token" data-direction="ascending" aria-label="Aufsteigend nach Datenstein sortieren" aria-pressed="true" hidden>▲</button><button class="sort-button" type="button" data-sort="token" data-direction="descending" aria-label="Absteigend nach Datenstein sortieren" aria-pressed="false" hidden>▼</button></span></span></th><th scope="col" data-sort-column="year"><span class="sortable-heading"><a href="../years/">Jahrgang</a><span class="sort-arrows"><button class="sort-button" type="button" data-sort="year" data-direction="ascending" aria-label="Aufsteigend nach Jahrgang sortieren" aria-pressed="false" hidden>▲</button><button class="sort-button" type="button" data-sort="year" data-direction="descending" aria-label="Absteigend nach Jahrgang sortieren" aria-pressed="false" hidden>▼</button></span></span></th><th scope="col" data-sort-column="category"><span class="sortable-heading"><a href="../categories/">Kategorie</a><span class="sort-arrows"><button class="sort-button" type="button" data-sort="category" data-direction="ascending" aria-label="Aufsteigend nach Kategorie sortieren" aria-pressed="false" hidden>▲</button><button class="sort-button" type="button" data-sort="category" data-direction="descending" aria-label="Absteigend nach Kategorie sortieren" aria-pressed="false" hidden>▼</button></span></span></th></tr></thead><tbody>{link_rows}</tbody></table></div><p class="visually-hidden" id="sort-status" aria-live="polite"></p><noscript><p class="footnote">Die Linkliste ist statisch nach Datenstein sortiert. Sortierfunktionen benötigen JavaScript.</p></noscript></section>'''
    write_page(out, "links/index.html", "Verwendete Links", "Übersicht der in NFC-Datensteinen verwendeten Linkziele.", links_content, sort_links=True)

    # Each link category has its own static, directly addressable overview.
    for category_id, category in sorted(db.get("linkCategories", {}).items()):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", category_id):
            raise ValueError(f"Link-Kategorie-ID ist nicht URL-tauglich: {category_id!r}")
        label = category.get("labels", {}).get("de") or category_id
        category_description = localized(category.get("descriptions", {}))
        members = []
        for link_id, link in public_links.items():
            if category_id not in effective_link_categories(db, link_id, link):
                continue
            uses = token_usage.get(link_id, [])
            token_refs = ", ".join(
                f'<a href="../../../{esc(token["year"])}/{esc(token_id)}/">{esc(token_id + (" · " + short_label(token) if short_label(token) else ""))}</a>'
                for token_id, token in sorted(uses)
            ) or "Noch keinem Datenstein zugeordnet."
            description = localized(link.get("descriptions", {})) or "Noch keine Beschreibung eingetragen."
            member_tags = " ".join(
                f'<a class="tag" href="../{esc(other_id)}/">{esc(db.get("linkCategories", {}).get(other_id, {}).get("labels", {}).get("de", other_id))}</a>'
                for other_id in effective_link_categories(db, link_id, link) if other_id != category_id
            )
            members.append(f'''<article class="category-link-card"><p class="eyebrow">{esc(description)}</p><h2><a href="{esc(link["url"])}">{esc(link["url"])}</a></h2><p class="category-link-meta"><strong>Verwendet in:</strong> {token_refs}</p>{f'<div class="tag-list">{member_tags}</div>' if member_tags else ''}</article>''')
        description_html = f'<p>{esc(category_description)}</p>' if category_description else ''
        category_body = f'''<nav class="breadcrumbs" aria-label="Brotkrumennavigation"><a href="../../">Linkverzeichnis</a><span aria-hidden="true">/</span><span aria-current="page">{esc(label)}</span></nav>
<header class="page-heading"><p class="eyebrow">Link-Kategorie</p><h1>{esc(label)}</h1>{description_html or '<p>Alle im Verzeichnis dieser Kategorie zugeordneten Ziele.</p>'}<p class="count-label">{len(members)} {"Link" if len(members) == 1 else "Links"}</p></header>
<section class="category-link-list">{''.join(members) if members else '<p class="empty-state">Dieser Kategorie sind noch keine Links zugeordnet.</p>'}</section>
<p class="back-link"><a class="text-link" href="../../">← Zur gesamten Linkübersicht</a></p>'''
        write_page(out, f"links/categories/{category_id}/index.html", f"Links: {label}", f"Alle Links der Kategorie {label}.", category_body)

    write_page(out, "404.html", "Seite nicht gefunden", "Die angeforderte Seite ist nicht vorhanden.", '''<header class="page-heading"><p class="eyebrow">404</p><h1>Seite nicht gefunden</h1><p>Diese Adresse ist im Verzeichnis nicht vorhanden.</p><a class="button button-primary" href="index.html">Zur Startseite</a></header>''')
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "assets" / "site.css").write_text(CSS, encoding="utf-8", newline="\n")
    (out / "assets" / "links-sort.js").write_text(JS, encoding="utf-8", newline="\n")
    (out / "assets" / "token-viewer.js").write_text(TOKEN_VIEWER_JS, encoding="utf-8", newline="\n")
    shutil.copyfile(ROOT / "tools" / "assets" / "kapiqad.woff", out / "assets" / "kapiqad.woff")
    shutil.copyfile(ROOT / "tools" / "assets" / "favicon.svg", out / "assets" / "favicon.svg")
    # Keep the published artifact independent of optional Jekyll processing on GitHub Pages.
    (out / ".nojekyll").write_text("", encoding="utf-8")


CSS = r'''@charset "utf-8";
@font-face {
  font-family: "KApIqaD";
  src: url("kapiqad.woff") format("woff");
  font-style: normal;
  font-weight: 400;
  font-display: swap;
}
:root {
  color-scheme: dark;
  --page: #151413;
  --panel: #201e1b;
  --panel-raised: #292622;
  --text: #f2eee5;
  --muted: #c4bcb0;
  --line: #51483f;
  --accent: #ff8068;
  --accent-soft: #ffb19d;
  --identity-accent: #f46855;
  --max: 72rem;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}
* { box-sizing: border-box; }
html { background: var(--page); color: var(--text); font-size: 100%; }
body { margin: 0; min-width: 18rem; background: var(--page); color: var(--text); line-height: 1.65; }
a { color: var(--accent-soft); text-decoration-thickness: .08em; text-underline-offset: .18em; }
a:hover { color: #fff; }
a:focus-visible, button:focus-visible { outline: .2rem solid #fff; outline-offset: .2rem; }
button { color: inherit; font: inherit; }
.skip-link { position: absolute; z-index: 5; top: .5rem; left: .5rem; padding: .65rem 1rem; transform: translateY(-160%); background: var(--text); color: var(--page); }
.skip-link:focus { transform: translateY(0); }
.site-header { width: min(var(--max), calc(100% - 3rem)); margin: 0 auto; min-height: 6rem; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 1rem; border-bottom: 1px solid var(--line); }
.brand { display: flex; align-items: center; gap: .8rem; text-decoration: none; color: var(--text); }
.site-header > .brand { grid-column: 1; justify-self: start; }
.header-insignia { grid-column: 2; justify-self: center; color: var(--identity-accent); font-size: clamp(2.6rem, 5vw, 3.8rem); line-height: 1; white-space: nowrap; }
.header-tools { grid-column: 3; display: flex; flex-direction: column; align-items: flex-end; gap: .35rem; }
.brand-mark { display: grid; place-items: center; width: 2.8rem; aspect-ratio: 1; border: 1px solid var(--identity-accent); color: var(--identity-accent); font-family: Georgia, serif; font-size: 1.55rem; transform: rotate(45deg); }
.brand-mark .pIqaD-glyph { transform: rotate(-45deg); }
.pIqaD-glyph { font-family: "KApIqaD", serif; font-feature-settings: "liga" 1; font-variant-ligatures: common-ligatures; }
.brand-name, .brand-caption { display: block; }
.brand-name { font-family: Georgia, "Times New Roman", serif; font-size: 1.2rem; letter-spacing: .04em; }
.brand-caption { color: var(--muted); font-size: .76rem; letter-spacing: .07em; text-transform: uppercase; }
.language-switch, .primary-nav { display: flex; flex-wrap: wrap; align-items: center; }
.language-switch { justify-content: flex-end; gap: .85rem; color: var(--text); font-size: .78rem; letter-spacing: .1em; }
.language-switch [aria-current="page"] { color: var(--accent-soft); font-weight: 700; }
.language-unavailable { color: var(--muted); opacity: .55; }
.primary-nav { justify-content: flex-end; gap: .5rem 1.6rem; }
.primary-nav a { color: var(--text); font-size: .92rem; text-decoration: none; }
.primary-nav a:hover { color: var(--accent-soft); text-decoration: underline; }
main { width: min(var(--max), calc(100% - 3rem)); min-height: 65vh; margin: 0 auto; }
.hero { position: relative; min-height: 25rem; padding: clamp(3rem, 6vw, 5.5rem) 0 3.5rem; border-bottom: 1px solid var(--line); overflow: hidden; }
.hero h1, .page-heading h1, .token-heading h1 { margin: .4rem 0 1rem; font-family: Georgia, "Times New Roman", serif; font-size: clamp(2.7rem, 7.7vw, 5.6rem); font-weight: 500; letter-spacing: -.035em; line-height: 1.04; }
.hero h1 span { color: var(--accent-soft); }
.eyebrow { margin: 0 0 .7rem; color: var(--accent-soft); font-size: .76rem; font-weight: 700; letter-spacing: .16em; line-height: 1.4; text-transform: uppercase; }
.hero-copy { max-width: 39rem; color: var(--muted); font-size: clamp(1.05rem, 2vw, 1.25rem); }
.button { display: inline-flex; align-items: center; justify-content: center; min-height: 2.9rem; padding: .62rem 1.15rem; border: 1px solid var(--accent); border-radius: .12rem; font-weight: 700; text-decoration: none; }
.button-primary { background: var(--accent); color: #21120f; }
.button-primary:hover { background: #ffc1b2; border-color: #ffc1b2; color: #21120f; }
.button-outline { color: var(--text); }
.button-outline:hover { background: var(--accent); color: #21120f; }
.text-link { font-weight: 650; }
.hero-stamp { position: absolute; right: 2%; top: 14%; width: clamp(9rem, 23vw, 17rem); aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 1px solid #796457; outline: 1px solid #796457; outline-offset: .6rem; color: var(--accent); font-family: "KApIqaD", Georgia, serif; font-feature-settings: "liga" 1; font-variant-ligatures: common-ligatures; opacity: .22; transform: rotate(22.5deg); clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); pointer-events: none; }
.hero-stamp span, .hero-stamp b { font-size: clamp(2rem, 6vw, 4.2rem); font-weight: 400; letter-spacing: normal; }
.hero-stamp span { transform: scale(1.16); }
.hero-stamp i { position: absolute; inset: .7rem; border: 1px solid currentColor; clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.intro-grid { display: grid; grid-template-columns: repeat(3, 1fr); border-bottom: 1px solid var(--line); }
.intro-grid article { padding: 2rem 1.6rem 2.1rem 0; }
.intro-grid article + article { padding-left: 1.6rem; border-left: 1px solid var(--line); }
.index { color: var(--accent); font-family: Georgia, serif; font-size: .9rem; }
h2 { font-family: Georgia, "Times New Roman", serif; font-weight: 500; line-height: 1.2; }
.intro-grid h2 { margin: .4rem 0; font-size: 1.5rem; }
.intro-grid p, .callout p, .page-heading > p:not(.eyebrow) { color: var(--muted); }
.section-block { padding: 3.2rem 0; }
.home-dashboard { padding: 2.5rem 0 4rem; }
.home-dashboard > .section-heading { margin-bottom: 1.2rem; }
.home-dashboard > .section-heading h2 { margin: .1rem 0; color: var(--identity-accent); font-size: 2.2rem; }
.overview-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .8rem; }
.overview-stat { display: flex; flex-direction: column; gap: .45rem; min-height: 8rem; padding: 1.1rem; border: 1px solid var(--line); background: var(--panel); color: var(--text); text-decoration: none; }
.overview-stat:hover { border-color: var(--accent); background: var(--panel-raised); }
.overview-stat > span { color: var(--muted); font-size: .9rem; }
.overview-stat strong { color: var(--identity-accent); font-family: Georgia, "Times New Roman", serif; font-size: 2.2rem; font-weight: 500; line-height: 1; }
.overview-stat small { margin-top: auto; color: var(--accent-soft); font-size: .78rem; }
.overview-breakdown { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3rem; margin-top: 2.8rem; }
.overview-breakdown .section-heading, .overview-token-section .section-heading { align-items: baseline; margin-bottom: .6rem; }
.overview-breakdown h3, .overview-token-section h3 { margin: 0; color: var(--identity-accent); font-family: Georgia, "Times New Roman", serif; font-size: 1.5rem; font-weight: 500; }
.overview-breakdown h3 a, .overview-token-section h3 a { color: inherit; text-decoration: none; }
.overview-breakdown h3 a:hover, .overview-token-section h3 a:hover { color: var(--accent-soft); text-decoration: underline; }
.overview-list { margin: 0; padding: 0; list-style: none; }
.overview-list li { border-bottom: 1px solid var(--line); }
.overview-token-section #home-token-list > li:last-child { border-bottom: 0; }
.overview-token-section #home-token-list { display: grid; gap: .55rem; }
.overview-token-section #home-token-list > li { border: 0; background: var(--panel); }
.overview-token-section #home-token-list > li > a { padding: .95rem 1rem; }
.overview-token-section #home-token-list > li > a:hover { background: var(--panel-raised); }
.overview-list a { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: .85rem .2rem; color: var(--text); text-decoration: none; }
.overview-list a:hover { color: var(--accent-soft); }
.overview-list a > span:last-child { color: var(--muted); font-size: .88rem; text-align: right; }
.overview-list strong { color: var(--identity-accent); }
.overview-list small { margin-left: .65rem; color: var(--muted); }
.overview-token-section { margin-top: 2.8rem; }
.section-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; margin-bottom: 1.4rem; }
.section-heading h2 { margin: .1rem 0; font-size: 2rem; }
.record-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr)); gap: 1rem; }
.record-card { min-height: 9.5rem; display: flex; flex-direction: column; align-items: flex-start; gap: .4rem; padding: 1.25rem; border: 1px solid var(--line); background: var(--panel); color: var(--text); text-decoration: none; }
.record-card:hover { border-color: var(--accent); background: var(--panel-raised); }
.record-card strong { font-family: Georgia, serif; font-size: 1.7rem; font-weight: 500; }
.record-card > span:last-child { color: var(--muted); }
.record-card .eyebrow { color: var(--accent-soft); font-size: .7rem; }
.token-card-short-label, .year-card-short-label { color: var(--identity-accent); font-weight: 650; }
.token-label-values { display: block; color: var(--muted); }
.year-token-card { display: grid; grid-template-columns: auto minmax(8rem, 1fr) auto; align-items: center; gap: 1rem; }
.year-card-seal { position: relative; display: grid; place-items: center; width: 5.5rem; aspect-ratio: 1; border: 1px solid var(--accent); color: var(--identity-accent); clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.year-card-seal::before { position: absolute; inset: .35rem; border: 1px solid var(--line); content: ""; clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.year-card-seal strong { position: relative; z-index: 1; font-family: Georgia, "Times New Roman", serif; font-size: 1.25rem; font-weight: 500; letter-spacing: -.04em; }
.year-card-copy { display: flex; min-width: 0; flex-direction: column; align-items: flex-start; gap: .45rem; }
.year-card-description { color: var(--muted); }
.year-categories { padding: 2.4rem 0 3.5rem; }
.year-category + .year-category { margin-top: 2.7rem; }
.year-category > h2 { display: flex; align-items: baseline; gap: .8rem; margin: 0 0 1rem; font-size: 1.7rem; }
.year-category-id { color: var(--identity-accent); font-family: system-ui, sans-serif; font-size: 1.5em; }
.year-page-heading h1 { margin: 0; color: var(--identity-accent); font-size: clamp(3.5rem, 8vw, 5.6rem); }
.page-heading.year-page-heading { padding-top: 1.75rem; }
.year-heading-line { display: flex; align-items: center; justify-content: space-between; gap: 2rem; }
.year-insignia { color: var(--identity-accent); font-size: clamp(3.5rem, 8vw, 5.6rem); line-height: 1; white-space: nowrap; }
.year-page-heading > p { margin-top: 1.2rem; }
.year-card-gallery { display: flex; align-items: center; gap: .6rem; }
.year-card-gallery figure { width: 5.6rem; margin: 0; text-align: center; }
.year-card-gallery img { display: block; width: 100%; height: auto; aspect-ratio: 1; object-fit: contain; }
.year-card-gallery figcaption { color: var(--muted); font-size: .68rem; }
.year-categories .record-grid, .token-index-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 31rem), 1fr)); }
.callout { display: flex; align-items: center; justify-content: space-between; gap: 2rem; margin: .8rem 0 4rem; padding: 2rem; border: 1px solid var(--line); background: var(--panel); }
.callout h2 { margin: .2rem 0 .5rem; font-size: 1.8rem; }
.callout p { max-width: 39rem; margin: .2rem 0; }
.callout .button { flex-shrink: 0; }
.page-heading { padding: 4rem 0 2rem; border-bottom: 1px solid var(--line); }
.page-heading h1 { font-size: clamp(2.5rem, 6vw, 4.4rem); }
.categories-page-heading h1 { color: var(--identity-accent); }
.links-page-heading h1 { color: var(--identity-accent); }
.tokens-page-heading h1 { color: var(--identity-accent); }
.page-heading > p:not(.eyebrow) { max-width: 49rem; font-size: 1.1rem; }
.link-list { margin: 0; padding: 0; list-style: none; }
.link-list li { border-bottom: 1px solid var(--line); }
.link-list a { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1.2rem .2rem; color: var(--text); font-family: Georgia, serif; font-size: 1.4rem; text-decoration: none; }
.link-list a:hover { color: var(--accent-soft); }
.arrow { color: var(--accent); }
.category-grid { display: grid; gap: 1rem; padding: 2rem 0; }
.category-card { display: grid; grid-template-columns: 5rem 1fr; gap: 1.25rem; padding: 1.5rem; border: 1px solid var(--line); background: var(--panel); }
.category-number { display: grid; place-items: center; align-self: start; aspect-ratio: 1; border: 1px solid var(--accent); color: var(--accent); font-family: Georgia, serif; font-size: 2rem; }
.category-copy h2 { margin: 0; font-size: 1.8rem; }
.category-copy > p:not(.eyebrow) { color: var(--muted); }
.category-link-list { display: grid; gap: 1rem; padding: 2rem 0 1rem; }
.category-link-card { padding: 1.35rem; border: 1px solid var(--line); background: var(--panel); }
.category-link-card h2 { margin: .25rem 0 .8rem; font-family: system-ui, sans-serif; font-size: 1.05rem; font-weight: 600; overflow-wrap: anywhere; }
.category-link-card .eyebrow { color: var(--muted); font-size: .9rem; font-weight: 400; letter-spacing: 0; text-transform: none; }
.category-link-meta { color: var(--muted); }
.back-link { margin: 0 0 3rem; }
.tag-list { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .8rem; }
.tag { display: inline-block; padding: .12rem .55rem; border: 1px solid var(--line); border-radius: 99rem; color: var(--text); font-family: system-ui, sans-serif; font-size: .8rem; text-decoration: none; }
.tag:hover { border-color: var(--accent); }
.footnote, .muted { color: var(--muted); font-size: .9rem; }
.count-label { color: var(--accent-soft) !important; font-size: .9rem !important; }
.breadcrumbs { display: flex; flex-wrap: wrap; gap: .55rem; padding-top: 1.5rem; color: var(--muted); font-size: .9rem; }
.breadcrumbs a { color: var(--muted); }
.token-heading { position: relative; display: grid; grid-template-columns: auto minmax(12rem, 1fr) auto; align-items: center; gap: clamp(1.5rem, 4vw, 3rem); padding: 2rem 0 4rem; border-bottom: 0; }
.token-heading::after { position: absolute; right: 0; bottom: 0; left: 0; height: 1px; background: var(--line); content: ""; }
.token-heading h1 { margin-bottom: .3rem; font-size: clamp(3.2rem, 9vw, 6rem); }
.token-heading .lead { margin: .4rem 0 0; color: var(--muted); font-size: 1.2rem; }
.token-hero-description { width: 100%; color: var(--text); font-size: 1.08rem; line-height: 1.65; text-align: center; }
.token-hero-short-label { margin: 0 0 .45rem; color: var(--identity-accent); font-family: Georgia, "Times New Roman", serif; font-size: 1.2rem; }
.token-description { margin: 0; }
.token-hero-description .empty-state { padding: 0; border: 0; color: var(--muted); background: transparent; }
.token-seal { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; width: clamp(7rem, 20vw, 10.8rem); aspect-ratio: 1; flex: 0 0 auto; border: 1px solid var(--accent); color: var(--accent-soft); clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.token-seal::before { position: absolute; inset: .45rem; border: 1px solid var(--line); content: ""; clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.token-seal h1 { position: relative; z-index: 1; margin: 0 0 .25rem; color: var(--identity-accent); font-family: Georgia, "Times New Roman", serif; font-size: clamp(1.7rem, 4vw, 2.35rem); font-weight: 500; letter-spacing: -.04em; line-height: 1; }
.token-seal span { position: relative; z-index: 1; color: var(--muted); font-size: .78rem; letter-spacing: .04em; }
.token-visual { position: relative; width: clamp(7rem, 20vw, 11rem); flex: 0 0 auto; }
.token-content { padding-bottom: 4rem; }
.token-flow { display: flow-root; margin-top: 1.25rem; }
.token-flow > .token-aside { float: right; width: min(19rem, 36%); margin: 1.7rem 0 1.5rem 3rem; }
.token-flow .nfc-section { padding-bottom: .5rem; border-bottom: 0; }
.token-flow .nfc-section > .eyebrow, .token-flow .entries-section > .eyebrow { color: var(--identity-accent); }
.token-aside > .eyebrow { color: var(--identity-accent); }
.token-flow .nfc-text { width: calc(100% - 22rem); }
.token-flow .entries-section { padding-top: 1rem; border-bottom: 0; }
.token-flow .resource-list { display: block; }
.token-flow .resource-list li { margin: .4rem 0; }
.token-flow .media-section { clear: both; }
.token-content .eyebrow { font-size: .88rem; letter-spacing: .13em; }
.content-section { padding: 1.7rem 0; border-bottom: 1px solid var(--line); }
.content-section h2 { margin: 0 0 .8rem; font-size: 1.7rem; }
.content-section .empty-state { max-width: 42rem; }
.resource-list { display: grid; gap: .4rem; margin: 0; padding-left: 1.25rem; }
.resource-list li { overflow-wrap: anywhere; padding: .2rem 0; }
.nfc-text { overflow-wrap: anywhere; white-space: pre-wrap; padding: 1rem; border-left: .2rem solid var(--accent); background: var(--panel); color: var(--text); font: inherit; }
.media-section { min-width: 0; }
.model-stage { display: grid; width: 100%; height: min(68vh, 40rem); min-height: 19rem; background: radial-gradient(ellipse at center, #34302a 0%, #24211e 58%, var(--panel) 100%); }
.model-stage-compact { height: auto; aspect-ratio: 1; min-height: 0; background: transparent; }
.model-stage-compact .data-stone-viewer, .model-stage-compact .viewer-fallback { transform: scale(1.15); }
.data-stone-viewer, .viewer-fallback { grid-area: 1 / 1; width: 100%; height: 100%; min-width: 0; }
.data-stone-viewer { background: transparent; }
.data-stone-viewer[hidden] { display: none; }
.viewer-fallback { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; align-content: center; padding: .75rem; }
.viewer-fallback[hidden] { display: none; }
.viewer-fallback figure { display: flex; flex-direction: column; min-width: 0; min-height: 0; margin: 0; }
.viewer-fallback img { display: block; width: 100%; height: 100%; min-height: 0; flex: 1; object-fit: contain; }
.viewer-fallback figcaption { padding: .45rem; color: var(--muted); text-align: center; }
.media-empty { align-self: center; justify-self: center; color: var(--muted); }
.viewer-controls { margin-top: .8rem; }
.viewer-controls[hidden] { display: none; }
.viewer-controls-compact { display: flex; justify-content: center; margin-top: .1rem; }
.token-visual .viewer-controls-compact { position: absolute; top: calc(100% + .1rem); left: 50%; width: max-content; margin-top: 0; transform: translateX(-50%); }
.motion-toggle { display: inline-flex; align-items: center; gap: .4rem; min-height: 2rem; padding: .15rem .3rem; border: 0; background: transparent; color: var(--muted); cursor: pointer; font-size: .8rem; }
.motion-toggle:hover { color: var(--text); }
.motion-icon { position: relative; display: grid; width: 1.8rem; aspect-ratio: 1; place-items: center; flex: 0 0 auto; background: var(--accent); clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.motion-icon::before { position: absolute; inset: 1px; background: var(--page); content: ""; clip-path: polygon(30% 0,70% 0,100% 30%,100% 70%,70% 100%,30% 100%,0 70%,0 30%); }
.motion-icon::after { z-index: 1; width: .56rem; height: .7rem; background: linear-gradient(to right, var(--accent-soft) 0 .2rem, transparent .2rem .36rem, var(--accent-soft) .36rem 100%); content: ""; }
.motion-toggle[aria-pressed="false"] .motion-icon::after { width: .65rem; height: .78rem; background: var(--accent-soft); clip-path: polygon(0 0,100% 50%,0 100%); }
.viewer-status { min-height: 1.5rem; color: var(--muted); font-size: .88rem; }
.static-gallery { height: min(68vh, 40rem); min-height: 19rem; }
.token-aside { align-self: start; padding: 1.3rem; border: 1px solid var(--line); background: var(--panel); }
.token-aside dl { margin: 1rem 0 1.4rem; }
.token-aside dt { margin-top: .8rem; color: var(--muted); font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; }
.token-aside dd { margin: .1rem 0; overflow-wrap: anywhere; }
.table-wrap { width: 100%; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; }
caption { padding: 0 0 .8rem; color: var(--muted); text-align: left; }
th, td { padding: .9rem .7rem; border-bottom: 1px solid var(--line); vertical-align: top; }
th { color: var(--accent-soft); font-size: 1.08rem; }
td { overflow-wrap: anywhere; }
.url-value { word-break: break-word; }
.sortable-heading { display: flex; align-items: center; gap: .45rem; white-space: nowrap; }
.sort-arrows { display: inline-flex; align-items: center; gap: .1rem; }
.sort-button { display: inline-grid; place-items: center; width: 1.15em; height: 1.15em; padding: 0; border: 0; background: transparent; color: var(--muted); font: inherit; font-size: .85em; line-height: 1; cursor: pointer; }
.sort-button[hidden] { display: none; }
.sort-button[aria-pressed="true"] { color: var(--identity-accent); }
.sort-button:hover { color: #fff; }
.empty-state { padding: 1rem; border-left: .2rem solid var(--line); color: var(--muted); background: var(--panel); }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; clip-path: inset(50%); }
.site-footer { width: min(var(--max), calc(100% - 3rem)); margin: 0 auto; padding: 1.5rem 0 2rem; border-top: 1px solid var(--line); color: var(--muted); font-size: .88rem; }
.site-footer p { margin: 0; }
@media (max-width: 48rem) {
  .site-header { width: min(var(--max), calc(100% - 2rem)); grid-template-columns: 1fr auto; gap: .8rem; padding: .8rem 0; }
  .header-insignia { display: none; }
  .header-tools { grid-column: 2; align-items: flex-end; gap: .35rem; }
  .primary-nav { justify-content: flex-end; gap: .3rem 1rem; }
  .language-switch { justify-content: flex-end; }
  main, .site-footer { width: min(var(--max), calc(100% - 2rem)); }
  .hero { min-height: 0; padding: 3rem 0 3rem; }
  .hero-stamp { right: .5rem; top: 13%; width: 7rem; opacity: .12; }
  .overview-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .overview-breakdown { gap: 1.5rem; }
  .intro-grid { grid-template-columns: 1fr; }
  .intro-grid article, .intro-grid article + article { padding: 1.3rem 0; border-left: 0; }
  .intro-grid article + article { border-top: 1px solid var(--line); }
  .callout { align-items: flex-start; flex-direction: column; padding: 1.4rem; }
  .token-flow { margin-top: 1.25rem; padding-bottom: 2rem; }
  .token-flow > .token-aside { float: none; width: 100%; margin: 0 0 1.2rem; }
  .token-flow .nfc-text { width: 100%; }
  .token-flow .nfc-section { padding-top: 0; }
  .category-card { grid-template-columns: 3.6rem 1fr; gap: .9rem; padding: 1rem; }
  .category-number { font-size: 1.5rem; }
  .year-token-card { grid-template-columns: auto minmax(0, 1fr); }
  .year-card-gallery { grid-column: 1 / -1; justify-content: flex-end; }
  .year-insignia { display: none; }
}
@media (max-width: 36rem) {
  .site-header { grid-template-columns: 1fr; }
  .header-tools { grid-column: 1; align-items: flex-start; }
  .primary-nav, .language-switch { justify-content: flex-start; }
  .hero-stamp { display: none; }
  .overview-breakdown { grid-template-columns: 1fr; gap: 2rem; }
  .hero h1 { font-size: clamp(2.6rem, 13vw, 4rem); }
  .section-heading { align-items: flex-start; flex-direction: column; }
  .token-heading { grid-template-columns: auto auto; grid-template-areas: "identity visual" "description description"; align-items: start; justify-content: center; gap: 1rem clamp(1rem, 8vw, 3rem); padding-bottom: 2.5rem; }
  .token-heading::after { bottom: 1.25rem; }
  .token-summary-grid { margin-top: 0; }
  .token-identity { grid-area: identity; }
  .token-visual { grid-area: visual; }
  .token-hero-description { grid-area: description; margin: 0 auto; }
  .token-visual .viewer-controls-compact { position: static; width: auto; margin-top: .1rem; transform: none; }
  .token-seal { width: 5.3rem; }
  .token-seal h1 { font-size: 1.2rem; }
  .token-seal span { font-size: .62rem; }
  .token-visual { width: 5.5rem; }
  .model-stage, .static-gallery { height: 31rem; min-height: 0; }
  .model-stage-compact { height: auto; aspect-ratio: 1; }
  .motion-toggle { gap: .15rem; font-size: .65rem; }
  .viewer-fallback { grid-template-columns: 1fr; gap: .35rem; padding: .4rem; }
  .viewer-fallback figure { min-height: 0; }
  .viewer-fallback figcaption { padding: .15rem; }
  table { min-width: 48rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; }
}
'''


JS = r'''"use strict";
(function () {
  const table = document.getElementById("links-table");
  if (!table) return;
  const tbody = table.tBodies[0];
  const status = document.getElementById("sort-status");
  const labels = { token: "Datenstein", year: "Jahrgang", category: "Kategorie" };
  const buttons = Array.from(table.querySelectorAll(".sort-button[data-sort]"));

  function sortBy(key, direction, announce) {
    const rows = Array.from(tbody.rows);
    rows.sort((left, right) => {
      let a = left.dataset[key] || "";
      let b = right.dataset[key] || "";
      if (key === "year") {
        a = Number.parseInt(a, 10) || 0;
        b = Number.parseInt(b, 10) || 0;
        return direction === "ascending" ? a - b : b - a;
      }
      const compared = a.localeCompare(b, "de", { numeric: true, sensitivity: "base" });
      return direction === "ascending" ? compared : -compared;
    });
    rows.forEach((row) => tbody.appendChild(row));
    buttons.forEach((button) => {
      const active = button.dataset.sort === key && button.dataset.direction === direction;
      button.setAttribute("aria-pressed", String(active));
      button.hidden = false;
    });
    table.querySelectorAll("[data-sort-column]").forEach((heading) => {
      if (heading.dataset.sortColumn === key) heading.setAttribute("aria-sort", direction);
      else heading.removeAttribute("aria-sort");
    });
    if (announce) {
      status.textContent = `Linkliste sortiert nach ${labels[key]}, ${direction === "ascending" ? "aufsteigend (niedrigster Wert zuerst)" : "absteigend (höchster Wert zuerst)"}.`;
    }
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => sortBy(button.dataset.sort, button.dataset.direction, true));
  });
  sortBy("token", "ascending", false);
})();
'''


TOKEN_VIEWER_JS = r'''"use strict";
(function () {
  const viewer = document.querySelector(".data-stone-viewer");
  if (!viewer) return;
  const fallback = document.getElementById("viewer-fallback");
  const controls = document.getElementById("viewer-controls");
  const toggle = document.getElementById("motion-toggle");
  const motionLabel = document.getElementById("motion-label");
  const status = document.getElementById("viewer-status");
  const fallbackMessage = "3D-Ansicht nicht verfügbar. Vorder- und Rückseite werden als Bilder angezeigt.";
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let settled = false;
  let moving = false;
  let hasEmbeddedAnimation = false;

  function setMotion(enabled) {
    moving = enabled;
    if (hasEmbeddedAnimation) {
      if (enabled) viewer.play();
      else viewer.pause();
    } else if (enabled) viewer.setAttribute("auto-rotate", "");
    else viewer.removeAttribute("auto-rotate");
    toggle.setAttribute("aria-pressed", String(enabled));
    const noun = hasEmbeddedAnimation ? "Animation" : "Drehung";
    const action = enabled ? "pausieren" : "starten";
    toggle.setAttribute("aria-label", `${noun} ${action}`);
    motionLabel.textContent = `${noun} ${action}`;
  }

  function showFallback() {
    viewer.hidden = true;
    viewer.removeAttribute("aria-hidden");
    viewer.inert = true;
    fallback.hidden = false;
    status.textContent = fallbackMessage;
  }

  const timer = window.setTimeout(() => {
    if (!settled) showFallback();
  }, 15000);

  viewer.addEventListener("load", () => {
    settled = true;
    window.clearTimeout(timer);
    viewer.hidden = false;
    viewer.style.visibility = "visible";
    viewer.removeAttribute("aria-hidden");
    viewer.inert = false;
    fallback.hidden = true;
    controls.hidden = false;
    hasEmbeddedAnimation = viewer.availableAnimations.length > 0;
    if (hasEmbeddedAnimation) {
      viewer.animationName = viewer.availableAnimations[0];
      if (!reducedMotion) viewer.setAttribute("autoplay", "");
      setMotion(!reducedMotion);
      status.textContent = reducedMotion
        ? "3D-Modell geladen. Die Modellanimation ist zunächst pausiert."
        : "3D-Modell geladen. Die Animation lässt sich pausieren; das Modell kann zusätzlich mit Maus oder Touch gedreht und gezoomt werden.";
    } else {
      setMotion(!reducedMotion);
      status.textContent = reducedMotion
        ? "3D-Modell geladen. Bewegungen sind zunächst pausiert."
        : "3D-Modell geladen. Mit Maus oder Touch drehen und zoomen. Die automatische Drehung lässt sich pausieren.";
    }
  });

  viewer.addEventListener("error", () => {
    settled = true;
    window.clearTimeout(timer);
    showFallback();
  });

  toggle.addEventListener("click", () => setMotion(!moving));
})();
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Erzeugt die statische NFC-Website.")
    parser.add_argument("--out", type=Path, default=ROOT / "site", help="Ausgabeordner (Standard: site/)")
    args = parser.parse_args()
    db = json.loads(DATABASE.read_text(encoding="utf-8"))
    out = args.out if args.out.is_absolute() else ROOT / args.out
    render(out, db)
    print(f"Statische Website erzeugt in {out}")


if __name__ == "__main__":
    main()
