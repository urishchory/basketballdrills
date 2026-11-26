"""Builds docs/coaches.html (Hebrew, RTL) from coaches.json.

Run:  python coaches_sync.py && python build_coaches.py
Kept apart from build.py on purpose: this page has its own Hebrew template
(template-coaches.html) and its own data shape.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent


def main() -> None:
    db = json.loads((HERE / "coaches.json").read_text(encoding="utf-8"))
    # neutralise "</script>" inside the data blob, JSON.parse restores it
    payload = json.dumps(db, ensure_ascii=False).replace("<", "\\u003c")
    html = (HERE / "template-coaches.html").read_text(encoding="utf-8")
    for token, value in {
        "__TITLE__": db["meta"]["title"],
        "__SUBTITLE__": db["meta"]["subtitle"],
        "__COUNT__": str(len(db["items"])),
        "__DATA__": payload,
    }.items():
        html = html.replace(token, value)
    out = HERE / "docs" / "coaches.html"
    out.write_text(html, encoding="utf-8")
    print(f"built docs/coaches.html - {len(db['items'])} videos")


if __name__ == "__main__":
    main()
