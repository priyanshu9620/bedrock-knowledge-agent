"""Corpus → chunks → Gemini embeddings → vector index. Source: local corpus/ or the S3 docs bucket."""

import hashlib
import re
from pathlib import Path

from ka.config import settings

CORPUS = Path(__file__).resolve().parents[2] / "corpus"  # local only; the Lambda reads S3


def load_docs(source: str = "local") -> dict[str, str]:
    """{doc name: markdown text}."""
    if source == "s3":
        import boto3

        s3 = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region).client("s3")
        out = {}
        for o in s3.list_objects_v2(Bucket=settings.docs_bucket, Prefix="handbook/").get("Contents", []):
            name = o["Key"].rsplit("/", 1)[-1]
            if name.endswith(".md"):
                out[name] = s3.get_object(Bucket=settings.docs_bucket, Key=o["Key"])["Body"].read().decode()
        return out
    return {p.name: p.read_text() for p in sorted(CORPUS.glob("*.md"))}


def chunk(text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
    """Paragraph-aware fixed-size chunks with overlap; the doc title (first heading) is prefixed to every chunk."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    title = paras[0] if paras and paras[0].startswith("#") else ""
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 > max_chars and cur:
            chunks.append(cur.strip())
            cur = cur[-overlap:] + "\n\n" + p if overlap else p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur.strip():
        chunks.append(cur.strip())
    return [c if c.startswith(title) or not title else f"{title}\n\n{c}" for c in chunks]


def ingest(index, gemini, docs: dict[str, str]) -> dict:
    keys, texts, meta = [], [], []
    for doc, text in docs.items():
        for i, c in enumerate(chunk(text)):
            keys.append(hashlib.sha1(f"{doc}#{i}".encode()).hexdigest()[:16])
            texts.append(c)
            meta.append({"doc": doc, "chunk": i, "text": c})
    vectors = gemini.embed(texts, task="RETRIEVAL_DOCUMENT")
    n = index.upsert(keys, vectors, meta)
    return {"docs": len(docs), "chunks": n, "dimension": len(vectors[0]) if vectors else 0}
