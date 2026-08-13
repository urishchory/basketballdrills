"""בונה את דפי ה-HTML מתוך קבצי ה-JSON.

הרצה:  python build.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATE = HERE / "template.html"

# docs/ holds the finished page and nothing else. GitHub Pages serves this
# folder directly (Settings > Pages > Branch: main, Folder: /docs), so the
# source JSON and working files never end up on the published site.
DIST = HERE / "docs"

# (מקור נתונים, דף היעד ב-dist) — רק דפים פעילים.
# fundamentals.json מוקפא בכוונה ולכן לא נבנה מכאן.
PAGES = [
    ("library.json", "index.html"),
    ("mental.json", "mental.html"),
]


def build(source: str, output: str) -> None:
    db = json.loads((HERE / source).read_text(encoding="utf-8"))
    meta = db["meta"]
    items = db["items"]

    # Newest batch first. Python's sort is stable and reverse=True does not
    # reorder ties, so items added on the same day keep their order in the file.
    items.sort(key=lambda it: it.get("added", ""), reverse=True)

    # ensure_ascii=False שומר על העברית קריאה; מנטרלים </script> שישבור את התג
    payload = json.dumps(db, ensure_ascii=False).replace("<", "\\u003c")

    html = TEMPLATE.read_text(encoding="utf-8")
    for token, value in {
        "__TITLE__": meta["title"],
        "__SUBTITLE__": meta["subtitle"],
        "__UPDATED__": meta["updated"],
        "__COUNT__": str(len(items)),
        "__DATA__": payload,
    }.items():
        html = html.replace(token, value)

    DIST.mkdir(exist_ok=True)
    (DIST / output).write_text(html, encoding="utf-8")
    print(f"built {DIST.name}/{output} - {len(items)} entries")


def main() -> None:
    for source, output in PAGES:
        build(source, output)


if __name__ == "__main__":
    main()
