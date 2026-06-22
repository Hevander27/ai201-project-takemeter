#!/usr/bin/env python3
"""TakeMeter — command-line interface for the fine-tuned classifier.

Classifies an r/fantasyfootball comment as analysis / hot_take / reaction and
prints the predicted label with its confidence (plus the full distribution).

Usage:
    python interface.py "Chase Brown is a top 10 back, people just won't admit it"
    python interface.py            # interactive mode (type comments, blank line quits)

The model is loaded from MODEL_DIR (a folder with config.json, model.safetensors,
and the tokenizer files). Save it from the Colab notebook after training with:
    model.save_pretrained("takemeter-model")
    tokenizer.save_pretrained("takemeter-model")
then download that folder into this repo (or set MODEL_DIR to its path).
"""
import os
import sys

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_DIR = os.environ.get("MODEL_DIR", "./takemeter-model")
ID2LABEL = {0: "analysis", 1: "hot_take", 2: "reaction"}


def load_model(model_dir=MODEL_DIR):
    if not os.path.isdir(model_dir):
        sys.exit(
            f"Model folder not found: {model_dir}\n"
            "Save it from Colab (model.save_pretrained('takemeter-model') + "
            "tokenizer.save_pretrained('takemeter-model')), download it here, "
            "or set MODEL_DIR to its path."
        )
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()
    return tokenizer, model


def classify(text, tokenizer, model):
    enc = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        probs = F.softmax(model(**enc).logits, dim=-1)[0]
    top = int(probs.argmax())
    dist = {ID2LABEL[i]: float(probs[i]) for i in range(len(probs))}
    return ID2LABEL[top], float(probs[top]), dist


def show(text, tokenizer, model):
    label, conf, dist = classify(text, tokenizer, model)
    bars = "  ".join(f"{k}={v:.2f}" for k, v in dist.items())
    print(f"  → {label}  (confidence {conf:.2f})")
    print(f"    {bars}")


def main():
    tokenizer, model = load_model()
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]), tokenizer, model)
        return
    print("TakeMeter — type an r/fantasyfootball comment (blank line to quit)")
    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            break
        show(text, tokenizer, model)


if __name__ == "__main__":
    main()
