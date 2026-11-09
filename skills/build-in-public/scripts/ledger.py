#!/usr/bin/env python3
"""Build-in-public ledger.

Tracks numbered episodes and the X / LinkedIn posts drafted for them:
what is drafted, what has been posted (and where), and how this week
compares with the posting targets. Standard library only. It never
touches the network and never posts anything.

The ledger lives at build-in-public/ledger.json in your project. The
script finds it by walking up from the current directory, or you can
pass --ledger PATH.

Commands
  init                      create build-in-public/ (ledger + context.md) here
  set-targets               change the weekly post targets per platform
  status                    totals, this week vs targets, pending drafts
  episodes                  every episode with its posts and their status
  next                      next episode number + commit to diff from
  new-episode               create an episode and its draft folder
  check FILE                lint a draft (X weighted length, links, AI tells)
  add-post                  register a draft file under an episode
  mark-posted ID            record that a draft went live (optionally --url)
  mark-skipped ID           record that a draft will not be posted
  metrics ID                record numbers the user read off X/LinkedIn
  list                      posts, filterable by episode/platform/status
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta

LEDGER_DIRNAME = "build-in-public"
LEDGER_FILENAME = "ledger.json"
PLATFORM_CODES = {"x": "X", "linkedin": "LI"}
FORMATS = ("post", "thread", "carousel", "video", "poll", "article")
PILLARS = ("build-log", "decision", "lesson", "customer-insight", "point-of-view", "proof", "numbers", "launch")
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "context-template.md")
STATUSES = ("draft", "posted", "skipped")
DEFAULT_TARGETS = {"x": 7, "linkedin": 3}
X_LIMIT = 280
X_PREMIUM_LIMIT = 25000
LINKEDIN_LIMIT = 3000
LINKEDIN_FOLD = 210  # roughly where "...see more" cuts a post on desktop
METRIC_FIELDS = ("impressions", "likes", "replies", "reposts", "quotes", "bookmarks",
                 "shares", "clicks", "profile_visits", "follows", "comments", "reactions")

THREAD_SEPARATOR = re.compile(r"^\s*---\s*$", re.M)
URL_RE = re.compile(
    r"https?://\S+|\b(?:[a-z0-9-]+\.)+(?:com|in|io|ai|co|app|dev|org|net|so|xyz)\b(?:/\S*)?",
    re.I,
)
HASHTAG_RE = re.compile(r"(?<![\w&])#[A-Za-z_][\w]*")
AI_TELLS = [
    (re.compile(r"\b(?:it[’']?s|this is|that[’']?s)\s+not\s+(?:just\s+)?[^.!?\n]{1,60}[,;:—-]\s*(?:it[’']?s|this is|that[’']?s)\b", re.I),
     "'it's not X, it's Y' reveal"),
    (re.compile(r"\bno\s+\w+(?:\s+\w+)?,\s*no\s+\w+(?:\s+\w+)?,\s*(?:and\s+)?no\s+\w+", re.I), "'no X, no Y, no Z' list"),
    (re.compile(r"\b(?:delve|game[- ]changer|unlock(?:ing)? the power|leverag(?:e|ing)|seamless(?:ly)?|"
                r"revolutioni[sz]e|in today[’']?s (?:fast[- ]paced|digital) world|excited to announce|"
                r"thrilled to (?:share|announce)|here[’']?s the thing|let that sink in|buckle up)\b", re.I),
     "stock AI/LinkedIn phrase"),
    (re.compile(r"—"), "em dash (reads as AI to many people; use a full stop or comma)"),
]
ENGAGEMENT_BAIT = re.compile(
    r"\b(?:comment\s+['\"]?\w+['\"]?\s+(?:below\s+)?(?:and|to get|for)|like if you|repost if|"
    r"tag (?:a|someone|3)|follow for more|drop a [^\s]+ (?:below|in the comments))\b",
    re.I,
)


# ---------------------------------------------------------------- utilities

def now() -> datetime:
    return datetime.now().astimezone()


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def parse_when(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def week_start(dt: datetime) -> datetime:
    start = dt - timedelta(days=dt.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)


def slugify(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:limit].rstrip("-")) or "episode"


def die(message: str) -> None:
    sys.exit(f"error: {message}")


def find_ledger(explicit: str | None) -> str:
    if explicit:
        return os.path.abspath(explicit)
    directory = os.getcwd()
    while True:
        candidate = os.path.join(directory, LEDGER_DIRNAME, LEDGER_FILENAME)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent
    die("no build-in-public/ledger.json above the current directory. "
        "Run `ledger.py init` from the project root, or pass --ledger PATH.")
    return ""  # unreachable


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save(path: str, data: dict) -> None:
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".ledger-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def base_dir(ledger_path: str) -> str:
    return os.path.dirname(ledger_path)


def rel_to_base(ledger_path: str, file_path: str) -> str:
    absolute = os.path.abspath(file_path)
    base = base_dir(ledger_path)
    try:
        rel = os.path.relpath(absolute, base)
    except ValueError:
        return absolute
    return absolute if rel.startswith("..") else rel


def get_episode(data: dict, number: int) -> dict:
    for episode in data["episodes"]:
        if episode["number"] == number:
            return episode
    die(f"episode {number} does not exist. Run `ledger.py episodes` to see them.")
    return {}


def get_post(data: dict, post_id: str) -> dict:
    wanted = post_id.upper()
    for post in data["posts"]:
        if post["id"].upper() == wanted:
            return post
    die(f"post {post_id} does not exist. Run `ledger.py list` to see post IDs.")
    return {}


def targets(data: dict) -> dict:
    return {**DEFAULT_TARGETS, **data.get("settings", {}).get("weekly_targets", {})}


# ---------------------------------------------------------------- draft checks

def _x_weight(char: str) -> int:
    cp = ord(char)
    if cp in (0x200D, 0xFE0E, 0xFE0F) or 0x1F3FB <= cp <= 0x1F3FF:
        return 0  # joiners, variation selectors and skin tones ride on the emoji before them
    if cp <= 4351 or 8192 <= cp <= 8205 or 8208 <= cp <= 8223 or 8242 <= cp <= 8247:
        return 1
    return 2


def x_length(text: str) -> int:
    """X's weighted length: links count 23, CJK and emoji count 2. Approximate for exotic emoji."""
    total, position = 0, 0
    for match in URL_RE.finditer(text):
        total += sum(_x_weight(c) for c in text[position:match.start()])
        total += 23
        position = match.end()
    total += sum(_x_weight(c) for c in text[position:])
    return total


