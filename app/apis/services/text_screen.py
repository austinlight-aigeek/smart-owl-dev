import re

import spacy
from fastapi import HTTPException


def clean_prompt(prompt: str, http_err: HTTPException) -> str:
    if pii_recognize(prompt):
        raise http_err
    else:
        return ner_mask(prompt)


def pii_recognize(prompt: str) -> bool:
    # TODO: Add more patterns as required
    patterns = [
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}",  # Email
        r"\d{3}[-.\s]?\d{2}[-.\s]?\d{4}",  # SSN
        r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",  # Phone number
    ]
    for pattern in patterns:
        if re.search(pattern, prompt):
            return True
    return False


def ner_mask(prompt: str) -> bool:
    """
    Use Named Entity Recognition to screen prompt
    """
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(prompt)
    masked_text = list(prompt)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG"]:
            start, end = ent.start_char, ent.end_char
            masked_text[start:end] = "MASKED"

    return "".join(masked_text)
