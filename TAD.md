# Personal RAG Copilot — Technical Architecture Document v1.1

**Document Control**
- **Version:** 1.1
- **Date:** September 9, 2025
- **Source:** Audit Findings Resolution
- **Status:** Architectural Design Complete

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

The system follows a layered architecture with clear separation of concerns:

- **Presentation Layer**: Gradio multipage UI
- **Application Layer**: Query processing, response generation
- **Domain Layer**: Retrieval, ranking, evaluation logic
- **Infrastructure Layer**: Storage, external services, dependencies

### 1.2 Component Diagram

```
[UI Layer]
  Chat | Ingest | Evaluate | Settings

[Application Layer]
  Query Service | Response Generator | Evaluation Service

[Domain Layer]
  Retrieval Engine (Dense/Lexical/Hybrid) | Ranking System | Evaluation Framework

[Infrastructure Layer]
  Pinecone Client | BM25 Index | LLM Service | Configuration
```

### 1.3 Data Flow Architecture

User Query → UI → Query Service → Retrieval Engine → RRF Fusion → [Optional Reranking] → Response Generator → LLM → Response + Evaluation

---

## 2. System Decomposition

### 2.1 Retrieval Engine

**Components:**
- DenseRetriever: Handles vector search via Pinecone
- LexicalRetriever: Manages BM25 indexing and search
- HybridRetriever: Orchestrates parallel retrieval and RRF fusion

**Interfaces:**
- IRetriever interface with retrieve(query) -> List[Document]

### 2.2 Ranking System

**Components:**
- RRFFusion: Implements reciprocal rank fusion
- Reranker: Optional cross-encoder reranking

**Interfaces:**
- IRanker interface with rank(documents, query) -> List[Document]

### 2.3 Evaluation Framework

**Components:**
- RagasEvaluator: Faithfulness and quality metrics
- MetricAggregator: Historical tracking

**Interfaces:**
- IEvaluator interface with evaluate(question, answer, contexts) -> Metrics

### 2.4 UI Components

**Components:**
- ChatInterface: Streaming chat with transparency
- IngestInterface: Document upload and processing
- EvaluateInterface: Quality metrics dashboard
- SettingsInterface: Configuration management

---

## 3. Interface Specifications

### 3.1 Core Interfaces

#### Document Interface

```python
@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0
    source: str = ""  # 'dense', 'lexical', 'fused'
    rank: int = 0
```

#### RetrievalResult Interface

```python
@dataclass
class RetrievalResult:
    documents: List[Document]
    query: str
    retrieval_mode: str
    rrf_k: int
    weights: Dict[str, float]
    timing: Dict[str, float]
```

#### EvaluationMetrics Interface

```python
@dataclass
class EvaluationMetrics:
    faithfulness: float
    relevancy: float
    context_precision: float
    rationale: str
    timestamp: datetime
```

### 3.2 Service Interfaces

#### IRetriever

```python
class IRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 10) -> List[Document]:
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        pass
```

#### IEvaluator

```python
class IEvaluator(ABC):
    @abstractmethod
    def evaluate(self, question: str, answer: str, contexts: List[str]) -> EvaluationMetrics:
        pass
```

---

## 4. Architecture Decision Records (ADRs)

### ADR-001: Hybrid Retrieval with RRF

**Context:** Need to combine dense and lexical search for optimal results

**Decision:** Implement RRF fusion with k=60 default, user-configurable

**Rationale:** RRF provides robust combination without requiring score normalization

**Consequences:** Added complexity but improved retrieval quality

### ADR-002: Optional Reranking

**Context:** Trade-off between accuracy and performance

**Decision:** Make reranking optional with user toggle

**Rationale:** Allows users to choose based on their needs

**Consequences:** Variable performance, requires caching

### ADR-003: Ragas for Evaluation

**Context:** Need standardized evaluation metrics

**Decision:** Integrate Ragas framework

**Rationale:** Industry standard for RAG evaluation

**Consequences:** Dependency on external library, potential import issues

### ADR-004: Gradio Multipage

**Context:** Need organized UI structure

**Decision:** Use Gradio 5 multipage with routing

**Rationale:** Clean URLs, better navigation

**Consequences:** Requires Gradio 5, potential migration effort

---

## 5. Sequence Diagrams

### 5.1 Query Processing Flow

```
User -> UI: Submit query
UI -> QueryService: process_query(query)
QueryService -> RetrievalEngine: retrieve(query)
RetrievalEngine -> DenseRetriever: retrieve_parallel
RetrievalEngine -> LexicalRetriever: retrieve_parallel
RetrievalEngine -> RRFFusion: fuse_results
QueryService -> Reranker: rerank (optional)
QueryService -> ResponseGenerator: generate_response
ResponseGenerator -> LLM: generate
ResponseGenerator -> Evaluator: evaluate
UI <- QueryService: return response + metrics
```

### 5.2 Document Ingestion Flow

```
User -> UI: Upload documents
UI -> IngestService: process_documents
IngestService -> DocumentProcessor: extract_text
IngestService -> DenseRetriever: create_embeddings
IngestService -> LexicalRetriever: build_index
IngestService -> Pinecone: upsert_vectors
UI <- IngestService: ingestion_complete
```

