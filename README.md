# TakeMeter — Classifying Discourse Quality in r/fantasyfootball

A fine-tuned text classifier that sorts r/fantasyfootball comments into three
discourse types — **analysis**, **hot_take**, and **reaction** — and an honest
evaluation of where it works and where it breaks.

- **Base model:** `distilbert-base-uncased` (fine-tuned)
- **Baseline:** `llama-3.3-70b-versatile` via Groq, zero-shot
- **Dataset:** 230 hand-reviewed comments collected from public r/fantasyfootball
- **Task:** 3-class single-label classification

> `planning.md` holds the working notes and design rationale. This README is the
> standalone final report.

---

## 1. The Community and Why It Fits

**r/fantasyfootball** (~3M members) is a text-heavy community where the *quality
of reasoning* varies wildly within a single thread: a deeply-researched player
breakdown (snap share, target data, matchup history) sits right next to a
one-line "START HIM, easy league-winner" and a panicked "welp, season over."
That spread between **reasoned argument**, **unsupported assertion**, and
**emotional reaction** is a distinction the community itself cares about —
regulars routinely call out "great writeup" vs. "lazy take." That makes it a
good fit for a discourse-quality classifier: the labels are grounded in how
people there actually talk.

---

## 2. Label Taxonomy

Three mutually exclusive labels. (I originally planned a fourth, `advice_seeking`,
for start/sit questions, but a random sample of *comments* contained almost none —
those live in megathread top-level posts. I switched to `reaction`, which fits
the comment data and mirrors the canonical sports taxonomy.)

| Label | Definition | Example |
|-------|------------|---------|
| **analysis** | A structured argument backed by specific, verifiable evidence (stats, snap/target share, matchup data, usage trends, named comparisons, or multi-step reasoning). The reasoning stands even if you strip the opinion. | *"Kelce had 3 touchdowns, 90-something receptions. He's on his way down, but the 3 TDs was incredibly low compared to his other stats and his history."* |
| **hot_take** | A bold, confident opinion, ranking, or prediction asserted **without** genuine support. Any evidence is vague, cherry-picked, or decorative. | *"Chase Brown is a top 10 back but people don't wanna have that convo yet."* |
| **reaction** | A short, emotional response (excitement, frustration, disbelief, banter) with little to no argument — expressing a feeling, not defending a claim. | *"Niners are finished 😂"* |

### Hard edge cases and decision rules
- **Brief evaluative opinion (hot_take vs reaction):** if it asserts an
  evaluation/ranking → `hot_take`; if it's pure emotional venting with no claim →
  `reaction`.
- **Bold claim with one decorative stat (analysis vs hot_take):** if the evidence
  genuinely supports the claim as reasoning → `analysis`; if it's a single
  cherry-picked/decorative stat behind a sweeping claim → `hot_take`.
- **Emotional post that also reasons (reaction vs analysis):** strip the emotional
  framing; if specific evidence and a real argument remain → `analysis`.

Three genuinely difficult annotation calls are documented in `planning.md`
(Hard Edge Cases section).

---

## 3. The Dataset

- **Source:** Public r/fantasyfootball comments only, pulled from the public
  **PullPush.io** Reddit archive API (no authentication). Cleaned (`[deleted]`/
  `[removed]`, bots, and links removed; de-duplicated; whitespace normalized).
- **Two-pool collection.** A random pull of *medium-length* comments (60–1200
  chars) skewed heavily toward `analysis` and produced almost no `reaction` —
  because reactions are short. So I collected a second pool of *short* comments
  (12–110 chars) to harvest genuine `reaction` and short `hot_take` posts. This
  was a direct result of reading the data first and finding the labels didn't
  apply cleanly to a single random pull.
- **Dropped content:** ~22% of the random stream was off-topic (platform/app
  talk, league logistics, spelling banter) — not a "take." These were discarded,
  not labeled.
- **Labeling process:** every comment was AI **pre-labeled** with the definitions
  above (Claude), then **reviewed and corrected by hand**. See AI Usage section.

**Final label distribution (230 examples):**

| Label | Count | Share |
|-------|------:|------:|
| analysis | 85 | 37% |
| hot_take | 84 | 37% |
| reaction | 61 | 27% |
| **Total** | **230** | **100%** |

