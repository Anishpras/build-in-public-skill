# Episode Formats

Pick the pillar from what the material really is. Over any 2 weeks, aim for a mix:

- about half build-log or decision
- about a quarter lesson or customer-insight
- about a quarter point-of-view or proof
- numbers whenever you have real ones

## Pillars (`--pillar`)

| Pillar | What counts | Good on |
|---|---|---|
| `build-log` | Something shipped or changed | X thread, LinkedIn post with a screenshot |
| `decision` | A choice between options, with the trade-off (stack, pricing, positioning, hiring, segment) | Both platforms; LinkedIn gets the "why" |
| `lesson` | Something learned the hard way (bug, wrong assumption, cost, failed experiment) | X single post, LinkedIn post |
| `customer-insight` | What users or buyers actually do or say (real conversations, with permission for quotes) | Both |
| `point-of-view` | Your take on the market or category, backed by what you've seen | LinkedIn first, X as a sharp single post |
| `proof` | A real result a customer got, or a real before/after (never invented) | Both |
| `numbers` | A real metric moved (signups, revenue, churn, cost, reach), with context | X single post, LinkedIn post |
| `launch` | A milestone: beta, first customer, pricing live, a major release | Both, plus a pinned post |

## Episode skeletons

### build-log
- **X:** a hook with the outcome, then 2–4 parts covering what changed, the unexpected bit and what's next. The link goes in the last self-reply.
- **LinkedIn:**
  1. A 1-line hook (the outcome, or the surprising part).
  2. The context, in 2 lines.
  3. What you built, in 3–5 short lines with real specifics.
  4. Why it matters for the customer.
  5. What's next.
  6. Optional real question.

### decision
- **X:** "Chose A over B for [part]. Gave up [cost]. Got [benefit]. [One line on why]."
- **LinkedIn:**
  1. The choice.
  2. The options you considered.
  3. What tipped it.
  4. What you're giving up.
  5. How you'll know if it was wrong.

### lesson
- **X:** "I assumed [X]. [What happened]. Now I [change]."
- **LinkedIn:** the same arc, plus how a reader can avoid it.

### customer-insight
- Only from real conversations, support tickets, surveys or analytics the user shares.
- "Talked to 6 [ICP]. 4 said [thing]." Use this only if those are the real numbers.

### point-of-view
- Name the common belief, say where it breaks for your segment, and back it with what you've actually seen.
- Contrarian is fine. Contrarian without evidence is noise.

### proof
- The customer, the before, the after, and what changed in between.
- Only real results, and named only with permission. Otherwise anonymize ("a 12-person agency").

### numbers
- The real number, the time period, what you think caused it, and what you'll try next.
- Never round up or leave out the denominator.

### launch
- What's live today, who it's for, and the one thing to do next.
- Say clearly what's still coming.

## Mining a repo for the first episodes

Run `git log --reverse --format='%h %ad %s' --date=short`, then group commits into 3–5 stories:

- the first deploy
- the hardest piece
- a decision you'd defend
- something you rebuilt
- the unglamorous work (auth, billing, consent, tests) that buyers never see but would care about

Each story is an episode candidate. Ask the founder for the "why" behind the ones they like.

**Episode 0** is the founder's "what I'm building and why". Don't write it until `context.md` has their real reason.
