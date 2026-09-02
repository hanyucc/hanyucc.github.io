#!/usr/bin/env python3
"""Build hanyuc.com from content.yaml + templates/.

    python build.py            # write hanyuc.com/index.html
    python build.py --preview  # write hanyuc.com/preview.html instead

Content lives in content.yaml, markup in templates/, styling in static/.
Nothing here knows what a publication looks like; nothing there knows what
one is.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parent
OUT = ROOT / "hanyuc.com"
STATIC_SRC = ROOT / "static"
STATIC_DST = OUT / "static"

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<rect width="32" height="32" rx="5" fill="#4b6e5d"/>
<text x="16" y="23" font-family="Georgia,serif" font-size="21" font-weight="600"
      text-anchor="middle" fill="#f4f6f5">H</text>
</svg>
"""


def bibtex_key(pub: dict, first_author_surname: str) -> str:
    """chen2024dipole -- surname + year + first distinctive title word."""
    stop = {
        "a", "an", "the", "of", "for", "with", "and", "in", "on", "as",
        "to", "at", "by", "from", "i", "is",
    }
    words = re.findall(r"[A-Za-z]+", pub["title"].lower())
    tail = next((w for w in words if w not in stop and len(w) > 3), "paper")
    return f"{first_author_surname.lower()}{pub['year']}{tail}"


def make_bibtex(pub: dict, authors: list[dict]) -> str:
    """Derive a BibTeX entry from the same data the page renders.

    Override per-publication with an explicit `bibtex:` key in content.yaml
    when the venue needs fields this cannot know (volume, number, pages).
    """
    if pub.get("bibtex"):
        return pub["bibtex"].strip()

    names = " and ".join(a["name"] for a in authors)
    surname = authors[0]["name"].split()[-1]
    key = bibtex_key(pub, surname)

    if pub.get("preprint"):
        kind, venue_field = "@misc", None
    elif pub.get("journal"):
        kind, venue_field = "@article", "journal"
    else:
        kind, venue_field = "@inproceedings", "booktitle"

    # Double braces keep BibTeX styles from case-folding "ArchSym", "3D", etc.
    fields = [("title", "{" + pub["title"] + "}"), ("author", names)]
    if venue_field:
        fields.append((venue_field, pub["venue"]))
    fields.append(("year", str(pub["year"])))

    arxiv = next((l["href"] for l in pub["links"] if l["type"] == "arxiv"), None)
    if pub.get("preprint") and arxiv:
        fields.append(("eprint", arxiv.rstrip("/").split("/")[-1]))
        fields.append(("archivePrefix", "arXiv"))

    width = max(len(k) for k, _ in fields)
    body = ",\n".join(f"  {k.ljust(width)} = {{{v}}}" for k, v in fields)
    return f"{kind}{{{key},\n{body}\n}}"


def resolve(content: dict) -> dict:
    """Expand author ids and derive per-publication fields."""
    people = content["people"]

    for pub in content["publications"]:
        missing = [a for a in pub["authors"] if a not in people]
        if missing:
            raise SystemExit(
                f"content.yaml: publication {pub['id']!r} lists unknown "
                f"author id(s): {', '.join(missing)}"
            )
        pub["author_list"] = [people[a] for a in pub["authors"]]

        if not pub.get("links"):
            raise SystemExit(f"content.yaml: {pub['id']!r} has no links")
        # First link is the canonical destination for title + thumbnail.
        pub["primary_href"] = pub["links"][0]["href"]
        pub["bibtex"] = make_bibtex(pub, pub["author_list"])

    return content


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--preview",
        action="store_true",
        help="write preview.html and leave index.html untouched",
    )
    args = ap.parse_args()

    content = resolve(yaml.safe_load((ROOT / "content.yaml").read_text("utf-8")))

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    html = env.get_template("index.html").render(
        build_date=dt.date.today().strftime("%B %Y"),
        **content,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    if STATIC_DST.exists():
        shutil.rmtree(STATIC_DST)
    shutil.copytree(STATIC_SRC, STATIC_DST)
    (STATIC_DST / "favicon.svg").write_text(FAVICON, "utf-8")

    name = "preview.html" if args.preview else "index.html"
    (OUT / name).write_text(html, "utf-8")

    kb = len(html.encode("utf-8")) / 1024
    print(f"wrote {OUT / name}  ({kb:.1f} KB)")
    print(f"copied static -> {STATIC_DST}")


if __name__ == "__main__":
    main()