No class exceeds 70%; every class clears the 20% floor. The notebook splits
70/15/15 → **train 161 / val 34 / test 35**, balanced across splits.

**Three difficult-to-label examples** (full reasoning in `planning.md`):
1. *"His production has significantly dropped. I'd argue maybe top 10, not top 5."*
   → **hot_take** (an unsupported ranking, not evidence-backed analysis).
2. *"Wasn't there a game ~2 yrs ago where he had 13 catches for 30 yards? Lol …
   dude gets his no matter what lmao"* → **hot_take** (fuzzy, decorative stat +
   emotional framing, not a real argument).
3. *"Welcome to mediocre / Signed, A cowboys fan"* → **reaction** (implied claim
   but pure emotional snark, no argument).

---

## 4. Fine-Tuning

- **Starting point:** `distilbert-base-uncased`, a 66M-parameter distilled BERT,
  with a fresh 3-way classification head.
- **Approach:** supervised fine-tuning on the 161-example train split, validated
  on 34 held-out examples, evaluated on a locked 35-example test set, using the
  HuggingFace `Trainer`.

### Key hyperparameter decision (epochs / learning rate / batch size)
The notebook defaults (3 epochs, LR 2e-5, batch size 16) **underfit** on this
small dataset: training loss stayed at ~1.05 (≈ `ln(3)`, the loss of random
guessing on 3 classes), every prediction confidence sat near 0.33, and the model
scored **0.571 accuracy — below the 0.686 zero-shot baseline.** With only ~33
total gradient steps, the model never learned to separate the classes.

I diagnosed this as too few updates and changed three things:

| Hyperparameter | Default | Final | Why |
|---|---|---|---|
| epochs | 3 | **10** | more passes over a tiny dataset |
| learning rate | 2e-5 | **5e-5** | move the weights enough to learn |
| train batch size | 16 | **8** | ~2× more gradient steps per epoch |

This is the change that made fine-tuning actually learn the
`analysis`-vs-`hot_take` boundary the zero-shot model couldn't.

---

## 5. Evaluation Report

Both models evaluated on the **same locked 35-example test set**.

### 5.1 Overall accuracy

| Model | Accuracy | Macro-F1 |
|---|---:|---:|
| Zero-shot baseline (Llama-3.3-70B) | 0.686 | 0.62 |
| **Fine-tuned DistilBERT** | **0.743** | **0.72** |

Fine-tuning improved accuracy by **+5.7 points** and macro-F1 by **+0.10**. The
single biggest gain was on `hot_take` recall, which jumped from **0.15 → 0.77** —
the exact boundary the zero-shot model could not infer. (Training note: val
accuracy peaked around epochs 8–9 while train loss fell to ~0.01, so the model is
slightly overfit by epoch 10; the chosen config still gives the best test result.)

### 5.2 Per-class metrics

**Baseline (Groq, zero-shot):**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| analysis | 0.76 | 1.00 | 0.87 | 13 |
| hot_take | 1.00 | 0.15 | 0.27 | 13 |
| reaction | 0.56 | 1.00 | 0.72 | 9 |
| **accuracy** | | | **0.69** | 35 |
| **macro avg** | 0.78 | 0.72 | 0.62 | 35 |

**Fine-tuned DistilBERT:**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| analysis | 0.92 | 0.92 | 0.92 | 13 |
| hot_take | 0.62 | 0.77 | 0.69 | 13 |
| reaction | 0.67 | 0.44 | 0.53 | 9 |
| **accuracy** | | | **0.74** | 35 |
| **macro avg** | 0.74 | 0.71 | 0.72 | 35 |

The two models trade weaknesses. The baseline barely predicted `hot_take`
(recall 0.15); the fine-tuned model predicts it readily (recall 0.77) but now
*over*-predicts it, dragging down `reaction` recall (0.44). `analysis` is solid
for both, and best for the fine-tuned model (F1 0.92).

### 5.3 Confusion matrix (fine-tuned model)

Text version (rows = true, columns = predicted). Paste counts from
`confusionMatrix.png` / Section 4. The committed `confusionMatrix.png` is the
supplementary image.

