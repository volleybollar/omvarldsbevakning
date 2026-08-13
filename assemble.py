#!/usr/bin/env python3
"""
assemble.py - Reads /tmp/news.json, fills template.html from the repo checkout,
writes index.html + a dated archive file into the repo working tree.

Usage: python3 assemble.py <REPO_DIR>

Called by the nightly CCR agent, which then commits and pushes the result.
No GitHub token and no network access are needed - the agent's sandbox proxy
blocks api.github.com, so publishing goes through git push instead.
"""
import json, os, sys

if len(sys.argv) < 2:
    print("Usage: python3 assemble.py <REPO_DIR>")
    sys.exit(1)

REPO_DIR = sys.argv[1]

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def card_ai(i):
    return (f'<div class="news-card" data-title="{esc(i["t"])}" data-source="{esc(i["s"])}" data-category="ai" data-desc="{esc(i["d"])}" data-url="{esc(i["u"])}" data-lang="{esc(i.get("lang","en"))}">'
            f'<input type="checkbox" class="news-checkbox">'
            f'<div class="news-content"><div class="news-meta">'
            f'<span class="news-source news-source-ai">{esc(i["s"])}</span>'
            f'<div class="news-dot"></div><span class="news-time">{esc(i.get("age",""))}</span></div>'
            f'<div class="news-title">{esc(i["t"])}</div>'
            f'<div class="news-desc">{esc(i["d"])}</div>'
            f'<a href="{i["u"]}" class="news-link" target="_blank" rel="noopener">Las mer &#8594;</a>'
            f'</div></div>')

def card_dig(i):
    return (f'<div class="news-card" data-title="{esc(i["t"])}" data-source="{esc(i["s"])}" data-category="digital" data-desc="{esc(i["d"])}" data-url="{esc(i["u"])}" data-lang="{esc(i.get("lang","en"))}">'
            f'<input type="checkbox" class="news-checkbox">'
            f'<div class="news-content"><div class="news-meta">'
            f'<span class="news-source news-source-digital">{esc(i["s"])}</span>'
            f'<div class="news-dot"></div><span class="news-time">{esc(i.get("age",""))}</span></div>'
            f'<div class="news-title">{esc(i["t"])}</div>'
            f'<div class="news-desc">{esc(i["d"])}</div>'
            f'<a href="{i["u"]}" class="news-link" target="_blank" rel="noopener">Las mer &#8594;</a>'
            f'</div></div>')

def card_sch(i):
    badge = (f'<div class="news-dot"></div><span class="news-country">{i["c"]}</span>'
             if i.get("c") else "")
    return (f'<div class="news-card" data-title="{esc(i["t"])}" data-source="{esc(i["s"])}" data-category="school" data-desc="{esc(i["d"])}" data-url="{esc(i["u"])}" data-lang="{esc(i.get("lang","en"))}">'
            f'<input type="checkbox" class="news-checkbox">'
            f'<div class="news-content"><div class="news-meta">'
            f'<span class="news-source news-source-school">{esc(i["s"])}</span>'
            f'<div class="news-dot"></div><span class="news-time">{esc(i.get("age",""))}</span>{badge}</div>'
            f'<div class="news-title">{esc(i["t"])}</div>'
            f'<div class="news-desc">{esc(i["d"])}</div>'
            f'<a href="{i["u"]}" class="news-link news-link-orange" target="_blank" rel="noopener">Las mer &#8594;</a>'
            f'</div></div>')

# Load news data
with open("/tmp/news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

ai_items  = news.get("ai",  [])
dig_items = news.get("dig", [])
sch_items = news.get("sch", [])

# Read template from the repo checkout
template_path = os.path.join(REPO_DIR, "template.html")
print("Reading template from", template_path, "...")
with open(template_path, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace("{{DATE}}",          news["date"])
html = html.replace("{{DATE_LONG}}",     news["date_long"])
html = html.replace("{{TIME}}",          news["time"])
html = html.replace("{{COUNT_AI}}",      str(len(ai_items)))
html = html.replace("{{COUNT_DIGITAL}}", str(len(dig_items)))
html = html.replace("{{COUNT_SCHOOL}}",  str(len(sch_items)))
html = html.replace("{{NEWS_AI}}",       "".join(card_ai(i)  for i in ai_items))
html = html.replace("{{NEWS_DIGITAL}}",  "".join(card_dig(i) for i in dig_items))
html = html.replace("{{NEWS_SCHOOL}}",   "".join(card_sch(i) for i in sch_items))

# Write index.html and the dated archive into the repo working tree
datefile = news["date"] + "_Omvarldsbevakning.html"
for name in ("index.html", datefile):
    path = os.path.join(REPO_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  wrote {name} ({len(html.encode('utf-8'))} bytes)")

print(f"\nDone. {len(ai_items)} AI / {len(dig_items)} digitalisering / {len(sch_items)} skola.")
print(f"Now commit and push {REPO_DIR}.")
