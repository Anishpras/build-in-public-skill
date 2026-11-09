# build-in-public

A skill for Claude Code (and other agents that read `SKILL.md`). It turns what you actually shipped, decided, learned or measured into **X and LinkedIn posts**, written as numbered episodes. It keeps a **local ledger** of every draft, what you posted, and how each post did.

It's built for founders and GTM people doing founder-led marketing. The X rules come from **X's own open-sourced ranking code**, not from "growth hacks" threads.

It **drafts and tracks. It never posts.** Everything stays in your project.

## What it does

- **Writes episodes from real material.** It reads your recent commits (`git log` since the last episode) and asks you one question for the "why", the cost or the surprise. Then it writes a separate X version and LinkedIn version.
- **Won't invent things.** No made-up numbers, customers, quotes or backstory. Planned features are described as planned. A `context.md` file holds your product facts and what's live vs planned.
- **Tracks everything** in `build-in-public/ledger.json`:
  - episodes, drafts, posted / skipped status, URLs
  - this week's count vs your targets (default: X 7, LinkedIn 3)
  - metrics you read off X or LinkedIn analytics
- **Lints every draft:**
  - X's weighted character count (links = 23, emoji = 2)
  - links in the main post
  - hashtag count
  - engagement bait
  - common AI tells, including em dashes, "it's not X, it's Y" and "excited to announce"

## Why the X rules are different

xAI publishes the For You recommendation code at [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm). These are the default values in `home-mixer/params/param.rs`, read on 9 November 2026. Production values sit behind runtime flags and can differ.

| Popular advice | What the code says |
|---|---|
| "Replies are worth 27x a like" | That's from Twitter's **2023** code. Current defaults: like **0.708**, reply **5.0**, reply from a mutual follow **5.0 + 15.0**, quote **5.0**, share via DM **5.0**, **share via copy link 20.0**, follow **4.0**, repost **1.0**. The code comment says weights apply to predicted *probabilities*, so "1 reply = N likes" is a misreading. |
| "Your post dies if nobody engages in 30 minutes" | `author_cold_start.rs` reserves feed slots for **original** posts from accounts with **≤50K followers**, under **2 hours** old and with fewer than 200 impressions. The window is 2 hours, and it's an exploration boost. |
| "DM your post to friends for early momentum" | Code comment: engagement must happen on a post served in the Home Timeline. *"Directly navigating to a post (i.e., coordinating via groupchat) has no ranking impact."* |
| "Bookmark your own post" | Bookmarks aren't a weighted head in the default value model. |
| "Ask divisive questions to farm replies" | The negative weights are large: not interested **−53.07**, mute **−58.8**, block **−31.2**, report **−234**. Bait backfires. |
| "Links cut your reach 50%" | The code has no explicit link penalty, and opening a link is weighted +0.2. X leadership said in July 2026 that links haven't been penalized for over a year. Link posts still tend to get fewer replies, so the skill defaults to putting the link in the first self-reply. You can test it the other way. |

The LinkedIn rules follow LinkedIn's March 2026 engineering post on its rebuilt feed (LLM retrieval over post text and the author's headline, plus a generative recommender over member history), plus the public link-reach studies, which conflict. The skill tells you when the evidence is mixed.

## Install

**Claude Code plugin:**

```
/plugin marketplace add anishpras/build-in-public-skill
/plugin install build-in-public@build-in-public-skill
```

**[skills CLI](https://github.com/vercel-labs/skills)** (Claude Code, Codex, Cursor and other agents):

```bash
npx skills add anishpras/build-in-public-skill        # this project
npx skills add anishpras/build-in-public-skill -g     # all projects
```

**Manual:**

```bash
git clone https://github.com/anishpras/build-in-public-skill
cp -r build-in-public-skill/skills/build-in-public ~/.claude/skills/   # or <your-project>/.claude/skills/
```

Requires Python 3.8+ (standard library only) and git.

## Use it

Open your agent in your product's repo and talk normally:

- "Set up build in public for this project." Creates `build-in-public/`, then fills `context.md` with you from your README, site copy and git history.
- "Write the next episode."
- "Turn today's pricing change into a LinkedIn post and an X thread."
- "Posted E003-X1 https://x.com/you/status/…" Logs it.
- "E003-X1 got 4,100 impressions, 38 replies, 12 follows." Records the metrics.
- "How many posts this week? What's pending? What should I post today?"

Each episode lands in `build-in-public/episodes/NNN-slug/`:

- `x-1.md`: exact text to paste. Thread parts are separated by `---`.
- `linkedin-1.md`: the LinkedIn post.
- `notes.md`: first comment, media and timing.

`build-in-public/` holds unpublished drafts. If your repo is public, add it to `.gitignore`.

## The ledger CLI

The skill drives this for you. You can also run it directly:

```bash
L=~/.claude/skills/build-in-public/scripts/ledger.py
python3 $L init --project "Acme"          # build-in-public/ + context.md + ledger.json
python3 $L status                          # totals, this week vs targets, drafts waiting
python3 $L next                            # next episode number + `git log <since>..HEAD`
python3 $L new-episode --title "Pricing v2" --pillar decision --since-commit $(git rev-parse --short HEAD)
python3 $L check build-in-public/episodes/001-pricing-v2/x-1.md --platform x
python3 $L add-post --episode 1 --platform x --format thread --file build-in-public/episodes/001-pricing-v2/x-1.md
python3 $L mark-posted E001-X1 --url https://x.com/you/status/123
python3 $L metrics E001-X1 --impressions 4100 --replies 38 --follows 12
python3 $L episodes                        # every episode and its posts
python3 $L set-targets --x 5 --linkedin 3
```

**Pillars:** `build-log`, `decision`, `lesson`, `customer-insight`, `point-of-view`, `proof`, `numbers`, `launch`.

## Repo layout

```
skills/build-in-public/
  SKILL.md                      workflow and rules for the agent
  scripts/ledger.py             ledger + draft linter (stdlib, no network)
  references/x-rules.md         X ranking facts from the code, formats, hook shapes
  references/linkedin-rules.md  LinkedIn feed facts, cadence, formats
  references/episode-formats.md pillars and episode skeletons
  assets/context-template.md    copied to build-in-public/context.md on init
.claude-plugin/                 plugin + marketplace manifests
tests/test_ledger.py            python3 -m unittest discover -s tests
```

## Caveats

- **The X weights are code defaults** from a specific date. X can change them, or override them in production. They tell you the direction, not exact multipliers.
- **LinkedIn publishes no weights.** The LinkedIn guidance is evidence-weighted judgment, and the skill says so.
- **Not affiliated with X Corp., xAI or LinkedIn.**

## License

MIT