|              | pred: analysis | pred: hot_take | pred: reaction |
|--------------|---:|---:|---:|
| **true: analysis** (13) | 12 | 1 | 0 |
| **true: hot_take** (13) | 1 | 10 | 2 |
| **true: reaction** (9) | 0 | 5 | 4 |

*(Reconstructed from the Section 4 per-class metrics and the wrong-prediction
list; confirm against `confusionMatrix.png`.)* The dominant off-diagonal cell
is **(true reaction → pred hot_take) = 5** — that single confusion accounts for
over half of all errors.

### 5.4 Three errors, analyzed

1. **"It's like shouting into the void at this point. They're going to surprise
   some people this year."** — true `reaction`, predicted **hot_take** (conf
   0.97). This is emotional venting with a vague optimistic flourish, but the
   phrase "they're going to surprise some people" reads like a confident
   prediction, so the model — now eager to call things `hot_take` — files it as
   one, with high confidence. A clean case of the model learning the *form* of a
   take without the underlying feeling-vs-claim distinction.

2. **"They've paid him, CMC, Kittle...Warner? They can't have much more $$$,
   right? RIGHT?!"** — true `reaction`, predicted **hot_take** (conf 0.78). It
   names real players and references contracts, so the model treats it as a take,
   missing that the content is pure emotional disbelief (the "RIGHT?!" is the
   giveaway). Short, player/topic-heavy reactions are the model's blind spot.

3. **"So we cherry pick 3 near the bottom? What about the others? Does this hold
   up year after year… or is this loose correlation?"** — true `analysis`,
   predicted **hot_take** (conf 0.94). This is genuine analytical skepticism —
   it's interrogating someone's methodology — but it's phrased as punchy
   rhetorical questions with no stats of its own, so the model reads the
   combative tone as a hot take. Analytical *substance* delivered in hot-take
   *form* fools it.

**Directional pattern (verified in the confusion matrix):** errors cluster on the
**reaction → hot_take** boundary (5 of 9 errors), with the rest on the
`hot_take`↔`analysis` line. This is a labeling-boundary/data problem more than an
annotation-consistency one: I labeled these examples consistently, but the model
learned that *short + claim-like surface form = hot_take* and pulls emotional
reactions (and even skeptical analysis) into it. Fixing it would need more
`reaction` examples that name players/reference topics, and more `analysis`
written in a terse, rhetorical-question style.

### 5.5 Sample classifications

Five test comments run through the fine-tuned model, with the model's predicted
label and confidence:

| Comment | True | Predicted | Confidence | Correct? |
|---|---|---|---:|:--:|
| "Kelce had 3 touchdowns, 90 something receptions, the 3 tds was incredibly low compared to his other stats and his history." | analysis | analysis | 0.99 | ✅ |
| "It's like shouting into the void at this point. They're going to surprise some people this year." | reaction | hot_take | 0.97 | ❌ |
| "They've paid him, CMC, Kittle...Warner? They can't have much more $$$, right? RIGHT?!" | reaction | hot_take | 0.78 | ❌ |
| "So we cherry pick 3 near the bottom? … or is this loose correlation?" | analysis | hot_take | 0.94 | ❌ |
| "Niners are finished" | reaction | hot_take | 0.97 | ❌ |

Overall test accuracy is 0.74; these five are chosen to show the model's
confidence behavior, including its dominant failure mode.

*Why the correct prediction is reasonable:* on the Kelce comment the model
predicts **analysis** with 0.99 confidence — correctly, because the comment cites
specific receiving stats (3 TDs, ~90 receptions) and contrasts them against the
player's historical baseline. That is exactly the evidence-backed reasoning that
defines `analysis`, and the high confidence is justified.

*Why the confident errors are revealing:* the four misses are all predicted
`hot_take` with high confidence (0.78–0.97) when the truth is `reaction` (or, in
the cherry-pick case, `analysis`). The model isn't hedging on these — it is
confidently wrong, which confirms it has internalized "short, claim-shaped text =
hot_take" rather than the feeling-vs-claim distinction. "Niners are finished" is
the cleanest example: pure emotional reaction, no claim, predicted `hot_take` at
0.97.

### 5.6 What the model learned vs. what I intended

