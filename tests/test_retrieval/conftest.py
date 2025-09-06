import sys
import types

stub = types.ModuleType("sentence_transformers")


class SentenceTransformer:  # pragma: no cover - minimal stub
    def __init__(self, *args, **kwargs):
        pass


def encode(self, *args, **kwargs):  # pragma: no cover
    return []


SentenceTransformer.encode = encode
stub.SentenceTransformer = SentenceTransformer
sys.modules.setdefault("sentence_transformers", stub)
