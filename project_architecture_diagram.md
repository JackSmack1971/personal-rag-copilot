## File Structure Diagram

```
personal-rag-copilot/
├── .github/                          # CI/CD workflows and issue templates
│   └── workflows/
│       ├── main.yml                  # Main CI pipeline
│       ├── benchmark.yml             # Performance validation workflow
│       └── lint-and-test.yml         # Code quality checks
├── config/                           # System configuration management
│   ├── default_settings.yaml         # Default system parameters
│   ├── development.yaml              # Development environment config
│   ├── production.yaml               # Production environment config
│   └── test.yaml                     # Test environment settings
├── docs/                             # Project documentation
│   ├── architecture.md               # System architecture overview
│   ├── api.md                        # API documentation
│   ├── deployment.md                 # Deployment instructions
│   └── user_guide.md                 # End-user documentation
├── scripts/                          # Helper and automation scripts
│   ├── benchmark_retrieval.py        # Retrieval performance validation
│   ├── validate_rrf.py               # RRF implementation verification
│   ├── benchmark_reranking.py        # Reranking latency testing
│   ├── validate_pinecone.py          # Pinecone index validation
│   └── test_ui_routing.py            # Multipage navigation testing
├── src/                              # Main source code
│   ├── config/                       # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py               # Settings loader and validator
│   │   └── validate.py               # Configuration validation logic
│   ├── evaluation/                   # Quality assessment framework
│   │   ├── __init__.py
│   │   ├── ragas_integration.py      # Faithfulness and quality metrics
│   │   ├── metrics.py                # Custom evaluation metrics
│   │   └── quality_thresholds.py     # Quality-based recommendation logic
│   ├── integrations/                 # External service integrations
│   │   ├── __init__.py
│   │   ├── pinecone_client.py        # Vector database operations
│   │   ├── huggingface_models.py     # Model loading and caching
│   │   └── api_clients.py            # External API management
│   ├── ranking/                      # Ranking and reranking system
│   │   ├── __init__.py
│   │   ├── reranker.py               # BGE-Reranker-v2-m3 implementation
│   │   ├── rrf_fusion.py             # Reciprocal Rank Fusion logic
│   │   └── ranking_utils.py          # Ranking utility functions
│   ├── retrieval/                    # Hybrid search implementation
│   │   ├── __init__.py
│   │   ├── dense.py                  # Dense vector retrieval (all-MiniLM-L6-v2)
│   │   ├── lexical.py                # BM25 lexical search
│   │   ├── hybrid.py                 # RRF fusion with dynamic weighting
│   │   └── query_analysis.py         # Query characteristics detection
│   ├── ui/                           # Gradio 5 multipage interface
│   │   ├── __init__.py
│   │   ├── chat.py                   # Main chat interface with streaming
│   │   ├── ingest.py                 # Document upload and processing
│   │   ├── evaluate.py               # Ragas evaluation dashboard
│   │   ├── settings.py               # Configuration management interface
│   │   └── components/               # Reusable UI components
│   │       ├── __init__.py
│   │       ├── transparency.py       # Citation badges and details drawer
│   │       └── performance.py        # Performance metrics display
│   ├── models/                       # Data models and schemas
│   │   ├── __init__.py
│   │   ├── document.py               # Document and chunk models
│   │   ├── query.py                  # Query and result models
│   │   └── evaluation.py             # Evaluation result models
│   ├── services/                     # Business logic services
│   │   ├── __init__.py
│   │   ├── document_service.py       # Document ingestion and management
│   │   ├── query_service.py          # Query processing orchestration
│   │   ├── evaluation_service.py     # Quality assessment coordination
│   │   └── index_service.py          # Index management operations
│   ├── api/                          # RESTful API endpoints
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── query.py              # Query API endpoints
│   │   │   ├── documents.py          # Document management endpoints
│   │   │   ├── config.py             # Configuration API endpoints
│   │   │   └── health.py             # Health check endpoints
│   │   └── middleware/               # API middleware
│   │       ├── __init__.py
│   │       ├── auth.py               # Authentication middleware
│   │       └── rate_limiting.py      # Rate limiting implementation
│   └── utils/                        # Shared utilities and helpers
│       ├── __init__.py
│       ├── logging.py                # Structured logging configuration
│       ├── performance.py            # Performance monitoring utilities
│       └── validation.py             # Input validation helpers
├── tests/                            # Automated test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration and fixtures
│   ├── unit/                         # Unit tests
│   │   ├── test_retrieval/
│   │   │   ├── test_dense.py
│   │   │   ├── test_lexical.py
│   │   │   └── test_hybrid.py
│   │   ├── test_ranking/
│   │   │   ├── test_rrf.py
│   │   │   └── test_reranker.py
│   │   ├── test_evaluation/
│   │   │   └── test_ragas_integration.py
│   │   └── test_integrations/
│   │       └── test_pinecone.py
│   ├── integration/                  # Integration tests
│   │   ├── test_api/
│   │   │   └── test_query_endpoints.py
│   │   ├── test_ui/
│   │   │   └── test_multipage_routing.py
│   │   └── test_end_to_end.py
│   └── fixtures/                     # Test data and fixtures
│       ├── sample_documents/
│       └── test_queries.json
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore patterns
├── .pre-commit-config.yaml           # Pre-commit hooks configuration
├── app.py                            # Main Gradio application entry point
├── Dockerfile                        # Container deployment configuration
├── docker-compose.yml                # Local development environment
├── requirements.txt                  # Python dependencies
├── requirements-dev.txt              # Development dependencies
├── pyproject.toml                    # Python project configuration
└── README.md                         # Project overview and setup
```

## Architectural Rationale

* **Modular Retrieval Architecture:** The `src/retrieval/` structure directly maps to the three retrieval modes specified in PRD section 2.1 (dense, lexical, hybrid), with dedicated modules for each approach and the RRF fusion logic that serves as the system's core innovation.

* **Separation of Ranking Concerns:** Following the FRD's FR-RNK requirements, `src/ranking/` isolates the optional BGE-Reranker-v2-m3 cross-encoder implementation and RRF fusion logic, enabling the toggle-based reranking functionality described in PRD section 2.3.

* **Multipage UI Structure:** The `src/ui/` organization directly reflects the Gradio 5 multipage requirements from PRD section 2.5, with dedicated modules for Chat, Ingest, Evaluate, and Settings pages as specified in the FRD's FR-UI functional requirements.

* **Evaluation-First Design:** The dedicated `src/evaluation/` directory addresses the "QA you can trust" strategy from PRD section 1, implementing Ragas faithfulness metrics as specified in FRD section FR-EVAL-001, treating quality assessment as a first-class architectural concern.

* **Integration Abstraction:** The `src/integrations/` directory encapsulates external dependencies (Pinecone, HuggingFace) following the repository pattern mentioned in the development guidelines, ensuring clean separation from business logic and facilitating testing with mocked services.

* **Performance Validation Infrastructure:** The `scripts/` directory contains the specific benchmarking tools referenced in the development commands (benchmark_retrieval.py, validate_rrf.py), supporting the performance requirements of sub-2-second p95 response times specified in the FRD.

* **Configuration Management:** The top-level `config/` directory and `src/config/` module address the extensive configuration requirements (RRF k-values, model parameters, performance settings) outlined in FRD section FR-CFG, enabling the user-tunable behavior emphasized in the PRD strategy.

* **API-Ready Architecture:** Although the primary interface is Gradio, the `src/api/` structure anticipates the RESTful API requirements mentioned in FRD section 4.2, providing programmatic access for future integrations while maintaining the current UI-focused approach.
