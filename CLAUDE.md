# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static site indexing basketball coaching material for one coach. No framework,
no dependencies, no package manager — Python 3 standard library and vanilla JS.
Published at https://urishchory.github.io/basketballdrills/ via GitHub Pages
(branch `main`, folder `/docs`).

## Commands

```bash
python build.py
```

Builds every page into `docs/`. That is the only build step. There are no tests,
no linter and nothing to install. Verifying a change means rebuilding and opening
the page.

Push credentials are cached in Git Credential Manager, so `git push` works
non-interactively.

## Architecture

One template, one build script, one JSON file per page:

```
library.json ─┐
              ├─→ build.py ─→ template.html ─→ docs/*.html
mental.json  ─┘
```

`build.py` holds a `PAGES` list of `(source_json, output_html)` pairs. Adding a
page means adding a tuple and creating the JSON — no other code changes.

**Token contract.** `build.py` does plain string replacement of `__TITLE__`,
`__SUBTITLE__`, `__UPDATED__`, `__COUNT__` and `__DATA__` in `template.html`.
`__DATA__` lands inside `<script id="data" type="application/json">`. Every `<`
in the payload is replaced with its unicode-escaped equivalent — the `.replace()`
call at the end of `build.py`'s serialisation step — which `JSON.parse` restores
at runtime, so a caption containing a closing script tag cannot break out of the
element. Keep that replace in place. Rendering, search and filtering all happen
client-side from that blob.

**`meta` drives the UI.** The `categories`, `types` and `statuses` arrays in each
JSON become the three rows of filter chips. `meta.labels` optionally renames the
row headings and the search placeholder (`library.json` omits it and gets the
defaults; `mental.json` sets its own). So the two pages have different taxonomies
while sharing one template.

**Sort order.** Items sort by `added` descending. Python's sort is stable and
`reverse=True` does not reorder ties, so items sharing a date keep their order in
the JSON file.

## Traps in template.html

Category and status colours live in CSS, keyed on the literal string from the
JSON. The data and the stylesheet must be kept in sync by hand:

- **A new `category` needs four CSS rules**, not one — the bare `[data-cat="…"]`
  block, the `@media (prefers-color-scheme: dark)` block, and the
  `:root[data-theme="light"]` and `:root[data-theme="dark"]` blocks. Miss any and
  the chip loses its colour in that theme. Both pages' categories share these
  blocks, so names must stay unique across `library.json` and `mental.json`.
- **A new `status` value needs a `[data-status="…"] { --sc: … }` rule**, or its
  dot renders with no colour. The "fade out rejected items" rule is hardcoded to
  `Not For Us`.

Both JSON files currently use the same three status values even though
`mental.json` relabels the row.

## Content workflow

The coach pastes an Instagram link into chat; Claude fetches the post, writes the
entry, rebuilds and pushes. Content and UI are **English**, but the coach's own
house jargon stays in Hebrew inside `tags` (דג מלוח, לובסטר, עקיצה, ריצהגנה,
כיס אוויר, יישור מנופים) — those terms have no reliable English equivalent and
translating them distorts them.

`url` may be `null`; the card then renders a "no clip" badge instead of a link.

**Platform access via WebFetch:** Instagram public posts usually work (retry with
`?hl=en` to bust the 15-minute cache). X returns HTTP 402; Facebook and YouTube
are fully blocked. These eight Instagram posts require a login and have been
retried three times — do not spend calls on them again:

```
C1w0mbbsCoT  DAePZ-LN2Jr  Cr8hEqAgxUt  Cxvo_Bhu9bZ
C8YdG_gshox  C285K_kAHMp  C2qAl7VAe76  CtXdB9gg2Kb
```

Entries built from the coach's notes rather than a fetched caption say so in
their `notes` field.

## Before committing data

**The repository is public.** A third-party email address once reached
`mental.json` through a Drive file's ownership metadata; scan new data for
personal details that are not the coach's own before committing.

`mental.json` links point at private Google Drive files — they work for the
folder's owner and show a permission request to everyone else.

`fundamentals.json` (56 entries) is deliberately gitignored and absent from
`PAGES`. The coach put that page on hold; do not revive it unless asked.

`dist/` is a superseded output folder, gitignored. The published output is
`docs/`.
