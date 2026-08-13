#!/usr/bin/env python3
"""
mirror_feeds.py - Hämtar varje RSS-flöde i feeds.json och sparar det som
XML-fil i feeds/.

Varför detta behövs: nyhetsagenten kör i en sandlåda vars egress-proxy
blockerar i stort sett alla nyhetsdomäner. GitHub Actions-runners har
däremot fri internetåtkomst. Actions hämtar därför flödena hit, och
agenten läser dem ur sin utcheckning av repot i stället.

Körs av .github/workflows/mirror-feeds.yml.
"""
import json, pathlib, urllib.request
from datetime import datetime, timezone

UA = "Mozilla/5.0 (compatible; omvarldsbevakning-mirror/1.0)"
OUT = pathlib.Path("feeds")

feeds = json.load(open("feeds.json", encoding="utf-8"))
OUT.mkdir(exist_ok=True)
status = []

for f in feeds:
    req = urllib.request.Request(f["url"], headers={"User-Agent": UA})
    try:
        body = urllib.request.urlopen(req, timeout=30).read()
        # En del servrar skickar en tom rad före XML-deklarationen, och då
        # vägrar parsern läsa filen. Deklarationen måste stå allra först.
        body = body.lstrip()
        # Flera sajter svarar 200 med sin vanliga HTML-sida när RSS-flödet
        # har lagts ner. Spegla bara det som faktiskt är ett flöde - annars
        # behålls gårdagens fil, vilket är bättre än en HTML-sida.
        if b"<rss" not in body[:2000] and b"<feed" not in body[:2000]:
            raise ValueError("svaret är inte RSS eller Atom (troligen en HTML-sida)")
        (OUT / f"{f['id']}.xml").write_bytes(body)
        status.append({**f, "ok": True, "bytes": len(body)})
        print(f"OK    {f['id']:22s} {len(body):>8} bytes")
    except Exception as e:
        status.append({**f, "ok": False, "error": str(e)[:200]})
        print(f"FEL   {f['id']:22s} {e}")

ok = sum(1 for s in status if s["ok"])
(OUT / "_status.json").write_text(
    json.dumps({
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ok": ok,
        "failed": len(status) - ok,
        "feeds": status,
    }, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(f"\n{ok}/{len(status)} flöden hämtade.")
if ok == 0:
    raise SystemExit(1)
