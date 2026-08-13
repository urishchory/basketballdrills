# Drill Library

A coach's searchable index of basketball material — drills collected from
Instagram, plus a room of mental-side talks. Each page is one self-contained
HTML file with no dependencies, so it loads fast on a phone at the side of the
court.

## Pages

| Page | What's on it |
| --- | --- |
| [Drill Library](https://urishchory.github.io/basketballdrills/) | 86 drills, small-sided games and teaching clips from Instagram. |
| [Mental Film Room](https://urishchory.github.io/basketballdrills/mental.html) | 114 talks and interviews, grouped by theme and audience. |

The Mental Film Room links point at private Google Drive files. They open for
the folder's owner; anyone else gets a permission request unless the Drive
sharing settings are changed.

## How it works

One template, one build script, one JSON file per page.

| File | Role |
| --- | --- |
| `library.json` | The drill data. This is the source of truth — every drill lives here. |
| `mental.json` | The mental-clips data, same shape. |
| `template.html` | The page design and the search/filter behaviour, shared by both pages. |
| `build.py` | Injects each JSON into the template and writes the pages into `docs/`. |

```bash
python build.py
```

GitHub Pages serves the `docs/` folder, so committing the rebuilt pages and
pushing publishes the change.

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
