import glob
import json
import os
import re
import sys

from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, "schema.json"), encoding="utf-8") as fh:
    SCHEMA = json.load(fh)

LABELS = SCHEMA["label_enums"]
TERM_V = Draft202012Validator(SCHEMA["term"])
SENT_V = Draft202012Validator(SCHEMA["sentence"])
ID_RE = re.compile(r"^HAT-\d{3}-S\d+$")

errors, warnings = [], []


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}/{k}", k, v
            yield from walk(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def check_labels(obj, where):
    for path, key, val in walk(obj):
        if key in LABELS and isinstance(val, str) and val not in LABELS[key]:
            errors.append(f"{where} {path}: '{val}' not in {LABELS[key]}")


def schema_errors(validator, rec, where):
    for e in validator.iter_errors(rec):
        loc = "/".join(str(p) for p in e.path) or "(root)"
        errors.append(f"{where} {loc}: {e.message}")


term_ids = set()
for f in sorted(glob.glob(os.path.join(ROOT, "entries", "*.json"))):
    name = os.path.basename(f)
    stem = name[:-5]
    if not ID_RE.match(stem):
        warnings.append(f"{name}: legacy/non-v1.1 filename, skipped")
        continue
    try:
        with open(f, encoding="utf-8") as fh:
            rec = json.load(fh)
    except Exception as ex:
        errors.append(f"{name}: invalid JSON ({ex})")
        continue
    if not isinstance(rec, dict):
        errors.append(f"{name}: must be a single JSON object")
        continue
    schema_errors(TERM_V, rec, name)
    check_labels(rec, name)
    sid = rec.get("sense_id")
    if sid != stem:
        errors.append(f"{name}: sense_id '{sid}' does not match filename")
    if stem in term_ids:
        errors.append(f"{name}: duplicate sense_id")
    term_ids.add(stem)

seen = set()
for f in sorted(glob.glob(os.path.join(ROOT, "sentences", "original", "*.jsonl"))):
    name = os.path.basename(f)
    stem = name[:-6]
    if not ID_RE.match(stem):
        warnings.append(f"{name}: non-v1.1 filename, skipped")
        continue
    if stem not in term_ids:
        errors.append(f"{name}: no matching term file in entries/")
    with open(f, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            where = f"{name}:{n}"
            try:
                rec = json.loads(line)
            except Exception as ex:
                errors.append(f"{where}: invalid JSON ({ex})")
                continue
            if not isinstance(rec, dict):
                errors.append(f"{where}: must be an object")
                continue
            schema_errors(SENT_V, rec, where)
            check_labels(rec, where)
            sid = rec.get("sentence_id")
            if sid in seen:
                errors.append(f"{where}: duplicate sentence_id {sid}")
            seen.add(sid)
            if isinstance(sid, str) and not sid.startswith(stem):
                warnings.append(f"{where}: sentence_id '{sid}' does not start with {stem}")
            if rec.get("correct") is True:
                tgt = rec.get("target_hi") or ""
                for w in rec.get("forbidden_hi") or []:
                    if w and w in tgt:
                        errors.append(f"{where}: forbidden_hi '{w}' appears in target_hi")

for w in warnings:
    print("WARN ", w)
for e in errors:
    print("ERROR", e)
print(f"\n{len(term_ids)} term files, {len(seen)} sentences, {len(errors)} errors, {len(warnings)} warnings")
sys.exit(1 if errors else 0)
