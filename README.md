# Drill Library

A searchable index of basketball drills, small-sided games and teaching clips
collected from Instagram. Built as a single self-contained HTML page so it loads
fast on a phone at the side of the court.

**Live site:** https://urishchory.github.io/basketballdrills/

## How it works

Three files, one command.

| File | Role |
| --- | --- |
| `library.json` | The data. This is the source of truth — every drill lives here. |
| `template.html` | The page design and the search/filter behaviour. |
| `build.py` | Injects the data into the template and writes `docs/index.html`. |

```bash
python build.py
```

GitHub Pages serves the `docs/` folder, so pushing a rebuilt `docs/index.html`
publishes the change.

## Adding a drill

Append an object to `items` in `library.json`, then rebuild.

```json
{
  "id": "instagram-shortcode",
  "url": "https://www.instagram.com/reel/.../",
  "source": "account_name",
  "title": "Short name for the drill",
  "summary": "What it is and what it develops.",
  "category": "Defense",
  "type": "Drill",
  "tags": ["closeout", "recovery"],
  "players": "2",
  "status": "To Try",
  "added": "2026-08-09",
  "notes": "Anything worth remembering before running it."
}
```

Items sort by `added`, newest first. Ties keep their order in the file.

### Field values

- **category** — `Warm-Up`, `Ball Handling`, `Finishing`, `Shooting`,
  `Footwork & Moves`, `Defense`, `Team Play`, `Athleticism`
- **type** — `Drill`, `Small-Sided Game`, `Film Clip`, `Concept`
- **status** — `To Try`, `Works Well`, `Not For Us`

`type` separates a drill you run at practice from a clip you send a player to
watch. `status` is what turns the archive into a planning tool — mark drills
after you've actually used them.

`url` may be `null` for a drill with no clip; the card renders without a link.

The category list, type list and status list all come from `meta` at the top of
`library.json`. Adding a value there adds a filter chip. New categories also
need a colour in `template.html` under the `[data-cat=...]` block, or the chip
falls back to plain text.

## Notes on the sources

Captions were pulled automatically where possible. Instagram allows this for
most public posts; X, Facebook and YouTube block it, and eight Instagram posts
require a login. Those entries are written from the coach's own notes and say so
in their `notes` field.
