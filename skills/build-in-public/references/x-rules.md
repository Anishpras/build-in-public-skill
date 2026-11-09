# X Rules

Everything marked "code" comes from xAI's published For You recommendation code: [`github.com/xai-org/x-algorithm`](https://github.com/xai-org/x-algorithm). The values were read on 9 November 2026 from commit `3b6919f87532` of `home-mixer/params/param.rs`.

These are the code's *default* values. Production values sit behind runtime flags (`rust_home_mixer_*`) and can differ. Treat them as direction, not gospel.

## How a post gets scored (code)

The model predicts how likely each viewer is to take each action. The score is the sum of each prediction multiplied by its weight.

A comment in the code warns against a common misreading: weights apply to *probabilities*, not raw counts. So "1 reply = 7 likes" is wrong. A reply is much rarer than a like, so its weight is bigger.

Default weights:

| Action | Weight | What it means for writing |
|---|---|---|
| share via copy link | 20.0 | The highest positive weight. Write things people want to send to someone. |
| reply from someone the author follows *and* who follows back | 5.0 + 15.0 boost | Replies from mutual follows count most of all. |
| reply | 5.0 | Real questions and real takes. |
| quote | 5.0 | Opinions and frameworks people want to add to. |
| share via DM | 5.0 | "Send this to your cofounder." |
| follow author | 4.0 | Consistent topics make people follow. |
| share | 2.118 | |
| repost | 1.0 | |
| like | 0.708 | A weak signal. Don't optimize for it. |
| click dwell time / click / open link | 0.385 / 0.274 / 0.2 | Opening a link is slightly *positive*. There is no explicit link penalty in the code. |
| profile click, video open | 0 | |
| bookmark | not a weighted head in the default value model | Self-bookmarking does nothing. |
| not interested | −53.07 | Bait, spam, off-topic posts and over-posting make people tap this. |
| mute author | −58.8 | |
| block author | −31.2 | |
| report | −234.0 | |

## Rules that follow

1. **Small accounts get a 2-hour exploration window on original posts** (code: `home-mixer/scorers/author_cold_start.rs`, on by default). Feed slots 15–16 are reserved for posts that meet all of these conditions:
   - original, not a reply or a repost
   - from an author with ≤50,000 followers
   - less than 2 hours old
   - fewer than 200 impressions

   So:
   - The story goes in the main post, not in a reply.
   - Post when your audience is online.
   - Stay around for the first 2 hours and answer every reply.

   The "30-minute window" advice going around is wrong about the length.
2. **Coordinated engagement doesn't count** (code comment in `param.rs`). Engagement only counts when the post was served in the Home Timeline. "Directly navigating to a post (i.e., coordinating via groupchat) has no ranking impact."
   - Don't DM a post to friends to "boost" it.
   - Don't join pods.
   - X also announced an engagement-farming policy in April 2026.
3. **Negative feedback costs a lot.** Avoid these, because they trigger "not interested" or mute:
   - engagement bait ("comment YES", "like if…")
   - off-topic rage bait
   - repeats
4. **Mutual follows matter.**
   - Spend 15–30 minutes a day replying thoughtfully to people in your space.
   - Follow back the people you actually talk with.
   - That's where the +15 reply boost comes from.
5. **Retrieval reads your text** (Grok-based embeddings). Stay on 2–3 topics so X learns who to show you to.
6. **Links.** X leadership (Nikita Bier and Elon Musk, July 2026) say there has been no link penalty for over a year, and the code has no explicit one. Link posts still tend to get fewer replies and likes because people leave the app, and third-party data conflicts.
   - Default: put the story in the main post and the link in the first self-reply.
   - Test a link in the main post once you have your own analytics.
7. **Hashtags: 0, or 1 at most.** Musk asked people to stop using them in December 2024. The ranker reads the text itself, so hashtags add nothing. There's no evidence for the "3+ hashtags trips a spam filter" claim, but there's no reason to use them either.

## Formats

- **Single post:** ≤280 weighted characters without Premium. Links count as 23, and emoji and CJK characters count 2. `ledger check` counts this for you. X has no "see more" fold, so the first line has to land the point.
- **Thread:** 3–7 parts. Part 1 must stand alone, because it's the one ranked and shown. Each part should earn the next. End with what happens next, plus the link in a final self-reply.
- **Screenshot or screen recording:** native media, not a link to it.
- **Real question:** use it only when you'll use the answers (naming, a UI choice, pricing, which segment to serve first). Reply to every answer.

## Hook shapes (fill with real material only)

| Shape | Skeleton | Earns |
|---|---|---|
| Build confession | "Spent [time] on [unglamorous thing]. Here's why it mattered: …" | replies |
| Decision with trade-off | "Chose [A] over [B] for [part]. Gave up [cost]. Got [benefit]." | replies, quotes |
| Before/after | screenshot + "[old] → [new]. The change: …" | shares |
| Wrong assumption | "I assumed [belief]. Then [evidence]. Now [change]." | replies |
| Mini-list | "[N] things I learned shipping [thing]:" + one line each | shares, follows |
| Customer insight | "Talked to [N] [ICP]. [What surprised you]." Only with real conversations. | shares, follows |
| Point of view | "[Common belief in your market] is backwards for [segment]. Here's what we see: …" | quotes, replies |
| Real question | "Stuck on [specific choice]. [A] or [B]? Context: …" | mutual replies |
