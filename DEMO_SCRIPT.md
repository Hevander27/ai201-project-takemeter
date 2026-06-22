# TakeMeter — Demo Video Script (~3.5 min)

Target length: 3–5 minutes. Have the Colab notebook open (run through Section 4),
plus the in-Colab Gradio UI (README §9) and the README's §5 tables visible.

---

## 0:00 — Intro (20s)
> "This is TakeMeter, a fine-tuned text classifier that rates discourse quality
> in the r/fantasyfootball subreddit. It sorts a comment into one of three types:
> **analysis** — an argument backed by real evidence; **hot_take** — a bold claim
> with no support; and **reaction** — a short emotional response. I fine-tuned
> DistilBERT on 230 hand-labeled comments and compared it to a zero-shot Llama-3.3
> baseline."

## 0:20 — Live classification, 3–5 posts (75s)
Open the Gradio UI (or run `interface.py`). Type or click each example so the
**label and confidence are visible on screen**.

> "Let me run a few comments through it live."

1. Paste: *"Kelce had 3 TDs and ~90 receptions — the TD count is incredibly low vs
   his history, he's declining but still useful."*
   > "Predicted **analysis**, 0.99 confidence."

2. Paste: *"Chase Brown is a top 10 back, people just don't wanna have that convo
   yet."*
   > "Predicted **hot_take** — a bold ranking with nothing behind it."

3. Paste: *"Niners are finished lol"*
   > "Predicted **hot_take** — and that one's actually wrong, I'll come back to it."

## 1:35 — One CORRECT prediction, explained (35s)
Back to the Kelce example.
> "The Kelce comment is a clean correct call. The model predicts **analysis** at
> 0.99, and that's reasonable: the comment cites specific receiving stats — three
> touchdowns, around ninety catches — and contrasts them against the player's
> own historical numbers. That's evidence-backed reasoning, which is exactly my
> definition of analysis. The high confidence is justified."

## 2:10 — One INCORRECT prediction, explained (40s)
Back to "Niners are finished lol" (and/or the README §5.5 row).
> "Here's a revealing miss. 'Niners are finished' is pure emotional reaction —
> there's no claim, no evidence, just venting. But the model predicts **hot_take**
> with 0.97 confidence. This is the model's biggest blind spot: it learned that
> short, claim-shaped text means hot_take, so it pulls emotional reactions into
> that bucket — and it does it confidently, not hesitantly. Five of my nine test
> errors are exactly this reaction-to-hot_take confusion."

## 2:50 — Evaluation report walkthrough (45s)
Show README §5 tables.
> "On the held-out test set, the zero-shot baseline scored 69% accuracy but
> basically never predicted hot_take — recall of 0.15. After fine-tuning,
> accuracy rose to 74% and macro-F1 from 0.62 to 0.72, and hot_take recall jumped
> from 0.15 to 0.77 — that was the whole goal. The confusion matrix shows the
> remaining weakness: reaction gets misread as hot_take. So fine-tuning taught the
> model the analysis-versus-hot_take boundary the baseline couldn't, but it
> overcorrected on reactions."

## 3:35 — Close (10s)
> "Everything — the dataset, the planning doc, the evaluation report, and a
> deployed Gradio interface — is in the GitHub repo. Thanks for watching."

---

### Checklist (assignment requires all of these on screen)
- [ ] 3–5 posts classified with **label + confidence visible**
- [ ] one **correct** prediction narrated (Kelce → analysis 0.99)
- [ ] one **incorrect** prediction narrated (Niners → hot_take 0.97)
- [ ] brief walkthrough of the evaluation report (README §5)
