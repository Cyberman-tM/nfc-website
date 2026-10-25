#!/usr/bin/env python3
"""Preview and import prepared token folders into the website database."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from build_site import validate


ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "prepare" / "incoming"
DATABASE = ROOT / "content" / "database.json"
TOKEN_ARCHIVE = ROOT / "content" / "token_archive"
MEDIA = ROOT / "content" / "media"
TOKEN_ID = re.compile(r"^Dn[0-9A-F]{3}$")
EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+(?![\w.-])")
URL = re.compile(r"https?://[^\s<>\"']+|(?:www\.)?[\w.-]+\.[A-Za-z]{2,}(?:/[^\s<>\"']*)?")
EMAIL_PLACEHOLDER = "[E-Mail-Adresse entfernt]"


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON kann nicht gelesen werden: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON muss ein Objekt sein: {path}")
    return value


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def collect_strings(value: object, path: str = "") -> list[tuple[str, str, bool]]:
    found: list[tuple[str, str, bool]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            explicit = "email" in str(key).lower() or "e-mail" in str(key).lower()
            if isinstance(child, str) and explicit and child.strip():
                found.append((child_path, child, True))
            else:
                found.extend(collect_strings(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(collect_strings(child, f"{path}[{index}]"))
    elif isinstance(value, str) and EMAIL.search(value):
        found.append((path or "Text", value, False))
    return found


def redact(value: object) -> object:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if ("email" in str(key).lower() or "e-mail" in str(key).lower()) and isinstance(child, str) and child.strip():
                result[key] = "E-Mail-Adresse vorhanden"
            else:
                result[key] = redact(child)
        return result
    if isinstance(value, list):
        return [redact(child) for child in value]
    if isinstance(value, str):
        return EMAIL.sub(EMAIL_PLACEHOLDER, value)
    return value


def redact_nfctools(export: dict) -> dict:
    """Sanitize text and clear byte payloads for records containing an address."""
    result = copy.deepcopy(export)
    records = result.get("data", [])
    if not isinstance(records, list):
        return redact(result)
    for record in records:
        if not isinstance(record, dict):
            continue
        record_text = " ".join(raw_record_strings(record))
        has_explicit_email = any(explicit for _, _, explicit in collect_strings(record))
        if EMAIL.search(record_text) or has_explicit_email:
            record["kRecordObject"] = record.get("kRecordObject", {})
            if isinstance(record["kRecordObject"], dict):
                record["kRecordObject"]["kPayload"] = []
            record["kRecordSize"] = 0
    return redact(result)


def raw_record_strings(value: object) -> list[str]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"kRecordDescription", "kRecordField1", "kRecordField2"} and isinstance(child, str):
                strings.append(child)
            strings.extend(raw_record_strings(child))
    elif isinstance(value, list):
        if value and all(isinstance(item, int) and 0 <= item <= 255 for item in value):
            strings.append(bytes(value).decode("utf-8", errors="ignore"))
        else:
            for child in value:
                strings.extend(raw_record_strings(child))
    return strings


def nfc_urls(export: dict | None) -> list[str]:
    if not export:
        return []
    urls: list[str] = []
    records = export.get("data", [])
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        # Plain text records may contain email addresses that resemble URLs;
        # only URI records should contribute links from an NFC export.
        if record.get("kRecordSelection") == 0:
            continue
        if any(EMAIL.search(text) for text in raw_record_strings(record)):
            continue
        description = record.get("kRecordDescription", "")
        field1 = record.get("kRecordField1", "")
        field2 = record.get("kRecordField2", "")
        candidates = [description]
        if field2:
            candidates.append(field2 if "://" in field2 else (f"{field1}{field2}" if field1 else field2))
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            for match in URL.findall(candidate):
                candidate_url = match.rstrip(".,;:!?)]")
                parsed = urlparse(candidate_url if "://" in candidate_url else "https://" + candidate_url)
                if parsed.hostname and "." in parsed.hostname:
                    normalized = parsed.geturl()
                    if normalized not in urls:
                        urls.append(normalized)
    return urls


def link_id_for(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "link").lower().removeprefix("www.")
    slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")[:30] or "link"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"auto-{slug}-{digest}"


def find_link_id(db: dict, url: str) -> str | None:
    for link_id, link in db.get("links", {}).items():
        if url in {link.get("url"), link.get("legacyUrl")}:
            return link_id
    return None


def prepare(token_id: str, folder: Path, db: dict) -> tuple[dict, dict | None, list[tuple[str, str, bool]], list[str]]:
    if not TOKEN_ID.fullmatch(token_id):
        raise ValueError(f"Ungültige Datenstein-ID {token_id!r}; erwartet Dn plus drei Hex-Zeichen.")
    token_path = folder / "token_info.json"
    export_path = folder / f"{token_id}.json"
    export = load_json(export_path) if export_path.is_file() else None
    if token_path.is_file():
        token = load_json(token_path)
    elif export is not None and token_id in db.get("tokens", {}):
        # An NFC-only refresh updates the tag text and links while retaining
        # editorial fields and existing designs from the published entry.
        token = copy.deepcopy(db["tokens"][token_id])
        records = export.get("data", [])
        text_records = [record for record in records if isinstance(record, dict) and record.get("kRecordSelection") == 0]
        if text_records:
            record = text_records[0]
            original = record.get("kRecordField1") or record.get("kRecordDescription")
            if isinstance(original, str):
                token.setdefault("nfcText", {})["original"] = original
    elif export is not None and any((folder / f"Design{number:02d}").is_dir() for number in range(1, 100)):
        # A complete NFC export and prepared designs are enough to register a
        # new token with neutral editorial defaults; metadata can be refined later.
        design_ids = sorted(
            (path.name for path in folder.iterdir() if path.is_dir() and re.fullmatch(r"Design\d+", path.name)),
            key=lambda value: int(value.removeprefix("Design")),
        )
        if not design_ids:
            raise ValueError(f"Keine Design-Ordner in {folder} gefunden.")
        records = export.get("data", [])
        text_records = [record for record in records if isinstance(record, dict) and record.get("kRecordSelection") == 0]
        original = ""
        language = "de"
        if text_records:
            record = text_records[0]
            original = record.get("kRecordField1") or record.get("kRecordDescription") or ""
            payload = record.get("kRecordObject", {}).get("kPayload", [])
            if isinstance(payload, list) and payload and isinstance(payload[0], int) and 0 < payload[0] <= len(payload) - 1:
                try:
                    language = bytes(payload[1:1 + payload[0]]).decode("ascii") or language
                except (ValueError, UnicodeDecodeError):
                    pass
        token = {
            "year": 2026,
            "categoryId": "0" if "0" in db.get("tokenCategories", {}) else next(iter(db.get("tokenCategories", {})), None),
            "designs": [{"id": design_id, "name": f"Design {index}"} for index, design_id in enumerate(design_ids, start=1)],
            "nfcText": {"originalLanguage": language, "original": original, "descriptions": {}},
            "descriptions": {},
            "links": [],
        }
        if db.get("defaultChipType"):
            token["chipType"] = db["defaultChipType"]
        if token["categoryId"] is None:
            raise ValueError("Keine Token-Kategorie in der Datenbank definiert.")
    else:
        raise ValueError(f"Eingabedatei fehlt: {token_path}; für einen neuen NFC-only-Import werden {export_path} und mindestens ein Design-Ordner benötigt.")
    sensitive = collect_strings(token)
    if export:
        sensitive.extend(collect_strings(export))
        for text in raw_record_strings(export):
            if EMAIL.search(text):
                sensitive.append(("NFCTools-Datensatz", text, False))
    sanitized = redact(token)
    links = db.setdefault("links", {})
    token_links = []
    link_values = sanitized.get("links", [])
    if not isinstance(link_values, list):
        raise ValueError("token_info.json: 'links' muss eine Liste sein.")
    extracted_urls = [EMAIL.sub(EMAIL_PLACEHOLDER, url) for url in nfc_urls(export)]
    if not token_path.is_file() and export is not None:
        # The export is the complete source of tag links for this refresh.
        sanitized["links"] = []
    nfc_text = sanitized.get("nfcText", {}).get("original", "")
    if isinstance(nfc_text, str):
        for match in URL.findall(EMAIL.sub("", nfc_text)):
            url = match.rstrip(".,;:!?)]")
            if "://" not in url:
                url = "https://" + url
            if url not in extracted_urls:
                extracted_urls.append(url)
    for value in link_values:
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            if value not in extracted_urls:
                extracted_urls.append(value)
        elif not isinstance(value, str) or value not in links:
            raise ValueError(f"Unbekannte Link-ID {value!r}. Verwende eine bestehende Link-ID oder gib den Link als URL an.")
        elif value not in token_links:
            token_links.append(value)
    for url in extracted_urls:
        link_id = find_link_id(db, url)
        if link_id is None:
            link_id = link_id_for(url)
            links.setdefault(link_id, {"url": url, "categories": [], "descriptions": {}})
        if link_id not in token_links:
            token_links.append(link_id)
    sanitized["links"] = token_links
    return sanitized, redact_nfctools(export) if export else None, sensitive, extracted_urls


def media_files(folder: Path) -> list[tuple[Path, Path]]:
    result = []
    for design_folder in sorted(folder.iterdir()):
        if not design_folder.is_dir() or not re.fullmatch(r"Design\d+", design_folder.name):
            continue
        for source in sorted(design_folder.iterdir()):
            if source.is_file() and source.suffix.lower() in {".stl", ".glb", ".webp"}:
                result.append((source, MEDIA / folder.name / design_folder.name / source.name))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Vorschau oder Übernahme vorbereiteter Datensteine.")
    parser.add_argument("token_id", help="Datenstein-ID, zum Beispiel DnF04")
    parser.add_argument("--apply", action="store_true", help="Änderungen nach Vorschau und Bestätigung übernehmen")
    args = parser.parse_args()

    folder = INCOMING / args.token_id
    try:
        db = load_json(DATABASE)
        original_db = copy.deepcopy(db)
        token, export, sensitive, urls = prepare(args.token_id, folder, db)
        old = original_db.get("tokens", {}).get(args.token_id)
        candidate_db = copy.deepcopy(db)
        candidate_db.setdefault("tokens", {})[args.token_id] = token
        validate(candidate_db)
        changed = old != token
        print(f"Datenstein: {args.token_id} ({'wird aktualisiert' if old else 'neu'})")
        if changed:
            old_fields = old or {}
            for key in sorted(set(old_fields) | set(token)):
                if old_fields.get(key) != token.get(key):
                    kind = "neu" if key not in old_fields else ("entfernt" if key not in token else "geändert")
                    print(f"  Token-Feld {kind}: {key}")
        else:
            print("Token-Daten: unverändert")
        for link_id in sorted(set(db.get("links", {})) - set(original_db.get("links", {}))):
            print(f"  Neue Linkdefinition: {link_id} → {db['links'][link_id]['url']}")
        for url in urls:
            print(f"  Eingabe-Link: {url}")
        if export is not None:
            archive = TOKEN_ARCHIVE / f"{args.token_id}.json"
            archived_text = canonical(load_json(archive)) if archive.exists() else None
            export_text = canonical(export)
            archive_state = "neu" if archived_text is None else ("geändert" if archived_text != export_text else "unverändert")
            print(f"  NFCTools-Archiv {archive_state}: {archive.relative_to(ROOT)}")
        files = media_files(folder)
        for source, target in files:
            state = "neu" if not target.exists() else ("geändert" if source.read_bytes() != target.read_bytes() else "unverändert")
            print(f"  Datei {state}: {source.relative_to(ROOT)} → {target.relative_to(ROOT)}")
        if sensitive:
            print("\nMögliche E-Mail-Adresse(n) gefunden:")
            for path, _, explicit in sensitive:
                print(f"  {path}{' (explizites E-Mail-Feld)' if explicit else ''}")
            print(f"Öffentliche Ausgabe wird auf einen Platzhalter reduziert: {EMAIL_PLACEHOLDER}")
        if not args.apply:
            print("\nNur Vorschau. Für die Übernahme denselben Befehl mit --apply wiederholen.")
            return 0
        if sensitive:
            answer = input("Die erkannte Adresse darf als generischer Platzhalter übernommen werden? [j/N] ").strip().lower()
            if answer not in {"j", "ja", "y", "yes"}:
                print("Abgebrochen; es wurden keine Dateien geändert.")
                return 1
        else:
            answer = input("Änderungen übernehmen? [j/N] ").strip().lower()
            if answer not in {"j", "ja", "y", "yes"}:
                print("Abgebrochen; es wurden keine Dateien geändert.")
                return 1

        DATABASE.write_text(canonical(candidate_db), encoding="utf-8", newline="\n")
        if export is not None:
            TOKEN_ARCHIVE.mkdir(parents=True, exist_ok=True)
            (TOKEN_ARCHIVE / f"{args.token_id}.json").write_text(canonical(export), encoding="utf-8", newline="\n")
        for source, target in files:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        print("Übernommen. Die Website wurde noch nicht neu generiert.")
        print("Website separat aktualisieren mit: python tools/build_site.py")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
