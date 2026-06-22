# TakeMeter — Planning

**Project:** Fine-tuned discourse-quality classifier for r/fantasyfootball
**Author:** Hevander Da Costa
**Date:** 2026-06-22

> This is my working/design document. Decisions, label definitions, edge-case
> rules, and annotation notes live here. The README is the final polished report.

---

## 1. Community

I chose **r/fantasyfootball**, a ~3M-member subreddit where people manage fantasy
football teams and constantly debate roster decisions, player value, and weekly
matchups. It's a strong fit for a discourse-quality classifier because the
content is text-heavy and the *quality of reasoning* varies enormously: the same
thread will contain a deeply-researched player breakdown (snap share, target
data, matchup history) sitting right next to a one-line "START HIM, easy
league-winner" with zero support, and a panicked "do I bench my RB1??" question.
That natural spread between **reasoned argument**, **unsupported assertion**, and
**decision-seeking question** is exactly the distinction the community itself
cares about — regulars routinely call out "lazy take" vs. "great writeup."

---

## 2. Labels

I use **three** mutually exclusive labels: `analysis`, `hot_take`, and
`reaction`. (I originally planned an `advice_seeking` label for start/sit
questions, but after pulling a random sample of r/fantasyfootball *comments* I
found almost none — advice questions live in megathread top-level posts, not the
comment stream. Rather than force a lopsided scrape, I switched to `reaction`,
which fits the actual comment data and mirrors the canonical sports taxonomy.)
These three capture the real spread of discourse quality in the comment threads.

> ⚠️ Replace the example posts below with **real posts you collect** before
> checking off Milestone 1. These are representative placeholders.

### `analysis`
**Definition:** The post makes a structured argument backed by *specific,
verifiable evidence* — snap counts, target share, route participation, matchup
stats, usage trends, or historical comparison — such that the reasoning would
stand even if you stripped out the opinion.

- *Example 1:* "I'm buying low on Pittman. His target share jumped from 19% to
  27% over the last three weeks, he's running 88% of routes, and the Colts face
  three bottom-10 pass defenses in the playoff weeks. The TD regression is coming."
- *Example 2:* "Don't drop Zamir White yet. Jacobs is on a 28-touch pace and
  RBs at that workload have a ~30% in-season injury rate historically; White is
  the clear handcuff and would be a league-winner with one injury."
- *Uncertain:* "Pollard's been bad but he's still seeing 70% of snaps." — one
  real stat, but no actual argument built on it. (See edge cases.)

### `hot_take`
**Definition:** A bold, confident opinion or prediction asserted *without*
genuine supporting evidence. The claim might be correct, but the post asserts
rather than argues; any "evidence" is vague, cherry-picked, or decorative.

- *Example 1:* "CMC is the most overrated pick in the first round, mark my words.
  Fade him."
- *Example 2:* "Anthony Richardson is a top-5 QB rest of season, it's not even
  close. Trust me."
- *Uncertain:* "Is anyone else benching Mahomes this week??" — phrased as a
  question but it's rhetorical, asserting a bold stance. (See edge cases.)

### `reaction`
**Definition:** A short, emotional response to a player, play, or event —
excitement, frustration, celebration, or disbelief — with little to no argument.
The post is expressing a feeling in the moment, not making or defending a claim.

- *Example 1:* "Kamara got 1-2 years left before he's likely outta the league!!"
- *Example 2:* "Welp, there goes my season. Benched him for 30 lmao."
- *Uncertain:* "His production has significantly dropped." — brief and judgmental,
  but it's stating an evaluation rather than venting a feeling. (See edge cases.)

---

## 3. Hard Edge Cases

These are the boundaries I expect to give me real pause. I'm writing the decision
rules **now**, before annotating, so I label consistently.

**Edge case A — brief evaluative opinion: `hot_take` vs `reaction`.**
*Example:* "His production has significantly dropped, top 10 at best."
Could be `reaction` (short, dismissive) or `hot_take` (an evaluative claim).
**Decision rule:** If the post asserts an *evaluation or ranking* of a player's
value/future (even briefly), it's a claim → `hot_take`. If it's an in-the-moment
*emotional* outburst tied to a specific event ("welp, season over lmao") with no
evaluative claim → `reaction`. Brief but judgmental, no emotion → **hot_take**.

**Edge case B — bold claim with one decorative stat: `analysis` vs `hot_take`.**
*Example:* "Adams is a top-5 WR, he had 11 targets last week." (one stat, used for
effect, no real argument)
**Decision rule:** If the evidence is specific and genuinely *supports* the claim
as part of reasoning → `analysis`. If the evidence is vague, cherry-picked, or
just decorative (one stat dropped in to sound credible) → `hot_take`. A single
out-of-context stat behind a sweeping claim → **hot_take**.

**Edge case C — emotional post that also reasons: `reaction` vs `analysis`.**
*Example:* "I'm so done with Kamara, he can't break a tackle anymore — 2.9 yards
per carry and a 38% snap share since week 4, it's over."
Could be `reaction` (emotional framing) or `analysis` (real stats + reasoning).
**Decision rule:** Strip the emotional framing. If specific, verifiable evidence
and a real argument remain → `analysis`. If removing the emotion leaves only a
bare assertion → `hot_take`; if it leaves nothing but the feeling → `reaction`.
The example has genuine usage stats supporting the claim → **analysis**.

*(I'll add at least 3 real difficult cases I hit during annotation in Milestone 3,
in the table below.)*

