"""Vector index: Amazon S3 Vectors in AWS, a numpy file locally. Same interface; chosen by settings."""

import json
from pathlib import Path

from ka.config import settings


class S3VectorsIndex:
    """put/query on an S3 Vectors index. Metadata: doc, chunk, text (text is non-filterable)."""

    def __init__(self, bucket: str | None = None, index: str | None = None, session=None):
        import boto3

        self.bucket = bucket or settings.vector_bucket
        self.index = index or settings.vector_index
        sess = session or boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
        self.client = sess.client("s3vectors")

    def upsert(self, keys: list[str], vectors: list[list[float]], metadata: list[dict]) -> int:
        n = 0
        for i in range(0, len(keys), 100):
            batch = [
                {"key": k, "data": {"float32": [float(x) for x in v]}, "metadata": m}
                for k, v, m in zip(
                    keys[i : i + 100], vectors[i : i + 100], metadata[i : i + 100], strict=True
                )
            ]
            self.client.put_vectors(vectorBucketName=self.bucket, indexName=self.index, vectors=batch)
            n += len(batch)
        return n

    def query(self, vector: list[float], k: int = 4) -> list[dict]:
        r = self.client.query_vectors(
            vectorBucketName=self.bucket,
            indexName=self.index,
            queryVector={"float32": [float(x) for x in vector]},
            topK=k,
            returnMetadata=True,
            returnDistance=True,
        )
        return [
            {
                "key": v["key"],
                "doc": v["metadata"].get("doc"),
                "text": v["metadata"].get("text", ""),
                "score": round(1 - v.get("distance", 0), 4),
            }
            for v in r.get("vectors", [])
        ]

    def count(self) -> int | None:
        try:
            r = self.client.list_vectors(vectorBucketName=self.bucket, indexName=self.index, maxResults=500)
            return len(r.get("vectors", []))
        except Exception:  # noqa: BLE001
            return None


class LocalIndex:
    """numpy cosine index persisted to .ka/index.npz + .json. For local runs and tests; never on AWS."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or settings.local_index_path)
        self.keys: list[str] = []
        self.meta: list[dict] = []
        self.vectors = None
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        import numpy as np

        self.vectors = np.load(self.path)["v"]
        d = json.loads(self.path.with_suffix(".json").read_text())
        self.keys, self.meta = d["keys"], d["meta"]

    def _save(self) -> None:
        import numpy as np

        self.path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(self.path, v=self.vectors)
        self.path.with_suffix(".json").write_text(json.dumps({"keys": self.keys, "meta": self.meta}))

    def upsert(self, keys: list[str], vectors: list[list[float]], metadata: list[dict]) -> int:
        import numpy as np

        new = np.asarray(vectors, dtype="float32")
        new /= np.linalg.norm(new, axis=1, keepdims=True) + 1e-9
        keep = [i for i, k in enumerate(self.keys) if k not in set(keys)]
        if self.vectors is not None and keep:
            self.vectors = np.vstack([self.vectors[keep], new])
            self.keys = [self.keys[i] for i in keep] + list(keys)
            self.meta = [self.meta[i] for i in keep] + list(metadata)
        else:
            self.vectors, self.keys, self.meta = new, list(keys), list(metadata)
        self._save()
        return len(keys)

    def query(self, vector: list[float], k: int = 4) -> list[dict]:
        import numpy as np

        if self.vectors is None:
            return []
        q = np.asarray(vector, dtype="float32")
        q /= np.linalg.norm(q) + 1e-9
        sims = self.vectors @ q
        top = np.argsort(-sims)[:k]
        return [
            {
                "key": self.keys[i],
                "doc": self.meta[i].get("doc"),
                "text": self.meta[i].get("text", ""),
                "score": round(float(sims[i]), 4),
            }
            for i in top
        ]

    def count(self) -> int:
        return len(self.keys)


def make_index():
    return S3VectorsIndex() if settings.vector_bucket else LocalIndex()
