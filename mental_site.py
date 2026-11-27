"""The coaches' mental library as its own site with the video files on it (Cloudflare Pages),
the same way the fundamentals coaches' site works (NBA-Fundamentals/pipeline/coach_site.py).

Uri, 26/11/2026: the Drive player was small on the phone and jumped back to Drive on full
screen. "יש משהו שכבר עובד, למה לסבך?" -> real <video> files, share sends the file, download.

Usage:
    python coaches_sync.py            # coaches.json from the studio (+ coaches_extra.json)
    python mental_site.py build       # encode new videos + write site/dist (no network)
    python mental_site.py deploy      # build + upload to Cloudflare Pages

Public site, no login (Uri chose public, 26/11). Videos: the picked 9:16 version from the studio,
re-encoded to 720p so each file stays well under the Pages 25 MiB limit and loads fast on a phone.
The Cloudflare token is read from NBA-Fundamentals/.env and never printed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent / "video-studio" / "projects"
ENV = Path.home() / "Desktop" / "NBA-Fundamentals" / ".env"
WORK = HERE / "site"                 # gitignored: cache of encoded files + dist
CACHE = WORK / "cache"
DIST = WORK / "dist"
PROJECT = "gezer-mental"
SITE_URL = f"https://{PROJECT}.pages.dev"
MAX_BYTES = 24 * 1024 * 1024


def source_video(pid: str) -> Path | None:
    pj = STUDIO / pid / "project.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text(encoding="utf-8"))
    v = d.get("picked")
    for name in (f"{v}_9x16.mp4", f"{v}_16x9.mp4"):
        f = STUDIO / pid / "versions" / name
        if v and f.is_file():
            return f
    return None


# Poster picked by hand where the studio's first option doesn't show the player
# (Uri 27/11: "ב-THUMBNAIL של מג'יק לא רואים אותו").
POSTER = {"p20261119-magic-1984": "thumbs/option2.jpg"}


def source_poster(pid: str) -> Path | None:
    d = json.loads((STUDIO / pid / "project.json").read_text(encoding="utf-8"))
    t = d.get("thumbs") or {}
    files = [POSTER.get(pid), t.get("chosen"), t.get("file")] + [o.get("file") for o in t.get("options") or [] if isinstance(o, dict)]
    for f in files:
        if isinstance(f, str) and (STUDIO / pid / f).is_file():
            return STUDIO / pid / f
    return None


def run(cmd: list) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout)[-400:])


def encode(pid: str, src: Path) -> Path:
    """720p H.264, faststart. Cached: re-encodes only when the source changed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{pid}.mp4"
    stamp = CACHE / f"{pid}.src"
    sig = f"{src.name}:{src.stat().st_size}:{int(src.stat().st_mtime)}"
    if out.exists() and stamp.exists() and stamp.read_text() == sig:
        return out
    for crf in (24, 27, 30):
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
             "-vf", "scale='if(gt(iw,ih),1280,720)':-2", "-c:v", "libx264", "-preset", "medium",
             "-crf", str(crf), "-maxrate", "2500k", "-bufsize", "5000k", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)])
        if out.stat().st_size <= MAX_BYTES:
            break
    stamp.write_text(sig)
    return out


def poster(pid: str, video: Path) -> Path:
    out = CACHE / f"{pid}.jpg"
    if out.exists() and out.stat().st_mtime >= video.stat().st_mtime:
        return out
    src = source_poster(pid)
    if src:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", "scale=540:-2", "-q:v", "4", str(out)])
    else:
        run(["ffmpeg", "-y", "-v", "error", "-ss", "3", "-i", str(video), "-frames:v", "1",
             "-vf", "scale=540:-2", "-q:v", "4", str(out)])
    return out


def build(DIST: Path = DIST) -> int:
    db = json.loads((HERE / "coaches.json").read_text(encoding="utf-8"))
    (DIST / "v").mkdir(parents=True, exist_ok=True)
    (DIST / "p").mkdir(exist_ok=True)
    for old in list((DIST / "v").glob("*.mp4")) + list((DIST / "p").glob("*.jpg")):
        old.unlink()
    keep = []
    for it in db["items"]:
        pid = it["id"]
        src = source_video(pid) if it.get("source", "studio") == "studio" else None
        if not src:
            print(f"  skip {pid}: no video file")
            continue
        v = encode(pid, src)
        p = poster(pid, v)
        if not (DIST / "v" / f"{pid}.mp4").exists():
            shutil.copy2(v, DIST / "v" / f"{pid}.mp4")
        shutil.copy2(p, DIST / "p" / f"{pid}.jpg")
        it["video"] = f"v/{pid}.mp4"
        it["poster"] = f"p/{pid}.jpg"
        it["file_name"] = f"{it['title']}.mp4".replace("/", "-").replace("\\", "-").replace('"', "").replace("?", "")
        keep.append(it)
        print(f"  {pid}: {v.stat().st_size // 1024} KB")
    db["items"] = keep
    payload = json.dumps(db, ensure_ascii=False).replace("<", "\\u003c")
    html = (HERE / "template-coaches.html").read_text(encoding="utf-8")
    for token, value in {"__TITLE__": db["meta"]["title"], "__SUBTITLE__": db["meta"]["subtitle"],
                         "__COUNT__": str(len(keep)), "__DATA__": payload}.items():
        html = html.replace(token, value)
    (DIST / "index.html").write_text(html, encoding="utf-8")
    # long cache for the media, fresh html
    (DIST / "_headers").write_text("/v/*\n  Cache-Control: public, max-age=604800\n/p/*\n  Cache-Control: public, max-age=604800\n", encoding="utf-8")
    print(f"built {DIST} - {len(keep)} videos")
    return len(keep)


def _env() -> dict:
    env = dict(os.environ)
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and line.split("=", 1)[0].strip() in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"):
            k, v = line.split("=", 1)
            if v.strip():
                env[k.strip()] = v.strip().strip('"')
    return env


def _account(env: dict) -> str:
    if env.get("CLOUDFLARE_ACCOUNT_ID"):
        return env["CLOUDFLARE_ACCOUNT_ID"]
    st = json.loads((ENV.parent / "data" / "coach_site" / "state.json").read_text(encoding="utf-8"))
    return st["account_id"]


def deploy() -> None:
    build()
    env = _env()
    env["CLOUDFLARE_ACCOUNT_ID"] = _account(env)
    npx = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
    # create the project the first time (ignore "already exists")
    subprocess.run([npx, "--yes", "wrangler@4", "pages", "project", "create", PROJECT, "--production-branch", "main"],
                   cwd=str(WORK), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    r = subprocess.run([npx, "--yes", "wrangler@4", "pages", "deploy", str(DIST), "--project-name", PROJECT,
                        "--branch", "main", "--commit-dirty=true"],
                       cwd=str(WORK), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (r.stdout + r.stderr).replace(env.get("CLOUDFLARE_API_TOKEN", "~"), "***")[-800:]
    print(tail)
    if r.returncode:
        sys.exit(1)
    print("live:", SITE_URL)


def github() -> None:
    """GitHub Pages (docs/coaches/), used while the Cloudflare token can't create a new Pages
    project (26/11: 10001 on pages/projects). Commit docs/coaches + push publishes it."""
    build(HERE / "docs" / "coaches")


if __name__ == "__main__":
    {"build": build, "deploy": deploy, "github": github}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