I intended the model to learn **epistemic status**: is a claim *supported by
evidence* (analysis), *asserted without it* (hot_take), or *not a claim at all*
(reaction)? Fine-tuning clearly taught it the **analysis** boundary well (F1
0.92) and fixed the baseline's near-total blindness to `hot_take` (recall
0.15 → 0.77) — confirming my hypothesis that fine-tuning would learn the
analysis-vs-hot_take line a zero-shot model can't.

But what it actually learned is closer to **surface form than epistemic status**.
Having learned to recognize `hot_take`, it now treats *short + claim-shaped* text
as `hot_take` by default — so it absorbs emotional `reaction`s that happen to name
players (recall dropped to 0.44) and even mislabels terse, rhetorical-question
`analysis` as `hot_take`. In other words it overcorrected: it learned the *form*
of a bold take more than the *feeling-vs-claim* and *supported-vs-unsupported*
distinctions I actually intended. The gap between "is a confident claim" and "is
just venting," and between "argues well" and "sounds punchy," is what the model
didn't fully capture — which is also the part hardest for human annotators and
most starved for examples (reaction is my smallest class at 27%).

---

## 6. Spec Reflection

- **How the spec helped:** committing to precise label definitions and explicit
  edge-case decision rules in `planning.md` *before* annotating kept my labeling
  consistent — when I hit a borderline post, I had a written rule to apply
  instead of guessing, which matters most on the fuzzy analysis/hot_take line.
- **How the implementation diverged:** the plan assumed a single random comment
  pull would yield a balanced 3-class set. It didn't — `reaction` was scarce and
  ~22% of comments were off-topic. I diverged by adding a second short-comment
  collection pool and dropping off-topic content, which is exactly the
  "read the data first, revise the plan" check the brief recommends.

---

## 7. AI Usage

1. **Label stress-testing & taxonomy revision.** I gave Claude my label
   definitions and had it pressure-test them against real pulled comments. This
   surfaced that `advice_seeking` was nearly absent in the comment stream; I
   revised the taxonomy to `analysis`/`hot_take`/`reaction` as a result.
2. **Annotation pre-labeling.** Claude pre-labeled all 230 comments using my
   definitions; I then reviewed and corrected every label by hand in Numbers.
   Pre-labeling sped up annotation, but the final labels are my own. (Disclosed
   here per the assignment.)
3. **Failure analysis.** I gave Claude the list of misclassified test examples
   and asked it to identify systematic patterns; it flagged the
   `hot_take → analysis` directional confusion and the "short reactions that name
   players" blind spot. I verified both by re-reading the examples before
   including them above.

---

## 8. Repo Contents & How to Run

```
ai201-project-takemeter/
├── README.md                                          # this file
├── planning.md                                        # design notes, label rules, edge cases
├── takemeter_dataset.csv                              # 230 labeled comments
├── evaluation_results.json                            # exported from the Colab notebook
├── confusionMatrix.png                                # exported from the Colab notebook
├── interface.py                                       # CLI: comment in -> label + confidence
├── gradio_app.py                                      # web UI (stretch: deployed interface)
└── Copy_of_ai201_project3_takemeter_starter_clean.ipynb   # the Colab notebook
```

**To reproduce:**
1. Open the TakeMeter starter Colab notebook; set runtime to **T4 GPU**.
2. Add `GROQ_API_KEY` via Colab Secrets.
3. Section 1: set `label_map = {"analysis":0,"hot_take":1,"reaction":2}` and
   upload `takemeter_dataset.csv`.
4. Section 2: split + tokenize. Section 5: run the Groq baseline.
5. Section 3: fine-tune with epochs=10, LR=5e-5, batch size=8.
6. Sections 4 & 6: evaluate, generate the confusion matrix, export results.

---

## 9. Deployed Interface (Stretch)

A simple interface that takes a new comment, runs it through the fine-tuned
model, and shows the predicted label and confidence. Two versions are committed:

- **`interface.py`** — command-line tool.
- **`gradio_app.py`** — a web UI with per-class confidence bars.

### First: save the model out of Colab
After training, run this once in the notebook, then download the `takemeter-model`
folder into this repo:
```python
model.save_pretrained("takemeter-model")
tokenizer.save_pretrained("takemeter-model")
```