def split_segments(text: str) -> list[str]:
    return [part.strip() for part in THREAD_SEPARATOR.split(text) if part.strip()]


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def lint_common(text: str) -> list[str]:
    warnings = []
    for pattern, label in AI_TELLS:
        hits = pattern.findall(text)
        if hits:
            warnings.append(f"{label} x{len(hits)}")
    if ENGAGEMENT_BAIT.search(text):
        warnings.append("engagement bait phrasing (pods/bait are against X and LinkedIn rules and invite 'not interested')")
    return warnings


def check_draft(platform: str, text: str, premium: bool = False) -> tuple[list[str], list[str]]:
    """Returns (report_lines, warnings)."""
    report, warnings = [], []
    if platform == "x":
        segments = split_segments(text)
        if not segments:
            return ["(empty)"], ["draft is empty"]
        limit = X_PREMIUM_LIMIT if premium else X_LIMIT
        for index, segment in enumerate(segments, 1):
            length = x_length(segment)
            label = "post" if index == 1 else f"reply {index - 1}"
            report.append(f"  {label}: {length}/{limit}")
            if length > limit:
                warnings.append(f"{label} is {length - limit} over the {limit} limit")
        if URL_RE.search(segments[0]):
            warnings.append("link in the main post: put the story first and the link in the first self-reply (see x-rules.md)")
        tags = HASHTAG_RE.findall(text)
        if len(tags) > 1:
            warnings.append(f"{len(tags)} hashtags: use 0, at most 1")
        if len(segments) > 8:
            warnings.append(f"{len(segments)} parts: threads past 7 rarely get read to the end")
    else:
        length = len(text.strip())
        report.append(f"  length: {length}/{LINKEDIN_LIMIT} characters, {len(text.split())} words")
        report.append(f"  before 'see more' (~{LINKEDIN_FOLD} chars): {text.strip()[:LINKEDIN_FOLD]!r}")
        if length > LINKEDIN_LIMIT:
            warnings.append(f"{length - LINKEDIN_LIMIT} characters over LinkedIn's {LINKEDIN_LIMIT} limit")
        if URL_RE.search(text):
            warnings.append("link in the post body: prefer the first comment, or the domain as plain text without a preview card")
        tags = HASHTAG_RE.findall(text)
        if len(tags) > 3:
            warnings.append(f"{len(tags)} hashtags: 0 to 3 is plenty")
    warnings.extend(lint_common(text))
    return report, warnings


