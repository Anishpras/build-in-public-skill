# LinkedIn Rules

## How the feed works now

LinkedIn rebuilt its feed and described it in an engineering post by Hristo Danchev on 12 March 2026:

- **Retrieval:** One LLM-based dual encoder embeds each post's text, plus the author's profile and headline, and matches them to members.
- **Ranking:** A "Generative Recommender" reads more than 1,000 of each member's past interactions to predict what they'll engage with next.

LinkedIn hasn't published weights between signals. Anything claiming exact numbers is a guess.

## What follows from that

1. **Your headline and topics decide who sees you.**
   - Use a headline like "Building [product]: [outcome] for [ICP]".
   - Keep posts to 2–3 topics: your build, your customers' problem, and your craft.
   - If posts wander across unrelated topics, the retrieval model can't place you.
2. **Dwell time and real comments matter more than reactions.** Write posts people read to the end, and reply to every comment, ideally within the first hour.
3. **Links: the data conflicts.**
   - Metricool (577K posts) found link posts got about 13.6% more interactions.
   - Hootsuite's experiment found about 6x more reach for posts without links, but its sample was skewed.
   - Magicpost (567K posts, 2026) found 414 vs 795 median impressions for posts with a link preview vs none.

   Default:
   - Don't use a preview card in the post.
   - Write the domain as plain text, or put the link in the first comment.
   - Test it both ways once you have numbers.
4. **Cadence:** about 3 posts a week, and never 2 on the same day. Never delete and repost to "reset" a post.
5. **No pods or bait.** Don't use "comment 'X' and I'll DM you", reaction pods, or tag-dumping. LinkedIn's policies cover inauthentic engagement, and readers can tell.
6. **Hashtags:** 0–3 at the end. They make little difference.

## Shape of a good post

- **The first ~210 characters are the hook.** That's roughly what shows before "…see more". Make one specific claim, tension or result. Don't open with "I'm excited to share".
- **Body:**
  - 120–300 words.
  - Short paragraphs of 1–3 lines.
  - Concrete details: what you built or learned, why, what it cost, and what you'd do differently.
- **End** with what's next, or a real question you want answered. Not "Thoughts?".
- **Voice:** first person, plain and calm. LinkedIn tolerates more context than X, so use it to explain the reasoning behind decisions.

## Formats

- **Text, or text with one image:** the default. Use a screenshot of the real thing.
- **Document carousel (PDF):** good for frameworks and lessons, like "5 decisions behind our pricing". It holds dwell time. Use 6–10 slides with one idea per slide.
- **Native video:** a demo or screen recording, uploaded directly, not linked. Add captions, because most people watch muted.
- **Poll:** only if you'll use the answer.

## Match the platform to the audience (GTM)

- **B2B buyers, operators, partners and investors:** LinkedIn is usually the primary channel. Lead with customer problems, decisions and proof.
- **Developers, indie hackers and tech early adopters:** X is usually primary, and LinkedIn is for credibility.
- **Consumers:** neither platform is usually where your users are. Use them for credibility, partners, hiring and investors, and meet users where they actually spend time.