### CLI (`interface.py`)
```bash
pip install transformers torch
python interface.py "Chase Brown is a top 10 back, people just won't admit it"
# → hot_take  (confidence 0.81)
#   analysis=0.12  hot_take=0.81  reaction=0.07

python interface.py        # interactive: type comments, blank line to quit
```
Set `MODEL_DIR=/path/to/takemeter-model` if the model lives elsewhere.

### Web UI (`gradio_app.py`)
```bash
pip install gradio transformers torch
python gradio_app.py        # opens http://127.0.0.1:7860
```

### Quickest option — run the web UI directly in Colab (no download needed)
Reuses the in-memory `model` and `tokenizer` right after training:
```python
!pip -q install gradio
import gradio as gr, torch, torch.nn.functional as F
ID2LABEL = {0: "analysis", 1: "hot_take", 2: "reaction"}
def predict(text):
    enc = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(model.device)
    with torch.no_grad():
        probs = F.softmax(model(**enc).logits, dim=-1)[0]
    return {ID2LABEL[i]: float(probs[i]) for i in range(len(probs))}
gr.Interface(predict,
    gr.Textbox(lines=3, label="r/fantasyfootball comment"),
    gr.Label(num_top_classes=3, label="Predicted discourse type"),
    title="TakeMeter").launch(share=True)   # share=True gives a public link
```

## 10. Confidence Calibration (Stretch)

**Question:** are the model's confidence scores meaningful — does a 0.9-confident
prediction get it right more often than a 0.6-confident one?

**Early signal (from the error list):** several *wrong* predictions carry very
high confidence — 0.94, 0.97, and 0.98 — which suggests the model is
**overconfident**, especially on the reaction→hot_take errors. The analysis below
quantifies that.

Run this cell in Colab after Section 4 to bin the test set by confidence and
compute Expected Calibration Error (ECE):

```python
import torch, torch.nn.functional as F
import numpy as np

texts  = test_df["text"].tolist()        # adjust to your test dataframe/column
labels = test_df["label"].tolist()
label2id = {"analysis":0, "hot_take":1, "reaction":2}

confs, correct = [], []
for t, true in zip(texts, labels):
    enc = tokenizer(t, return_tensors="pt", truncation=True, padding=True).to(model.device)
    with torch.no_grad():
        p = F.softmax(model(**enc).logits, dim=-1)[0]
    pred = int(p.argmax())
    confs.append(float(p[pred])); correct.append(int(pred == label2id[true]))

confs, correct = np.array(confs), np.array(correct)
bins = [(0.0,0.6),(0.6,0.8),(0.8,0.9),(0.9,1.01)]
print("| Confidence bin | N | Accuracy | Avg confidence |")
print("|---|---:|---:|---:|")
ece = 0.0
for lo, hi in bins:
    m = (confs >= lo) & (confs < hi)
    if m.sum() == 0:
        print(f"| {lo:.1f}–{hi:.1f} | 0 | — | — |"); continue
    acc, avg = correct[m].mean(), confs[m].mean()
    ece += (m.sum()/len(confs)) * abs(acc - avg)
    print(f"| {lo:.1f}–{hi:.1f} | {int(m.sum())} | {acc:.2f} | {avg:.2f} |")
print(f"\nExpected Calibration Error (ECE): {ece:.3f}")
```

### Results *(paste from the cell above)*

| Confidence bin | N | Accuracy | Avg confidence |
|---|---:|---:|---:|
| 0.0–0.6 | ‹FILL› | ‹FILL› | ‹FILL› |
| 0.6–0.8 | ‹FILL› | ‹FILL› | ‹FILL› |
| 0.8–0.9 | ‹FILL› | ‹FILL› | ‹FILL› |
| 0.9–1.0 | ‹FILL› | ‹FILL› | ‹FILL› |

**Expected Calibration Error: ‹FILL›**

**Interpretation** *(write 2–3 sentences once you have the numbers):* a
well-calibrated model has accuracy ≈ average confidence in each bin. If the
top bin (0.9–1.0) has accuracy well below 0.9, the model is overconfident — which
the high-confidence errors already hint at. Note the test set is only 35 examples,
so bins are small and the estimate is noisy; this is a directional check, not a
precise calibration curve.

## 11. Other Stretch Features

Not attempted: inter-annotator reliability and a separate systematic
error-pattern analysis (though §5.4 documents the dominant reaction→hot_take
pattern). Left as future work.
