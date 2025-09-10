# Interface Specifications for Personal RAG Copilot

**Version:** 1.0
**Date:** September 9, 2025
**Status:** Draft

---

## 1. Overview

This document defines the interface contracts between system components for the Personal RAG Copilot audit fixes implementation.

---

## 2. Core Data Interfaces

### 2.1 Document Interface

```python
@dataclass
class Document:
    """Represents a retrieved document chunk with metadata."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0
    source: str = ""  # 'dense', 'lexical', 'fused'
    rank: int = 0

    def __post_init__(self):
        if self.source not in ['dense', 'lexical', 'fused', '']:
            raise ValueError(f"Invalid source: {self.source}")
```

**Contract:**
- `id`: Unique identifier for the document chunk
- `content`: Text content of the chunk
- `metadata`: Additional information (filename, page, etc.)
- `score`: Relevance score (0.0 to 1.0)
- `source`: Retrieval method that found this document
- `rank`: Position in the result list

### 2.2 RetrievalResult Interface

```python
@dataclass
class RetrievalResult:
    """Container for retrieval operation results."""
    documents: List[Document]
    query: str
    retrieval_mode: str  # 'dense', 'lexical', 'hybrid'
    rrf_k: int = 60
    weights: Dict[str, float] = field(default_factory=dict)
    timing: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.retrieval_mode not in ['dense', 'lexical', 'hybrid']:
            raise ValueError(f"Invalid retrieval mode: {self.retrieval_mode}")
```

**Contract:**
- `documents`: Ordered list of retrieved documents
- `query`: Original search query
- `retrieval_mode`: Type of retrieval performed
- `rrf_k`: RRF parameter value used
- `weights`: Per-retriever weights applied
- `timing`: Performance timing data

### 2.3 EvaluationMetrics Interface

```python
@dataclass
class EvaluationMetrics:
    """Container for quality evaluation results."""
    faithfulness: float
    relevancy: float
    context_precision: float
    rationale: str
    timestamp: datetime

    def __post_init__(self):
        for metric in [self.faithfulness, self.relevancy, self.context_precision]:
            if not (0.0 <= metric <= 1.0):
                raise ValueError(f"Metric out of range: {metric}")
```

**Contract:**
- `faithfulness`: Answer claims supported by context (0.0-1.0)
- `relevancy`: Answer relevance to question (0.0-1.0)
- `context_precision`: Quality of retrieved context (0.0-1.0)
- `rationale`: Explanation of the evaluation
- `timestamp`: When evaluation was performed

---

## 3. Service Interfaces

### 3.1 IRetriever Interface

```python
from abc import ABC, abstractmethod
from typing import List

class IRetriever(ABC):
    """Abstract interface for retrieval components."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
        """
        Retrieve top-k relevant documents for the query.

        Args:
            query: Search query string
            top_k: Number of documents to retrieve

        Returns:
            List of relevant documents, ordered by relevance

        Raises:
            RetrievalError: If retrieval fails
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """
        Get the type of retrieval method.

        Returns:
            'dense', 'lexical', or 'hybrid'
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the retriever is ready for use.

        Returns:
            True if retriever is operational
        """
        pass
```

**Contract:**
- Implementations must handle errors gracefully
- Results must be sorted by relevance score
- Source type must match actual implementation

### 3.2 IEvaluator Interface

```python
from abc import ABC, abstractmethod

class IEvaluator(ABC):
    """Abstract interface for evaluation components."""

    @abstractmethod
    def evaluate(self, question: str, answer: str, contexts: List[str]) -> EvaluationMetrics:
        """
        Evaluate the quality of an answer given question and contexts.

        Args:
            question: Original question
            answer: Generated answer
            contexts: Retrieved context documents

        Returns:
            Evaluation metrics

        Raises:
            EvaluationError: If evaluation fails
        """
        pass

    @abstractmethod
    def get_supported_metrics(self) -> List[str]:
        """
        Get list of supported evaluation metrics.

        Returns:
            List of metric names
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if evaluator is ready for use.

        Returns:
            True if evaluator is operational
        """
        pass
```

**Contract:**
- All metrics must be in 0.0-1.0 range
- Must provide rationale for scores
- Must handle missing dependencies gracefully

### 3.3 IResponseGenerator Interface

```python
from abc import ABC, abstractmethod

class IResponseGenerator(ABC):
    """Abstract interface for response generation components."""

    @abstractmethod
    def generate_response(self, query: str, contexts: List[Document]) -> str:
        """
        Generate a response using query and retrieved contexts.

        Args:
            query: User question
            contexts: Retrieved relevant documents

        Returns:
            Generated response string

        Raises:
            GenerationError: If response generation fails
        """
        pass

    @abstractmethod
    def estimate_cost(self, query: str, contexts: List[Document]) -> float:
        """
        Estimate computational cost of generation.

        Args:
            query: User question
            contexts: Retrieved documents

        Returns:
            Estimated cost in arbitrary units
        """
        pass
```