---

## 6. Tradeoff Analysis

### 6.1 Performance vs Accuracy

**Reranking:** Improves accuracy by 15-20% but adds 2-5s latency

**Hybrid Retrieval:** Better coverage than single mode but requires parallel processing

**Recommendation:** Make reranking optional, optimize hybrid with caching

### 6.2 Complexity vs Maintainability

**Microservices:** Better separation but increases deployment complexity

**Monolithic:** Simpler but harder to maintain

**Recommendation:** Keep monolithic for now, modularize internally

### 6.3 Cost vs Quality

**Large Models:** Better quality but higher inference costs

**Small Models:** Lower cost but reduced accuracy

**Recommendation:** Use efficient models with optional upgrades

---

## 7. Risk Assessment and Mitigation

### 7.1 Technical Risks

**Dependency Failures:**
- Risk: Missing ragas/rank-bm25 causes import errors
- Mitigation: Dependency verification on startup, fallback metrics
- Impact: High
- Probability: Medium

**Performance Degradation:**
- Risk: Reranking slows down responses
- Mitigation: Caching, timeout handling, user controls
- Impact: Medium
- Probability: Low

**Type Errors:**
- Risk: Runtime type issues
- Mitigation: Pyright integration, type hints
- Impact: Medium
- Probability: Low

### 7.2 Operational Risks

**Configuration Errors:**
- Risk: Wrong Pinecone dimensions
- Mitigation: Validation checks, clear error messages
- Impact: High
- Probability: Low

**Data Loss:**
- Risk: Index corruption
- Mitigation: Backup strategies, validation
- Impact: High
- Probability: Low

---

## 8. Implementation Roadmap

### Phase 1: Infrastructure (Week 1)
1. Install dependencies (ragas, rank-bm25, pyright)
2. Configure pyright for type checking
3. Update requirements files
4. CI/CD integration

### Phase 2: Core Fixes (Week 2)
1. Fix response generation logic
2. Correct UI badge labels
3. Implement dependency verification
4. Add error handling

### Phase 3: Advanced Features (Week 3)
1. Complete Ragas integration
2. Implement reranking
3. Add evaluation dashboard
4. Performance optimization

### Phase 4: Testing & Validation (Week 4)
1. Comprehensive testing
2. Performance benchmarking
3. User acceptance testing
4. Documentation updates

---

## 9. Feature Flags and Rollback Strategy

### 9.1 Feature Flags

```python
FEATURE_FLAGS = {
    'enable_reranking': False,
    'enable_evaluation': True,
    'enable_streaming': True,
    'enable_transparency': True
}
```

### 9.2 Rollback Strategy

**Code Rollback:**
- Git tags for each phase
- Automated rollback scripts
- Configuration backup/restore

**Feature Rollback:**
- Feature flags for gradual rollout
- A/B testing capabilities
- User preference persistence

**Data Rollback:**
- Index snapshots
- Document versioning
- Audit trails for changes

---

## 10. Success Metrics and Validation

### 10.1 Technical Metrics
- Type checking errors: 0
- Test failure count: 0
- Response latency: <2s (without reranking)
- Retrieval accuracy: >85%

### 10.2 Quality Metrics
- Faithfulness score: >0.8 average
- User satisfaction: >4/5
- Badge accuracy: 100%
- Import success rate: 100%

### 10.3 Business Metrics
- Query success rate: >95%
- System uptime: >99%
- Feature adoption: >80%

---

## Original TAD Content (Archived)

### 2.1 Dependency Management Architecture

#### Current State
- Missing critical dependencies: `ragas`, `rank-bm25`, `pyright`
- Import errors causing 21 test failures
- Incomplete evaluation framework

#### Proposed Changes
- **Dependency Resolution Layer**: Implement automated dependency verification during application startup
- **Requirements Management**: Update `requirements.txt` and `pyproject.toml` with all required packages
- **Installation Pipeline**: Integrate dependency installation into CI/CD and local setup scripts

#### Implementation Details
```python
# src/config/dependency_check.py
def verify_dependencies():
    required_packages = ['ragas', 'rank_bm25', 'pyright']
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        raise RuntimeError(f"Missing dependencies: {missing}")
```

#### Impact Assessment
- **Risk**: Minimal - standard dependency management
- **Complexity**: Low - pip install commands
- **Testing**: Unit tests for dependency verification

---

### 2.2 Type-Checking Integration

#### Current State
- No static type checking
- Potential runtime type errors
- Development environment lacks type diagnostics

#### Proposed Changes
- **Type Checking Layer**: Integrate pyright as development and CI tool
- **Configuration Management**: Create `pyrightconfig.json` with project-specific settings
- **IDE Integration**: Enable real-time type checking in development environments

#### Implementation Details
```json
// pyrightconfig.json
{
  "include": ["src"],
  "exclude": ["tests"],
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "pythonVersion": "3.9",
  "typeCheckingMode": "basic"
}
```

