"""Shared domain knowledge injected into the distribution-facing specialists.

This is the difference between an LLM that "writes LinkedIn posts" and a specialist that
understands how LinkedIn actually distributes content. Kept in one place so the Strategist,
Copywriter, and Critic reason from the same, current mental model instead of generic advice.
Update this as the platform changes — it is deliberately factual, not fluffy.
"""

LINKEDIN_MECHANICS = """LINKEDIN DISTRIBUTION MECHANICS (reason from these, they are how reach actually works):
- The feed ranks by predicted MEANINGFUL ENGAGEMENT and DWELL TIME, not by likes. A post that
  makes people stop, expand "see more", and read to the end outranks one that collects quick likes.
- The first ~60–90 minutes after posting (the "golden hour") disproportionately determine total
  reach. Early comments and reshares from relevant people are the strongest signal.
- Comments (especially substantive replies) and reshares are worth far more than likes. A genuine
  question or a mild, defensible contrarian take earns comments; bland "agree?" bait does not and is
  penalized as engagement bait.
- The first 2 lines (everything before "see more") are the single biggest reach lever — they must
  earn the click. No throat-clearing, no context-setting preamble.
- Outbound links IN the post body suppress reach (they pull people off-platform). Put the link in the
  first comment, or invite a comment/DM instead. Never bury a call-to-action behind an in-body link.
- Formats by dwell potential: text posts that reward reading, and document/PDF carousels, tend to earn
  high dwell and reach; a single strong image supports a text post; native video is variable; a bare
  link post reaches least. Match format to the idea, not to novelty.
- FOLLOWERS grow from FOLLOW-WORTHY posts — a distinct point of view, a repeatable series, or value a
  reader wants more of — not merely LIKE-WORTHY posts. Reach without a reason to follow is a leaky bucket.
- Topical consistency compounds: LinkedIn routes a post to people interested in its topic, so a focused
  niche builds a coherent audience while scattered topics confuse routing and dilute reach.
- Post when THIS audience is actually online (their timezone and habits — for most B2B audiences,
  Tue–Thu mornings local time) so the golden hour lands while they're scrolling."""


GROWTH_STAGE_PLAYBOOKS = """GROWTH-STAGE PLAYBOOKS (priorities shift with scale — do not run a scale playbook on a foundation account):
- foundation (0–500 followers): nail POSITIONING and prove the account is alive. Establish who this is
  for and the one thing it's about. Volume matters less than a clear, repeatable POV. Small numbers are
  noisy — treat everything as a probe.
- signal (500–2k): find what RESONATES. Test formats and hooks deliberately, read which topics earn
  comments and follows, and start doubling down. This is a learning stage.
- reach (2k–10k): SCALE the winners. Ride relevant trends fast, repurpose proven angles, increase
  cadence only while reach-per-post holds.
- authority (10k–100k): go DEEP. Point-of-view pieces, series, original frameworks, taking positions.
  You are competing on insight, not frequency.
- scale (100k+): multi-format engine, community, systematic repurposing, and protecting the brand."""