### Difficult cases encountered during annotation
| # | Post (abbreviated) | Could be | Decided | Why |
|---|--------------------|----------|---------|-----|
| 1 | "His production has significantly dropped. I'd argue maybe top 10, but definitely not top 5." | hot_take / analysis | **hot_take** | It's an evaluative *ranking* claim with no specific evidence behind the drop. Per Edge Case A, brief-but-judgmental with no support → hot_take. |
| 2 | "Wasn't there a game ~2 years ago where he had 13 catches for 30 yards? Lol that's what I think when people say 'but bad QB play.' Dude gets his no matter what lmao" | analysis / hot_take | **hot_take** | It gestures at a specific game but the recall is fuzzy ("wasn't there…") and the framing is emotional ("lmao", "gets his no matter what"). The stat is decorative, not a real argument → hot_take, not analysis. |
| 3 | "Welcome to mediocre / Signed, A cowboys fan" | reaction / hot_take | **reaction** | There's an implied claim (the team is mediocre) but the post is pure emotional snark with no argument. Dominant tone is venting, not asserting a defensible take → reaction. |

> Add more here as you review. You should personally confirm/replace these three
> with cases that genuinely gave *you* pause during your review pass.

---

## 4. Data Collection Plan

- **Source:** Public r/fantasyfootball comments only, pulled from the public
  PullPush.io Reddit archive API (no auth required). Cleaned: dropped
  `[deleted]`/`[removed]`, bot comments, and links; de-duplicated; whitespace
  normalized. No private/authenticated content.
- **Two-pool collection (important).** A random pull of *medium-length* comments
  (60–1200 chars) skewed heavily toward `analysis` and produced almost no
  `reaction` — because reactions are short. So I collected in two pools:
  (1) medium comments for `analysis`/`hot_take`, and (2) a large pool of *short*
  comments (12–110 chars) to harvest genuine `reaction` and short `hot_take`
  posts. This is exactly the "read the data first, then revise" check the brief
  warns about — the random stream did not naturally yield a balanced 3-class set.
- **Final dataset:** 230 labeled examples in `takemeter_dataset.csv`
  (`text`, `label`, `notes`, `source`, `permalink`). Distribution:
  **analysis 85 (37%), hot_take 84 (37%), reaction 61 (27%)** — every class
  ≥20%, none >70%. The notebook does the 70/15/15 split.
- **AI pre-labeling disclosure.** All 230 labels were produced as an AI pre-label
  pass (Claude, using the definitions and edge-case rules above) and **must be
  reviewed and corrected by me** before training, per the AI Tool Plan. ~22% of
  the random stream was `off_topic` (platform/app talk, league logistics,
  spelling banter) and was dropped, not labeled — see README AI usage section.

---

## 5. Evaluation Metrics

- **Overall accuracy** — headline number, but *insufficient alone*: if the data
  is imbalanced (likely — advice questions are everywhere), a model can score
  high accuracy by just predicting the majority class.
- **Per-class precision / recall / F1** — required to see whether each
  distinction is actually learned. Recall per class catches a label collapsing
  to near-zero.
- **Macro-F1** — my primary single metric, because it weights all three classes
  equally regardless of frequency. This is the right call for an imbalanced,
  subjective task where I care about every label, not just the common one.
- **Confusion matrix** — to see *directional* confusion (e.g. is the model
  systematically calling `analysis` → `hot_take`? that tells me exactly which
  boundary it hasn't learned).

Why these and not just accuracy: the task is subjective and the classes are
unbalanced, so I need per-class + macro-F1 to know the model learned all three
distinctions rather than gaming the base rate.

---

## 6. Definition of Success

- **Primary bar:** the fine-tuned model must **beat the zero-shot Groq baseline
  on macro-F1** on the locked test set. If fine-tuning doesn't beat zero-shot,
  it didn't add value and I'll say so.
- **Quantitative target:** macro-F1 **≥ 0.70**, with **every class F1 ≥ 0.60**
  (no class collapsing), and overall accuracy clearly above the majority-class
  rate.
- **"Good enough for deployment" in a real community tool:** I'd want macro-F1
  **≥ 0.75** and no class below 0.65, *and* I'd only trust it as a **triage/flagging
  aid** (e.g. surfacing likely high-effort `analysis` posts) — not as an
  autonomous moderator. A subjective discourse-quality call should keep a human
  in the loop.

These are specific enough that at the end I can objectively check: did I beat the
baseline on macro-F1, and did I clear 0.70 macro / 0.60-per-class?

---

## AI Tool Plan

There's no application code to generate in this project, so AI assistance shows up
in three specific places:

**1. Label stress-testing (before annotating).**
I'll give Claude my three definitions + edge-case rules and ask it to generate
8–10 posts that deliberately sit on the `analysis`/`hot_take` and
`advice_seeking`/`analysis` boundaries. If I can't cleanly classify what it
produces, my definitions are too loose and I tighten them *before* labeling 200.

**2. Annotation assistance (pre-labeling).**
I plan to use Claude to **pre-label batches** of ~25 unlabeled posts at a time
using my exact definitions, then **manually review and correct every single one**
— pre-labels are a first pass, not the answer. I'll track which rows were
pre-labeled with a flag in the `notes` column (`prelabeled`) and disclose the
whole workflow in the README's AI usage section. (If review starts feeling like
rubber-stamping, I'll switch to fully manual labeling.)

**3. Failure analysis (after evaluation).**
I'll paste my list of misclassified test examples into Claude and ask it to find
*systematic* patterns (label pair confused most, post length, sarcasm,
short/low-info posts). Then I verify each proposed pattern by re-reading the
actual examples myself — I only keep patterns I can confirm in the data, and I'll
note in the report anything Claude suggested that I had to discard.

---

## Stretch features (update before starting any)
- [ ] Inter-annotator reliability (2nd labeler on 30+, Cohen's kappa)
- [ ] Confidence calibration
- [ ] Error pattern analysis (systematic, beyond individual errors)
- [ ] Deployed interface (post in → label + confidence out)
