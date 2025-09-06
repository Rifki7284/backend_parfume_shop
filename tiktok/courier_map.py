# tiktok/courier_map.py
import re

NORMALIZE = {
    "jnt": {"jnt", "j&t", "j&t express", "jet", "j n t"},
    "jne": {"jne", "j n e"},
    "sicepat": {"sicepat", "si cepat"},
    "anteraja": {"anteraja", "anter aja"},
    "ninja": {"ninja", "ninja xpress", "ninjaxpress"},
    "tiki": {"tiki"},
    "pos": {"pos", "pos indonesia"},
    "idexpress": {"idexpress", "id express", "ide"},
}

def to_binderbyte_code(name: str) -> str:
    key = re.sub(r"\s+", " ", name.strip().lower())
    for code, aliases in NORMALIZE.items():
        if key in aliases:
            return code
    return name.lower()
