# Project Overview & Purpose

This repository contains the Personal RAG Copilot, a hybrid retrieval-augmented generation platform that combines dense vector search and lexical BM25 search with advanced ranking fusion capabilities. The system provides a Gradio 5 multipage application for querying a knowledge base, ingesting documents, evaluating response quality, and configuring system parameters. The core innovation is the Reciprocal Rank Fusion (RRF) approach that intelligently combines dense semantic search with lexical keyword matching to provide more robust and accurate retrieval results.

## Architecture & Key Files

The application follows a modular Python architecture with clear separation of concerns:

**Core Application Structure:**
- Main entry point: `app.py` (Gradio multipage application)
- Retrieval engine: `src/retrieval/` (hybrid search implementation)
- Ranking system: `src/ranking/` (RRF fusion and optional reranking)
- User interface: `src/ui/` (Gradio page implementations)
- Evaluation framework: `src/evaluation/` (Ragas integration)
- Configuration: `src/config/` (system settings and parameters)

**Critical Files and Directories:**
- `src/retrieval/dense.py` - Dense vector retrieval using Sentence-Transformers all-MiniLM-L6-v2 (384-dim)
- `src/retrieval/lexical.py` - BM25 lexical search implementation
- `src/retrieval/hybrid.py` - RRF fusion logic with k=60 default
- `src/ranking/reranker.py` - BGE-Reranker-v2-m3 cross-encoder implementation
- `src/ui/chat.py` - Main chat interface with streaming responses
- `src/ui/ingest.py` - Document upload and processing interface
- `src/ui/evaluate.py` - Ragas evaluation dashboard
- `src/ui/settings.py` - Configuration management interface
- `src/evaluation/ragas_integration.py` - Faithfulness and quality metrics
- `src/integrations/pinecone_client.py` - Vector database operations
- `requirements.txt` - Python dependencies specification
- `config/default_settings.yaml` - Default system configuration

**Vector Database Integration:**
- All Pinecone operations MUST use the repository pattern defined in `src/integrations/pinecone_client.py`
- Index dimension MUST be 384 to match all-MiniLM-L6-v2 embeddings
- Cosine similarity metric is required for all vector operations

## Development Environment & Commands

The application is built using Python 3.12 with Gradio 5 as the primary UI framework. All dependencies should already be installed in the environment.
CPU remains the default execution target, though optional OpenVINO/XPU acceleration paths may be used when available.

**Core Development Commands:**
- To run the multipage application: `python app.py`
- To run all unit tests: `python -m pytest tests/ -v`
- To run tests with coverage: `python -m pytest tests/ --cov=src --cov-report=html`
- To format code: `black src/ tests/ app.py`
- To run linting: `flake8 src/ tests/ app.py`
- To run type checking: `pyright`
- To validate configuration: `python -m src.config.validate`

**Testing Specific Components:**
- To test retrieval engine: `python -m pytest tests/test_retrieval/ -v`
- To test RRF fusion: `python -m pytest tests/test_ranking/test_rrf.py -v`
- To test Pinecone integration: `python -m pytest tests/test_integrations/test_pinecone.py -v`
- To test Ragas evaluation: `python -m pytest tests/test_evaluation/ -v`

**Performance Validation:**
- To benchmark retrieval performance: `python scripts/benchmark_retrieval.py`
- To validate RRF with k=60: `python scripts/validate_rrf.py`
- To test reranking latency: `python scripts/benchmark_reranking.py`

## Code Style & Conventions

**Naming Conventions:**
- Use `snake_case` for variables, functions, and module names
- Use `PascalCase` for class names (e.g., `RetrievalEngine`, `RRFFusion`)
- Use `UPPER_CASE` for constants (e.g., `DEFAULT_RRF_K`, `EMBEDDING_DIMENSION`)
- Prefix private methods with underscore (e.g., `_compute_rrf_scores`)

**RRF Implementation Standards:**
- RRF formula MUST use: `score(d) = Σᵢ 1/(k + rankᵢ(d))` with k=60 default
- All RRF functions MUST accept configurable `k` parameter per query
- Weight parameters MUST be named `w_dense` and `w_lexical` for clarity
- Return metadata MUST include `rrf_weights`, `component_scores`, and `fusion_method`

**Retrieval Engine Standards:**
- Dense embeddings MUST be 384-dimensional using `all-MiniLM-L6-v2`
- Validate Pinecone index dimension equals 384 before any upsert/query operations
- BM25 implementation MUST use `rank-bm25` library for consistency
- All retrieval functions MUST return `(results, metadata)` tuple format

**Error Handling:**
- All functions that can fail MUST return results and handle exceptions gracefully
- Use structured logging with appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Pinecone connection failures MUST have retry logic with exponential backoff
- Model loading failures MUST provide clear error messages and fallback options

