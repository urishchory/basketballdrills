"""Builds coaches.json: the coaches' inspiration library (Hebrew).

Run:  python coaches_sync.py      (then python build_coaches.py)

Sources
  - ../video-studio/projects/*/project.json  -> every video Uri picked a version for
  - coaches_extra.json (optional)            -> items from other sources, e.g. the
    Drive mental-folder scan. Same item shape as below; they are merged by `id`
    and win over studio items with the same id.

Item shape (keep it stable, other sessions write to coaches_extra.json):
{
  "id": "p20261120-deni",             unique
  "source": "studio" | "drive",
  "title": "...", "player": "...",
  "sport": "כדורסל",                  free text, one of meta.sports ideally
  "audience": ["שחקנים","הורים","מאמנים"],
  "code": {"num": 12, "name": "אין 'אני והם', יש 'אנחנו'", "text": "exact words on the end card"},
  "topic": "...", "story": "...",
  "hook": "...", "lesson": "...", "on_court": "באימון הבא: ...",
  "tags": ["היסטורי"], "url": "https://drive.google.com/...", "added": "YYYY-MM-DD"
}
Only videos with a picked version are taken (Uri, 2026-11-26: "רק סרטונים שסיימתי").
No messages, briefs or personal notes go in: the repo is public.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
STUDIO = HERE.parent / "video-studio"
OUT = HERE / "coaches.json"
EXTRA = HERE / "coaches_extra.json"

# Uri's reminder codes, short names for the filter (video-studio/research/reminder-codes.md)
CODES = {
    1: "Next",
    2: "העבר נשאר בעבר",
    3: "טעות אחת הופכת לשלוש",
    4: "החטאתי – מחזיר בהגנה",
    5: "לקיחת אחריות",
    6: "לעשות למרות",
    7: "תפריט",
    8: "טוב יותר מאתמול",
    9: "לא מחויבים להצליח, מחויבים לנסות",
    10: "שולטים במה שבשליטתנו",
    11: "מותר להתאכזב",
    12: "אין 'אני והם', יש 'אנחנו'",
    13: "השחקן הוא המאמן",
    14: "באנו לעבוד",
    15: "כל פעולה, מכל הלב",
}
OTHER_CODE = "מסרים נוספים"

# "What happened?" - the coach picks the situation, the page shows the videos for it.
# Built from the on-court trigger column of reminder-codes.md. A video matches a situation
# when its code is in `codes` or one of `words` appears in its text.
SITUATIONS = [
    ("החטיא ומוריד ראש", ["Next", "העבר נשאר בעבר", "החטאתי – מחזיר בהגנה", "טעות אחת הופכת לשלוש"], ["החטא", "1 מתוך 13", "0 מתוך 18"]),
    ("אחרי הפסד קשה", ["מותר להתאכזב"], ["הפסד", "הפסיד"]),
    ("מאשימים אחרים", ["לקיחת אחריות"], ["מאשים", "להאשים"]),
    ("יושב על הספסל / לא נבחר", ["מותר להתאכזב", "לעשות למרות"], ["ספסל", "לא נבחר"]),
    ("מפחד לנסות / חוסר ביטחון", ["לא מחויבים להצליח, מחויבים לנסות", "חזרות מייצרות ביטחון"], ["ביטחון", "פחד"]),
    ("כל אחד לעצמו", ["אין 'אני והם', יש 'אנחנו'"], ["אגו"]),
    ("מתעסקים בשופט ובקהל", ["שולטים במה שבשליטתנו"], ["שפת גוף", "שופט"]),
    ("עייפים, אין מוטיבציה", ["לעשות למרות", "באנו לעבוד"], ["עייף", "מוטיבציה"]),
    ("פיגור גדול במשחק", [], ["פיגור", "0-3", "מ-3 הפסדים"]),
]

# Non-basketball and coach clips, by project id. Everything else is basketball.
SPORT = {
    "p20261104-cooley": "הוקי קרח",
    "p20261111-strug": "התעמלות",
    "p20261119-vrabel": "פוטבול",
    "p20261103-kane": "כדורגל",
    "p20261104-redmond": "אתלטיקה",
}
# Uri 26/11: split the videos into ספורטאים / ספורטאיות. Women in the videos, by player name.
WOMEN = {"אנג'ל ריס", "גבי וויליאמס", "נקאסה", "נטלי נקאסה", "ורוניקה ברטון", "קיה סטוקס", "קרי סטראג"}

# Clips where the speaker is a coach -> also useful for coaches
COACH_VOICE = {"p20261026-125853", "p20261023-nakase", "p20261025-nakase-full",
               "p20261120-redick", "p20261119-vrabel", "p20261118-215856"}


def clean(s):
    return " ".join((s or "").replace("\n", " ").split()).strip()


def code_of(d, opt):
    c = d.get("code") or {}
    num = c.get("primary")
    ec = d.get("endcard") or {}
    words = clean(c.get("text")) or clean(f"{ec.get('main', '')} {ec.get('main2', '')}")
    if num in CODES:
        return {"num": num, "name": CODES[num], "text": words}
    # try to match the story option's code string to a known code
    s = (opt or {}).get("code") or ""
    for n, name in CODES.items():
        if name != "Next" and name.split("–")[0].strip(" '") in s:
            return {"num": n, "name": name, "text": words}
    return {"num": None, "name": OTHER_CODE, "text": words}


def audience_of(pid, d):
    tag = d.get("tag") or ""
    aud = []
    if "להורים" in (d.get("title") or "") or tag == "הורים":
        aud.append("הורים")
    if tag == "מאמנים" or pid in COACH_VOICE:
        aud.append("מאמנים")
    if tag == "שחקנים" or not aud:
        aud.insert(0, "שחקנים")
    msgs = ((d.get("messages") or {}).get("options") or {})
    if msgs.get("parents") and "הורים" not in aud:
        aud.append("הורים")
    return aud


def quote_fallback():
    """Older projects have no story option; the quote library holds their story."""
    out = {}
    ql = STUDIO / "research" / "quote-library.json"
    if ql.exists():
        for q in json.loads(ql.read_text(encoding="utf-8")).get("quotes", []):
            if q.get("project"):
                out[q["project"]] = clean(q.get("story") or q.get("lesson") or "")
    return out


def studio_items():
    items = []
    qfb = quote_fallback()
    for pj in sorted((STUDIO / "projects").glob("p*/project.json")):
        d = json.loads(pj.read_text(encoding="utf-8"))
        if not d.get("picked"):
            continue
        pid = d["id"]
        st = d.get("story") if isinstance(d.get("story"), dict) else {}
        opts = st.get("options") or []
        ch = st.get("choice") if isinstance(st.get("choice"), int) else 0
        opt = opts[ch] if 0 <= ch < len(opts) else (opts[0] if opts else {})
        ec = d.get("endcard") or {}
        hk = d.get("hook") or {}
        drive = d.get("drive") or {}
        tag = d.get("tag") or ""
        tags = [t for t in [tag] if t in ("היסטורי", "מחוץ לכדורסל")]
        items.append({
            "id": pid,
            "source": "studio",
            "title": clean(d.get("title")),
            "player": clean(d.get("player")),
            "sport": SPORT.get(pid, "כדורסל"),
            "gender": "ספורטאיות" if clean(d.get("player")) in WOMEN else "ספורטאים",
            "audience": audience_of(pid, d),
            "code": code_of(d, opt),
            "topic": clean(d.get("topic") or d.get("value")),
            "story": clean(opt.get("story")) or qfb.get(pid, ""),
            "hook": clean(f"{hk.get('line1', '')} {hk.get('line2', '')}"),
            "lesson": clean(f"{ec.get('main', '')} {ec.get('main2', '')}"),
            "on_court": clean(ec.get("sub")),
            "tags": tags,
            "url": drive.get("link") if drive.get("status") == "done" else None,
            "added": (d.get("created") or drive.get("at") or "")[:10],
        })
    return items


def main():
    items = {it["id"]: it for it in studio_items()}
    if EXTRA.exists():
        for it in json.loads(EXTRA.read_text(encoding="utf-8")).get("items", []):
            items[it["id"]] = it
    # A coach must be able to watch it: only videos with a link reach the page.
    waiting = [it["id"] for it in items.values() if not it.get("url")]
    items = sorted((it for it in items.values() if it.get("url")),
                   key=lambda it: it.get("added", ""), reverse=True)
    # A line Uri repeats on 2+ videos becomes its own code chip (e.g. "חזרות מייצרות ביטחון").
    from collections import Counter
    other = Counter(it["code"]["text"].rstrip(".") for it in items if it["code"]["name"] == OTHER_CODE)
    for it in items:
        t = it["code"]["text"].rstrip(".")
        if it["code"]["name"] == OTHER_CODE and other[t] >= 2:
            it["code"]["name"] = t
    extra_codes = [t for t, n in other.items() if n >= 2]
    used = {it["code"]["name"] for it in items}
    meta_waiting = waiting
    situations = []
    for label, codes, words in SITUATIONS:
        hits = []
        for it in items:
            text = " ".join([it["title"], it["topic"], it["story"], it["hook"], it["lesson"], it["on_court"], it["code"]["text"]])
            if it["code"]["name"] in codes or any(w in text for w in words):
                hits.append(it["id"])
        if len(hits) >= 2:
            situations.append({"label": label, "ids": hits})
        print(f"  {label}: {len(hits)}")
    db = {
        "meta": {
            "title": "ספריית השראה לשחקנים",
            "subtitle": "סרטוני השראה מנטליים לשחקנים ולשחקניות. מחפשים לפי מה שקרה בקבוצה, לפי קוד או לפי ספורטאי, מראים או שולחים, וחוזרים על הקוד באימון.",
            "situations": situations,
            "codes": [n for n in CODES.values() if n in used] + extra_codes + ([OTHER_CODE] if OTHER_CODE in used else []),
            "audiences": ["שחקנים", "הורים", "מאמנים"],
            "updated": max((it.get("added", "") for it in items), default=""),
            "genders": ["ספורטאים", "ספורטאיות"],
            "sports": sorted({it["sport"] for it in items}, key=lambda s: (s != "כדורסל", s)),
        },
        "items": items,
    }
    OUT.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"coaches.json - {len(items)} videos, all with a link; waiting for a Drive link: {', '.join(meta_waiting) or '-'}")


if __name__ == "__main__":
    main()