**Contract:**
- Must utilize provided contexts in response
- Must handle empty contexts gracefully
- Cost estimation for performance planning

---

## 4. UI Component Interfaces

### 4.1 IChatInterface

```python
from abc import ABC, abstractmethod

class IChatInterface(ABC):
    """Interface for chat UI components."""

    @abstractmethod
    def display_message(self, message: str, sender: str) -> None:
        """
        Display a message in the chat interface.

        Args:
            message: Message content
            sender: 'user' or 'assistant'
        """
        pass

    @abstractmethod
    def show_typing_indicator(self) -> None:
        """Show typing indicator during response generation."""
        pass

    @abstractmethod
    def hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        pass

    @abstractmethod
    def update_citations(self, documents: List[Document]) -> None:
        """
        Update citation display with retrieval results.

        Args:
            documents: Retrieved documents with metadata
        """
        pass
```

**Contract:**
- Must support streaming responses
- Must display source badges correctly
- Must handle citation transparency

---

## 5. Configuration Interfaces

### 5.1 RetrievalConfig Interface

```python
@dataclass
class RetrievalConfig:
    """Configuration for retrieval components."""
    mode: str = 'hybrid'  # 'dense', 'lexical', 'hybrid'
    top_k: int = 10
    rrf_k: int = 60
    enable_reranking: bool = False
    rerank_top_k: int = 20
    lexical_weight: float = 1.0
    dense_weight: float = 1.0

    def __post_init__(self):
        if self.mode not in ['dense', 'lexical', 'hybrid']:
            raise ValueError(f"Invalid mode: {self.mode}")
        if not (1 <= self.rrf_k <= 100):
            raise ValueError(f"RRF k out of range: {self.rrf_k}")
```

**Contract:**
- All parameters must have valid ranges
- Mode must be supported by system
- Weights must be positive

### 5.2 EvaluationConfig Interface

```python
@dataclass
class EvaluationConfig:
    """Configuration for evaluation components."""
    enable_evaluation: bool = True
    faithfulness_threshold: float = 0.7
    enable_fallback_metrics: bool = True
    store_historical_data: bool = True
    evaluation_timeout: int = 30  # seconds

    def __post_init__(self):
        if not (0.0 <= self.faithfulness_threshold <= 1.0):
            raise ValueError(f"Invalid threshold: {self.faithfulness_threshold}")
```

**Contract:**
- Thresholds must be in valid ranges
- Timeout must be reasonable
- Fallback must be available

---

## 6. Error Interfaces

### 6.1 Base Exceptions

```python
class RagCopilotError(Exception):
    """Base exception for RAG Copilot errors."""
    pass

class RetrievalError(RagCopilotError):
    """Raised when retrieval operations fail."""
    pass

class EvaluationError(RagCopilotError):
    """Raised when evaluation operations fail."""
    pass

class GenerationError(RagCopilotError):
    """Raised when response generation fails."""
    pass

class ConfigurationError(RagCopilotError):
    """Raised when configuration is invalid."""
    pass
```

**Contract:**
- All exceptions inherit from RagCopilotError
- Include context about what failed
- Provide actionable error messages

---

## 7. Event Interfaces

### 7.1 System Events

```python
@dataclass
class QueryEvent:
    """Event fired when a query is processed."""
    query_id: str
    query: str
    timestamp: datetime
    retrieval_mode: str
    document_count: int
    processing_time: float

@dataclass
class EvaluationEvent:
    """Event fired when evaluation is performed."""
    query_id: str
    faithfulness: float
    relevancy: float
    timestamp: datetime

@dataclass
class ErrorEvent:
    """Event fired when errors occur."""
    error_type: str
    message: str
    timestamp: datetime
    context: Dict[str, Any]
```

**Contract:**
- Events must include timestamps
- Must provide sufficient context
- Must be serializable for logging

---

## 8. Implementation Notes

### 8.1 Interface Compliance

All implementations must:
- Validate input parameters
- Handle exceptions appropriately
- Provide meaningful error messages
- Include comprehensive docstrings
- Support the specified return types

### 8.2 Testing Requirements

Interface implementations must include:
- Unit tests for all methods
- Integration tests with mock dependencies
- Error handling tests
- Performance benchmarks

### 8.3 Versioning

Interface versions follow semantic versioning:
- Major: Breaking changes
- Minor: New optional methods
- Patch: Bug fixes and documentation

---

*This document defines the contracts that ensure system components can interact reliably and maintainably.*