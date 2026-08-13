#!/usr/bin/env python3
"""
recent_items.py - Läser de speglade flödena i feeds/ och skriver ut de
artiklar som publicerats de senaste N timmarna som kompakt JSON.

Användning: python3 recent_items.py [TIMMAR]   (standard 72)

Poängen: nyhetsagenten ska slippa öppna 24 XML-filer. Den kör det här
skriptet en gång och får en färdig, datumfiltrerad lista. Färskhetsregeln
avgörs alltså av kod, inte av modellens bedömning.

Hanterar både RSS (<item>, pubDate) och Atom (<entry>, published/updated).
"""
import json, pathlib, sys
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

ATOM = {"a": "http://www.w3.org/2005/Atom"}
HOURS = int(sys.argv[1]) if len(sys.argv) > 1 else 72
NOW = datetime.now(timezone.utc)
cutoff = NOW - timedelta(hours=HOURS)

here = pathlib.Path(__file__).parent
feeds = {f["id"]: f for f in json.load(open(here / "feeds.json", encoding="utf-8"))}


def parse_date(s):
    """RSS använder RFC 822-datum, Atom använder ISO 8601. Prova båda."""
    if not s:
        return None
    s = s.strip()
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def first(el, *paths):
    """Returnera texten i det första sökvägsuttryck som ger träff."""
    for p in paths:
        found = el.find(p, ATOM) if p.startswith("a:") or "a:" in p else el.find(p)
        if found is not None:
            if found.get("href"):
                return found.get("href").strip()
            txt = "".join(found.itertext()).strip()
            if txt:
                return txt
    return ""


out = []
for path in sorted((here / "feeds").glob("*.xml")):
    meta = feeds.get(path.stem, {"name": path.stem, "cat": "?", "lang": "en"})
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        continue

    for it in root.findall(".//item") + root.findall(".//a:entry", ATOM):
        published = parse_date(first(it, "pubDate", "a:published", "a:updated", "date"))
        if published is None or published < cutoff:
            continue
        title = first(it, "title", "a:title")
        url = first(it, "link", "a:link")
        if not title or not url:
            continue
        summary = first(it, "description", "a:summary", "a:content")
        out.append({
            "source": meta["name"],
            "cat": meta["cat"],
            "lang": meta["lang"],
            "title": title,
            "url": url,
            "published": published.strftime("%Y-%m-%dT%H:%MZ"),
            "age_hours": round((NOW - published).total_seconds() / 3600),
            "summary": " ".join(summary.split())[:400],
        })

out.sort(key=lambda x: x["published"], reverse=True)
print(json.dumps(out, ensure_ascii=False, indent=1))
print(f"\n# {len(out)} artiklar senaste {HOURS}h", file=sys.stderr)