#### Impact Assessment
- **Risk**: Low - non-invasive addition
- **Complexity**: Low - configuration file
- **Testing**: Type checking validation in CI

---

### 2.3 Response Generation Architecture

#### Current State
- Chat UI wired to stub retriever
- Responses echo user input
- No utilization of retrieved contexts

#### Proposed Changes
- **Response Synthesis Layer**: Implement context-aware response generation
- **LLM Integration**: Connect retrieval results to language model
- **Fallback Mechanisms**: Handle retrieval failures gracefully

#### Implementation Details
```python
# src/ui/chat.py - Updated _generate_response
def _generate_response(self, query: str, contexts: List[Document]) -> str:
    if not contexts:
        return "I apologize, but I couldn't find relevant information to answer your question."

    # Synthesize response from contexts
    prompt = f"Based on the following information, answer the question: {query}\n\n"
    for i, ctx in enumerate(contexts[:3]):  # Use top 3 contexts
        prompt += f"Context {i+1}: {ctx.content}\n\n"

    response = self.llm.generate(prompt)
    return response
```

#### Impact Assessment
- **Risk**: Medium - changes core functionality
- **Complexity**: Medium - LLM integration required
- **Testing**: Response quality validation tests

---

### 2.4 UI Component Architecture

#### Current State
- Incorrect badge labels ("SPARSE" instead of "LEXICAL")
- Inconsistent source identification
- User confusion about retrieval methods

#### Proposed Changes
- **Badge Management Layer**: Centralized badge label management
- **UI Consistency Framework**: Standardized source identification
- **Visual Design System**: Consistent badge styling and placement

#### Implementation Details
```python
# src/ui/components/badges.py
BADGE_LABELS = {
    'dense': 'DENSE',
    'lexical': 'LEXICAL',
    'hybrid': 'FUSED'
}

def get_source_badge(source_type: str) -> str:
    return BADGE_LABELS.get(source_type.lower(), 'UNKNOWN')
```

#### Impact Assessment
- **Risk**: Low - UI-only changes
- **Complexity**: Low - string replacements
- **Testing**: UI component tests

---

### 2.5 Evaluation Framework Architecture

#### Current State
- Ragas evaluation fails due to missing dependencies
- Import errors prevent evaluation functionality
- Incomplete quality assessment pipeline

#### Proposed Changes
- **Evaluation Service Layer**: Robust Ragas integration with error handling
- **Dependency Validation**: Pre-flight checks for evaluation components
- **Fallback Metrics**: Alternative evaluation methods when Ragas unavailable

#### Implementation Details
```python
# src/evaluation/ragas_integration.py - Enhanced
def evaluate_with_fallback(question: str, answer: str, contexts: List[str]):
    try:
        return ragas.evaluate(question, answer, contexts)
    except ImportError:
        # Fallback to simple metrics
        return {
            'faithfulness': calculate_simple_faithfulness(answer, contexts),
            'relevancy': calculate_simple_relevancy(question, answer)
        }
```

#### Impact Assessment
- **Risk**: Low - error handling addition
- **Complexity**: Medium - fallback implementation
- **Testing**: Evaluation accuracy tests

---

### 3. Implementation Sequence

### Phase 1: Infrastructure (Week 1)
1. Update requirements files
2. Implement dependency verification
3. Configure pyright
4. Update CI/CD pipelines

### Phase 2: Core Functionality (Week 2)
1. Fix response generation logic
2. Update UI badge labels
3. Enhance evaluation framework
4. Add error handling

### Phase 3: Testing & Validation (Week 3)
1. Comprehensive testing
2. Performance validation
3. User acceptance testing
4. Documentation updates

---

### 4. Risk Mitigation

### Technical Risks
- **Dependency Conflicts**: Implement virtual environment isolation
- **Performance Impact**: Monitor and optimize new components
- **Backward Compatibility**: Ensure existing functionality preserved

### Operational Risks
- **Deployment Complexity**: Automate installation processes
- **User Impact**: Gradual rollout with feature flags
- **Support Load**: Provide clear error messages and documentation

---

### 5. Success Metrics

- **Dependency Resolution**: 100% successful installations
- **Type Safety**: 0 type-checking errors in CI
- **Response Quality**: >90% responses utilize retrieved contexts
- **UI Accuracy**: 100% correct badge labels
- **Evaluation Reliability**: 100% successful evaluation runs

---

### 6. Dependencies & Prerequisites

- Python 3.9+
- Access to package repositories (PyPI)
- LLM API access (if using external models)
- Development environment with IDE support

---

### 7. Testing Strategy

### Unit Testing
- Dependency verification functions
- Badge label management
- Response generation logic

### Integration Testing
- End-to-end chat functionality
- Evaluation pipeline
- UI component rendering

### Performance Testing
- Response generation latency
- Type checking execution time
- Memory usage with new dependencies

---

### 8. Maintenance Considerations

- Regular dependency updates
- Type checking as part of code review
- Monitoring of evaluation metrics
- UI consistency audits

---

*This document will be updated as implementation progresses and new requirements emerge.*