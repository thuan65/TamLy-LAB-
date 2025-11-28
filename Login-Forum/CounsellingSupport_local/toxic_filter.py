# toxic_filter.py

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# — Model tiếng Anh (optionnal) —
EN_MODEL = "unitary/toxic-bert"
en_tokenizer = AutoTokenizer.from_pretrained(EN_MODEL)
en_model = AutoModelForSequenceClassification.from_pretrained(EN_MODEL)
EN_THRESHOLD = 0.5

def is_toxic_en(text: str, threshold: float = EN_THRESHOLD) -> bool:
    inputs = en_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = en_model(**inputs)
    probs = torch.sigmoid(outputs.logits)[0].tolist()
    return any(p > threshold for p in probs)


# — Model tiếng Việt: PhoBERT‑HSD —
VI_MODEL = "visolex/phobert-hsd"
vi_tokenizer = AutoTokenizer.from_pretrained(VI_MODEL)
vi_model = AutoModelForSequenceClassification.from_pretrained(VI_MODEL)
VI_THRESHOLD = 0.5

def is_toxic_vi(text: str, threshold: float = VI_THRESHOLD) -> bool:
    inputs = vi_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = vi_model(**inputs)
    logits = outputs.logits  # giả sử có 3 lớp: CLEAN / OFFENSIVE / HATE :contentReference[oaicite:1]{index=1}  
    probs = torch.softmax(logits, dim=1)[0].tolist()
    # probs[1] = OFFENSIVE, probs[2] = HATE
    return probs[1] > threshold or probs[2] > threshold

# — Kết hợp —
def is_toxic(text: str, en_threshold: float = EN_THRESHOLD, vi_threshold: float = VI_THRESHOLD) -> bool:
    # Nếu là tiếng Việt hoặc mix: check với vi_model
    if is_toxic_vi(text, vi_threshold):
        return True
    # Nếu không, check với model Anh
    if is_toxic_en(text, en_threshold):
        return True
    return False
