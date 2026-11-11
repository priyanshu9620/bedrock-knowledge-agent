"""Every fact in corpus/facts.yml must appear verbatim in its doc, and every question's cite doc must exist."""

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    facts = yaml.safe_load((ROOT / "corpus" / "facts.yml").read_text())
    bad = 0
    for f in facts:
        doc = (ROOT / "corpus" / f["doc"]).read_text()
        if f["text"] not in doc:
            print(f"FACT MISSING: {f['id']} → '{f['text']}' not in {f['doc']}")
            bad += 1
    qs = yaml.safe_load((ROOT / "eval" / "questions.yml").read_text())
    docs = {p.name for p in (ROOT / "corpus").glob("*.md")}
    for q in qs:
        c = q["expect"].get("cite")
        if c and c not in docs:
            print(f"QUESTION {q['id']}: cite doc {c} does not exist")
            bad += 1
    print(
        f"{len(facts)} facts in {len(docs)} docs, {len(qs)} questions ({sum(1 for q in qs for _ in [0] if q['class'] == 'kb')} kb / {sum(1 for q in qs if q['class'] == 'tool')} tool / {sum(1 for q in qs if q['class'] == 'both')} both / {sum(1 for q in qs if q['class'] == 'oos')} oos) — {'OK' if not bad else f'{bad} problems'}"
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
