from typing import Any

class AutoModelForSequenceClassification:
    @classmethod
    def from_pretrained(cls, *args: Any, **kwargs: Any) -> Any: ...

class AutoTokenizer:
    @classmethod
    def from_pretrained(cls, *args: Any, **kwargs: Any) -> Any: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