# ---------------------------------------------------------------- commands

def cmd_init(args: argparse.Namespace) -> None:
    path = os.path.abspath(args.ledger) if args.ledger else os.path.join(os.getcwd(), LEDGER_DIRNAME, LEDGER_FILENAME)
    if os.path.exists(path):
        die(f"{path} already exists; not overwriting it.")
    folder = os.path.dirname(path)
    os.makedirs(os.path.join(folder, "episodes"), exist_ok=True)
    project = args.project or os.path.basename(os.getcwd()) or "Project"
    data = {
        "version": 1,
        "project": project,
        "created_at": iso(now()),
        "settings": {"weekly_targets": dict(DEFAULT_TARGETS)},
        "episodes": [],
        "posts": [],
    }
    save(path, data)
    print(f"created {path}")
    context = os.path.join(folder, "context.md")
    if os.path.exists(context):
        print(f"kept existing {context}")
    elif os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, encoding="utf-8") as handle:
            template = handle.read().replace("{{PROJECT}}", project)
        with open(context, "w", encoding="utf-8") as handle:
            handle.write(template)
        print(f"created {context} (fill it in before the first episode)")
    else:
        print("warning: context template not found; create build-in-public/context.md by hand")


def cmd_set_targets(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    goal = data.setdefault("settings", {}).setdefault("weekly_targets", dict(DEFAULT_TARGETS))
    if args.x is None and args.linkedin is None:
        die("give --x N and/or --linkedin N")
    for platform in PLATFORM_CODES:
        value = getattr(args, platform)
        if value is not None:
            if value < 0:
                die("targets cannot be negative")
            goal[platform] = value
    save(path, data)
    print("weekly targets: " + ", ".join(f"{k}={v}" for k, v in goal.items()))


def cmd_status(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    posts, episodes = data["posts"], data["episodes"]
    start = week_start(now())
    goal = targets(data)
    print(f"{data.get('project', 'Project')} build in public  ({path})")
    print(f"episodes: {len(episodes)}  |  next episode: {next_episode_number(data)}")
    for platform, code in PLATFORM_CODES.items():
        mine = [p for p in posts if p["platform"] == platform]
        posted = [p for p in mine if p["status"] == "posted"]
        this_week = [p for p in posted if p.get("posted_at") and parse_when(p["posted_at"]) >= start]
        drafts = [p for p in mine if p["status"] == "draft"]
        last = max((p["posted_at"] for p in posted if p.get("posted_at")), default=None)
        name = "X" if platform == "x" else "LinkedIn"
        print(f"{name:9} posted {len(posted):3} total | this week {len(this_week)}/{goal.get(platform, 0)} "
              f"| drafts waiting {len(drafts)} | last posted {last or 'never'}")
    waiting = [p for p in posts if p["status"] == "draft"]
    if waiting:
        print("\ndrafts not yet posted:")
        for post in waiting:
            print(f"  {post['id']:10} ep {post['episode']:03d} {post['platform']:8} {post['format']:8} {post['hook'][:70]}")
    open_episodes = [e for e in episodes if episode_state(data, e["number"]) not in ("done", "empty")]
    if open_episodes:
        print("\nepisodes still open: " + ", ".join(f"{e['number']:03d}" for e in open_episodes))


def next_episode_number(data: dict) -> int:
    return max((e["number"] for e in data["episodes"]), default=0) + 1


def episode_state(data: dict, number: int) -> str:
    statuses = [p["status"] for p in data["posts"] if p["episode"] == number]
    if not statuses:
        return "empty"
    if all(s in ("posted", "skipped") for s in statuses):
        return "done"
    if any(s == "posted" for s in statuses):
        return "partly posted"
    return "drafted"


def cmd_episodes(args: argparse.Namespace) -> None:
    data = load(find_ledger(args.ledger))
    if not data["episodes"]:
        print("no episodes yet")
        return
    for episode in data["episodes"]:
        number = episode["number"]
        print(f"{number:03d}  {episode['title']}  [{episode['pillar']}]  {episode_state(data, number)}")
        if episode.get("summary"):
            print(f"     {episode['summary']}")
        for post in [p for p in data["posts"] if p["episode"] == number]:
            when = f" {post['posted_at']}" if post.get("posted_at") else ""
            url = f" {post['url']}" if post.get("url") else ""
            print(f"     {post['id']:10} {post['platform']:8} {post['format']:8} {post['status']}{when}{url}")


def cmd_next(args: argparse.Namespace) -> None:
    data = load(find_ledger(args.ledger))
    number = next_episode_number(data)
    since = None
    for episode in reversed(data["episodes"]):
        if episode.get("since_commit"):
            since = episode["since_commit"]
            break
    print(f"next episode: {number:03d}")
    if since:
        print(f"last episode was written at commit {since}; see what changed with:")
        print(f"  git log --oneline {since}..HEAD")
    else:
        print("no commit recorded yet; use the whole history (git log --oneline)")
    recent = data["episodes"][-5:]
    if recent:
        print("recent episode titles (avoid repeating the angle):")
        for episode in recent:
            print(f"  {episode['number']:03d} {episode['title']} [{episode['pillar']}]")


def cmd_new_episode(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    number = next_episode_number(data)
    folder = os.path.join("episodes", f"{number:03d}-{slugify(args.title)}")
    os.makedirs(os.path.join(base_dir(path), folder), exist_ok=True)
    episode = {
        "number": number,
        "title": args.title,
        "pillar": args.pillar,
        "summary": args.summary or "",
        "sources": args.source or [],
        "since_commit": args.since_commit,
        "created_at": iso(now()),
        "dir": folder,
    }
    data["episodes"].append(episode)
    save(path, data)
    print(f"episode {number:03d} created: {os.path.join(base_dir(path), folder)}")


def cmd_check(args: argparse.Namespace) -> None:
    with open(args.file, encoding="utf-8") as handle:
        text = handle.read()
    report, warnings = check_draft(args.platform, text, args.premium)
    print(f"{args.file} ({args.platform})")
    print("\n".join(report))
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("no warnings")


def cmd_add_post(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    get_episode(data, args.episode)
    if not os.path.exists(args.file):
        die(f"{args.file} does not exist; write the draft first.")
    with open(args.file, encoding="utf-8") as handle:
        text = handle.read()
    code = PLATFORM_CODES[args.platform]
    count = sum(1 for p in data["posts"] if p["episode"] == args.episode and p["platform"] == args.platform)
    post_id = f"E{args.episode:03d}-{code}{count + 1}"
    _, warnings = check_draft(args.platform, text)
    post = {
        "id": post_id,
        "episode": args.episode,
        "platform": args.platform,
        "format": args.format,
        "file": rel_to_base(path, args.file),
        "hook": args.hook or first_line(text),
        "status": "draft",
        "created_at": iso(now()),
        "posted_at": None,
        "url": None,
        "metrics": [],
    }
    data["posts"].append(post)
    save(path, data)
    print(f"registered {post_id} ({args.platform} {args.format}) -> {post['file']}")
    for warning in warnings:
        print(f"  warning: {warning}")


def cmd_mark_posted(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    post = get_post(data, args.id)
    if post["status"] == "posted" and not args.force:
        die(f"{post['id']} is already marked posted at {post['posted_at']}; pass --force to overwrite.")
    post["status"] = "posted"
    post["posted_at"] = iso(parse_when(args.at)) if args.at else iso(now())
    if args.url:
        post["url"] = args.url
    save(path, data)
    print(f"{post['id']} marked posted at {post['posted_at']}" + (f" ({post['url']})" if post.get("url") else ""))


def cmd_mark_skipped(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    post = get_post(data, args.id)
    if post["status"] == "posted":
        die(f"{post['id']} is already posted; it cannot be skipped.")
    post["status"] = "skipped"
    post["skip_reason"] = args.reason or ""
    save(path, data)
    print(f"{post['id']} marked skipped")


def cmd_metrics(args: argparse.Namespace) -> None:
    path = find_ledger(args.ledger)
    data = load(path)
    post = get_post(data, args.id)
    values = {field: getattr(args, field) for field in METRIC_FIELDS if getattr(args, field) is not None}
    if not values:
        die("give at least one metric, for example --impressions 1200 --replies 9")
    snapshot = {"recorded_at": iso(now()), **values}
    post.setdefault("metrics", []).append(snapshot)
    save(path, data)
    print(f"{post['id']} metrics recorded: " + ", ".join(f"{k}={v}" for k, v in values.items()))


def cmd_list(args: argparse.Namespace) -> None:
    data = load(find_ledger(args.ledger))
    posts = data["posts"]
    if args.episode is not None:
        posts = [p for p in posts if p["episode"] == args.episode]
    if args.platform:
        posts = [p for p in posts if p["platform"] == args.platform]
    if args.status:
        posts = [p for p in posts if p["status"] == args.status]
    if args.json:
        print(json.dumps(posts, indent=2, ensure_ascii=False))
        return
    if not posts:
        print("no matching posts")
        return
    for post in posts:
        latest = post["metrics"][-1] if post.get("metrics") else None
        numbers = ""
        if latest:
            numbers = "  " + " ".join(f"{k}={v}" for k, v in latest.items() if k != "recorded_at")
        print(f"{post['id']:10} {post['platform']:8} {post['format']:8} {post['status']:7} "
              f"{post.get('posted_at') or '':25} {post['hook'][:60]}{numbers}")


# ---------------------------------------------------------------- cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build-in-public ledger (local only; never posts).")
    parser.add_argument("--ledger", help="path to ledger.json (default: search upward for build-in-public/ledger.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create build-in-public/ (ledger.json, context.md, episodes/) in the current directory")
    p.add_argument("--project", help="product name (default: current folder name)")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("set-targets", help="weekly original-post targets per platform")
    p.add_argument("--x", type=int)
    p.add_argument("--linkedin", type=int)
    p.set_defaults(func=cmd_set_targets)

    sub.add_parser("status", help="totals, this week vs targets, drafts waiting").set_defaults(func=cmd_status)
    sub.add_parser("episodes", help="every episode with its posts").set_defaults(func=cmd_episodes)
    sub.add_parser("next", help="next episode number and the commit to diff from").set_defaults(func=cmd_next)

    p = sub.add_parser("new-episode", help="create an episode and its draft folder")
    p.add_argument("--title", required=True)
    p.add_argument("--pillar", required=True, choices=PILLARS)
    p.add_argument("--summary")
    p.add_argument("--source", action="append", help="where the material came from, e.g. git:6049a2f or 'user notes'; repeatable")
    p.add_argument("--since-commit", help="HEAD commit when this episode was written, so the next one can diff from it")
    p.set_defaults(func=cmd_new_episode)

    p = sub.add_parser("check", help="lint a draft without registering it")
    p.add_argument("file")
    p.add_argument("--platform", required=True, choices=sorted(PLATFORM_CODES))
    p.add_argument("--premium", action="store_true", help="X Premium long-post limit")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("add-post", help="register a draft file under an episode")
    p.add_argument("--episode", type=int, required=True)
    p.add_argument("--platform", required=True, choices=sorted(PLATFORM_CODES))
    p.add_argument("--format", required=True, choices=FORMATS)
    p.add_argument("--file", required=True)
    p.add_argument("--hook", help="defaults to the first line of the file")
    p.set_defaults(func=cmd_add_post)

    p = sub.add_parser("mark-posted", help="record that a draft went live")
    p.add_argument("id")
    p.add_argument("--url")
    p.add_argument("--at", help="ISO time it went live, default now")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_mark_posted)

    p = sub.add_parser("mark-skipped", help="record that a draft will not be posted")
    p.add_argument("id")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_mark_skipped)

    p = sub.add_parser("metrics", help="record numbers read off X or LinkedIn analytics")
    p.add_argument("id")
    for field in METRIC_FIELDS:
        p.add_argument(f"--{field.replace('_', '-')}", dest=field, type=int)
    p.set_defaults(func=cmd_metrics)

    p = sub.add_parser("list", help="list posts")
    p.add_argument("--episode", type=int)
    p.add_argument("--platform", choices=sorted(PLATFORM_CODES))
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
