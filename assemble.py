#!/usr/bin/env python3
"""
assemble.py - Reads /tmp/news.json, fetches HTML template from GitHub,
assembles full page, uploads index.html + dated archive to GitHub.

Usage: python3 assemble.py <GITHUB_TOKEN>
Called by the nightly CCR agent after it writes /tmp/news.json.
"""
import base64, json, sys, urllib.request

if len(sys.argv) < 2:
    print("Usage: python3 assemble.py <GITHUB_TOKEN>")
    sys.exit(1)

TOKEN = sys.argv[1]
REPO  = "volleybollar/omvarldsbevakning"
API   = "https://api.github.com/repos/" + REPO + "/contents/"
RAW   = "https://raw.githubusercontent.com/" + REPO + "/main/"
HDR   = {"Authorization": "token " + TOKEN,
         "Content-Type": "application/json",
         "User-Agent": "omvarldsbevakning-bot"}

def gh_get(path):
    req = urllib.request.Request(API + path, headers=HDR)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except:
        return {}

def gh_put(path, msg, content_b64, sha=None):
    body = {"message": msg, "content": content_b64}
    if sha:
        body["sha"] = sha
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API + path, data=data, headers=HDR, method="PUT")
    try:
        res = json.loads(urllib.request.urlopen(req).read())
        return res.get("commit", {}).get("sha", "error")[:12]
    except Exception as e:
        print("ERROR putting", path, str(e))
        return "error"

def fetch_raw(path):
    req = urllib.request.Request(RAW + path)
    return urllib.request.urlopen(req).read().decode("utf-8")

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def card_ai(i):
    return (f'<div class="news-card" data-title="{esc(i["t"])}" data-source="{esc(i["s"])}" data-category="ai" data-desc="{esc(i["d"])}">'
            f'<input type="checkbox" class="news-checkbox">'
            f'<div class="news-content"><div class="news-meta">'
            f'<span class="news-source news-source-ai">{esc(i["s"])}</span>'
            f'<div class="news-dot"></div><span class="news-time">{esc(i.get("age",""))}</span></div>'
            f'<div class="news-title">{esc(i["t"])}</div>'
            f'<div class="news-desc">{esc(i["d"])}</div>'
            f'<a href="{i["u"]}" class="news-link" target="_blank" rel="noopener">Las mer &#8594;</a>'
            f'</div></div>')

def card_dig(i):
    return (f'<div class="news-card" data-title="{esc(i["t"])}" data-source="{esc(i["s"])}" data-category="digital" data-desc="{esc(i["d"])}">'
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
    return (f'<div class="news-card" data-title="{esc(i["t"])}" data-source="{esc(i["s"])}" data-category="school" data-desc="{esc(i["d"])}">'
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

# Fetch template and substitute
print("Fetching template...")
html = fetch_raw("template.html")
html = html.replace("{{DATE}}",          news["date"])
html = html.replace("{{DATE_LONG}}",     news["date_long"])
html = html.replace("{{TIME}}",          news["time"])
html = html.replace("{{COUNT_AI}}",      str(len(ai_items)))
html = html.replace("{{COUNT_DIGITAL}}", str(len(dig_items)))
html = html.replace("{{COUNT_SCHOOL}}",  str(len(sch_items)))
html = html.replace("{{NEWS_AI}}",       "".join(card_ai(i)  for i in ai_items))
html = html.replace("{{NEWS_DIGITAL}}",  "".join(card_dig(i) for i in dig_items))
html = html.replace("{{NEWS_SCHOOL}}",   "".join(card_sch(i) for i in sch_items))

content_b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")

# Upload index.html
print("Uploading index.html...")
sha = gh_get("index.html").get("sha", "")
r1 = gh_put("index.html", f'Daily news {news["date"]}', content_b64, sha)
print("  index.html:", r1)

# Upload dated archive
datefile = news["date"] + "_Omvarldsbevakning.html"
print(f"Uploading {datefile}...")
sha2 = gh_get(datefile).get("sha", "")
r2 = gh_put(datefile, f"Archive {datefile}", content_b64, sha2 or None)
print(f"  {datefile}:", r2)

print(f"\nDone! https://volleybollar.github.io/omvarldsbevakning/")
if "error" in [r1, r2]:
    sys.exit(1)