**Evaluation Standards:**
- Ragas integration MUST compute faithfulness scores using official definition
- Evaluation results MUST include score, rationale, and confidence interval
- Quality thresholds: faithfulness < 0.7 triggers recommendations
- All evaluation metrics MUST be stored with timestamp and query context

**Performance Requirements:**
- Dense retrieval MUST complete within 500ms p95
- Lexical retrieval MUST complete within 200ms p95
- RRF fusion MUST complete within 100ms p95
- Reranking (when enabled) MUST complete within 1000ms additional latency
- Total query response time MUST be ≤ 2 seconds p95

## Testing & Validation Protocol

**Testing Framework:**
- Primary framework: `pytest` with `pytest-asyncio` for async operations
- Coverage target: Minimum 85% code coverage across all modules
- Performance testing: Use `pytest-benchmark` for latency validation
- Integration testing: Mock external services (Pinecone, Hugging Face) appropriately

**Required Test Coverage:**
- All public functions in `src/retrieval/` MUST have comprehensive unit tests
- RRF fusion logic MUST have tests validating k-value behavior and score calculation
- Pinecone integration MUST have tests for connection, upsert, query, and error scenarios
- Gradio UI components MUST have interaction tests for all user workflows
- Ragas evaluation MUST have tests validating metric computation accuracy

**Validation Protocol:**
- Before submitting work, ensure `python -m pytest tests/ -v` passes without errors
- Run `python scripts/validate_rrf.py` to verify RRF implementation matches specification
- Execute `python scripts/benchmark_retrieval.py` to confirm performance targets
- Validate Pinecone index configuration with `python scripts/validate_pinecone.py`
- Test multipage navigation with `python scripts/test_ui_routing.py`

**Performance Validation:**
- Retrieval latency MUST be measured and logged for each query type
- RRF fusion performance MUST be validated against different k values (30, 60, 100)
- Reranking overhead MUST be measured and displayed in UI when enabled
- Memory usage MUST remain under 8GB for full system operation

**Quality Assurance:**
- All commits MUST pass the full test suite before merge
- Performance benchmarks MUST not regress beyond 10% of baseline
- Ragas evaluation scores MUST be validated against known test cases
- Configuration validation MUST prevent invalid parameter combinations

## Pull Request (PR) Instructions

**Title Format:**
- For new features: `feat(scope): short description` (e.g., `feat(retrieval): add dynamic query weighting`)
- For bug fixes: `fix(scope): short description` (e.g., `fix(rrf): correct k-value handling for edge cases`)
- For improvements: `improve(scope): short description` (e.g., `improve(ui): enhance reranking performance display`)
- For documentation: `docs(scope): short description` (e.g., `docs(evaluation): add Ragas configuration guide`)

**Required PR Body Sections:**
```markdown
## Description:
[Detailed description of changes and motivation]

## Testing Done:
[Specific tests run and validation performed]

## Performance Impact:
[Any changes to retrieval latency, memory usage, or throughput]

## Configuration Changes:
[Any new parameters, defaults, or breaking configuration changes]

## Evaluation Results:
[If applicable, Ragas scores or quality metric changes]
```

**Review Requirements:**
- All PRs MUST include test coverage for new functionality
- Performance-impacting changes MUST include benchmark results
- RRF or ranking changes MUST include validation of score calculations
- UI changes MUST include screenshots or interaction descriptions
- Configuration changes MUST update default settings documentation

## Security & Non-Goals

**Security Guidelines:**
- All user input MUST be validated and sanitized to prevent injection attacks
- Never hardcode API keys, secrets, or credentials in source code
- Use environment variables for all external service credentials (Pinecone API keys)
- Document content MUST be sanitized during ingestion to prevent malicious content
- Query inputs MUST be validated for length, content, and format before processing
- Evaluation results containing sensitive information MUST be properly anonymized

**API Security:**
- Pinecone API keys MUST be loaded from environment variables or secure configuration
- Hugging Face model downloads MUST verify model authenticity when possible
- Rate limiting MUST be implemented for query endpoints if exposed externally
- Logging MUST NOT include sensitive user data or query contents

**Explicit Non-Goals:**
- Do not modify the CI/CD pipeline configuration files in `.github/workflows/` directory
- Do not add new third-party dependencies without explicit approval and security review
- Do not implement custom vector databases; stick to Pinecone integration pattern
- Do not modify core Gradio routing structure in `app.py` without architectural review
- Do not change default RRF k=60 value without performance validation and approval
- Do not implement alternative evaluation frameworks beyond Ragas without justification
- Do not modify the established retrieval modes (dense, lexical, hybrid) without architectural discussion
- Do not hardcode model paths; use configuration management for all model specifications
- Do not implement custom embedding models; stick to Sentence-Transformers all-MiniLM-L6-v2 (384-dim)
