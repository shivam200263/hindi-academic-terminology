import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build")
ID_RE = re.compile(r"^HAT-\d{3}-S\d+$")

TERM_COLS = [
    "sense_id", "entry_id", "english_term", "discipline", "subdiscipline",
    "definition_english", "definition_hindi", "preferred_hindi_equivalent",
    "alternative_hindi_equivalents",
]
SENT_COLS = [
    "sentence_id", "source_type", "source_tier", "source_ref", "source_url",
    "hindi_source", "verbatim_verified", "licence", "source_en", "target_hi",
    "target_hi_refined", "refinement_note", "term_en", "term_hi_used",
    "acceptable_alternatives", "forbidden_hi", "confusable_terms",
    "context_note", "domain", "level", "grammar_tags", "task_types",
    "correct", "verification_status", "notes",
]
LIST_COLS = {
    "discipline", "subdiscipline", "alternative_hindi_equivalents",
    "acceptable_alternatives", "forbidden_hi", "confusable_terms",
    "grammar_tags", "task_types",
}

os.makedirs(OUT, exist_ok=True)


def pick(rec, cols):
    row = {}
    for c in cols:
        v = rec.get(c)
        if v is None and c in LIST_COLS:
            v = []
        row[c] = v
    return row


terms = []
for f in sorted(glob.glob(os.path.join(ROOT, "entries", "*.json"))):
    stem = os.path.basename(f)[:-5]
    if not ID_RE.match(stem):
        continue
    with open(f, encoding="utf-8") as fh:
        rec = json.load(fh)
    row = pick(rec, TERM_COLS)
    row["full_record"] = json.dumps(rec, ensure_ascii=False)
    terms.append(row)

sents = []
for f in sorted(glob.glob(os.path.join(ROOT, "sentences", "original", "*.jsonl"))):
    stem = os.path.basename(f)[:-6]
    if not ID_RE.match(stem):
        continue
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = {"sense_id": stem}
            row.update(pick(json.loads(line), SENT_COLS))
            sents.append(row)


def dump(name, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


dump("terms.jsonl", terms)
dump("sentences.jsonl", sents)
print(f"built {len(terms)} terms, {len(sents)} sentences")
