"""Smoke the selector shape docling's HTML backend uses (p:has(...)) on SoupSieve 4."""
import json

import bs4
import soupsieve
from docling.backend import html_backend

breakers = sorted(html_backend._PARA_BREAKERS)
html = "<div><p>a<table></table></p><p>plain</p><p>b<ul><li>x</li></ul></p></div>"
soup = bs4.BeautifulSoup(html, "html.parser")
selector = "p:has(" + ",".join(breakers) + ")"
matched = soup.select(selector)
result = {"soupsieve": soupsieve.__version__, "bs4": bs4.__version__,
          "selector_tags": len(breakers), "matched": len(matched),
          "status": "pass" if len(matched) >= 1 else "fail"}
print(json.dumps(result))
raise SystemExit(0 if result["status"] == "pass" else 1)
