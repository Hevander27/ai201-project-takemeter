#!/usr/bin/env python3
"""TakeMeter — deployed web interface (Gradio).

A simple web UI: paste an r/fantasyfootball comment, get the predicted discourse
label (analysis / hot_take / reaction) with per-class confidence bars.

Run locally (after downloading the model folder into this repo):
    pip install gradio transformers torch
    python gradio_app.py
    # opens http://127.0.0.1:7860

Run in Colab (model already in memory after training): see the README
"Deployed Interface" section for the 8-line in-notebook version that reuses the
existing `model` and `tokenizer` and gives a public share link.
"""
import os

import gradio as gr
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_DIR = os.environ.get("MODEL_DIR", "./takemeter-model")
ID2LABEL = {0: "analysis", 1: "hot_take", 2: "reaction"}

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()


def predict(text):
    if not text or not text.strip():
        return {}
    enc = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        probs = F.softmax(model(**enc).logits, dim=-1)[0]
    return {ID2LABEL[i]: float(probs[i]) for i in range(len(probs))}


demo = gr.Interface(
    fn=predict,
    inputs=gr.Textbox(lines=3, label="r/fantasyfootball comment", placeholder="Paste a comment…"),
    outputs=gr.Label(num_top_classes=3, label="Predicted discourse type"),
    title="TakeMeter",
    description="Classifies a fantasy-football comment as analysis, hot_take, or reaction.",
    examples=[
        ["Kelce had 3 TDs and ~90 receptions — the TD count is incredibly low vs his history, he's declining but still useful."],
        ["Chase Brown is a top 10 back, people just don't wanna have that convo yet."],
        ["Niners are finished lol"],
    ],
)

if __name__ == "__main__":
    demo.launch()
