# Personal RAG Copilot — Detailed Test Cases

**Version:** 1.0
**Date:** September 9, 2025
**Source:** test_plan.md

---

## Test Case Format

Each test case follows this structure:
- **ID:** Unique identifier
- **Title:** Descriptive name
- **Type:** Unit/Integration/E2E/Performance/Security
- **Priority:** Critical/High/Medium/Low
- **Preconditions:** Required setup
- **Test Steps:** Step-by-step procedure
- **Expected Result:** Success criteria
- **Acceptance Criteria:** Links to PRD/FRD ACs
- **Test Data:** Required inputs
- **Post-conditions:** Cleanup requirements

---

## 1. Dependency Management Test Cases

### TC-DEP-001: Dependency Installation Verification
- **ID:** TC-DEP-001
- **Title:** Verify successful installation of critical dependencies
- **Type:** Integration
- **Priority:** Critical
- **Preconditions:**
  - Clean Python virtual environment
  - Access to package repositories
  - requirements.txt updated with audit fix dependencies
- **Test Steps:**
  1. Create new virtual environment
  2. Run `pip install -r requirements.txt`
  3. Attempt import of each critical dependency:
     - `import ragas`
     - `import rank_bm25`
     - `import pyright`
  4. Check for ImportError exceptions
  5. Verify package versions match requirements
- **Expected Result:**
  - All imports successful without errors
  - No ImportError or ModuleNotFoundError
  - Package versions compatible with system
- **Acceptance Criteria:** AC-DEP-01
- **Test Data:** requirements.txt, virtual environment
- **Post-conditions:** Virtual environment can be reused

### TC-DEP-002: Version Compatibility Validation
- **ID:** TC-DEP-002
- **Title:** Ensure installed dependency versions are compatible
- **Type:** Unit
- **Priority:** High
- **Preconditions:**
  - Dependencies installed successfully
  - requirements.txt available
- **Test Steps:**
  1. Run `pip list` to check installed versions
  2. Compare with requirements.txt specifications
  3. Test basic functionality of each package:
     - Ragas: Create Faithfulness evaluator
     - rank-bm25: Create BM25 index
     - pyright: Run type checking on sample file
  4. Verify no version conflicts or deprecation warnings
- **Expected Result:**
  - All versions within specified ranges
  - Basic functionality works without errors
  - No compatibility issues detected
- **Acceptance Criteria:** AC-DEP-01
- **Test Data:** Sample Python file for pyright testing
- **Post-conditions:** None

### TC-DEP-003: Import Error Handling
- **ID:** TC-DEP-003
- **Title:** Test system behavior when dependencies are missing
- **Type:** Integration
- **Priority:** High
- **Preconditions:**
  - System with missing dependencies
  - Error handling code implemented
- **Test Steps:**
  1. Remove or mock missing dependencies
  2. Attempt to start application
  3. Check error messages and fallback behavior
  4. Verify graceful degradation
  5. Test dependency verification function
- **Expected Result:**
  - Clear error messages indicating missing dependencies
  - Application fails gracefully with helpful instructions
  - No crashes or unhandled exceptions
- **Acceptance Criteria:** AC-DEP-01
- **Test Data:** Mock missing dependency scenarios
- **Post-conditions:** Restore dependencies

---

## 2. Type-Checking Integration Test Cases

### TC-TYP-001: Pyright Configuration Validation
- **ID:** TC-TYP-001
- **Title:** Verify pyright configuration is correct and functional
- **Type:** Static Analysis
- **Priority:** High
- **Preconditions:**
  - pyright installed
  - pyrightconfig.json exists
  - Source code available
- **Test Steps:**
  1. Run `pyright --verifyconfig` to check configuration
  2. Execute `pyright` on entire codebase
  3. Review configuration errors and warnings
  4. Validate type checking settings:
     - Include/exclude patterns
     - Type checking mode
     - Python version compatibility
  5. Check for configuration-related errors
- **Expected Result:**
  - Configuration validation passes
  - No configuration errors reported
  - Settings appropriate for project
- **Acceptance Criteria:** AC-TYP-01
- **Test Data:** pyrightconfig.json, source files
- **Post-conditions:** None

### TC-TYP-002: Type Error Detection
- **ID:** TC-TYP-002
- **Title:** Ensure pyright detects type errors correctly
- **Type:** Static Analysis
- **Priority:** High
- **Preconditions:**
  - pyright configured and working
  - Test files with intentional type errors
- **Test Steps:**
  1. Create test file with type errors:
     - Missing type hints
     - Incorrect type annotations
     - Type mismatches
  2. Run pyright on test file
  3. Verify error detection and reporting
  4. Check error message clarity and accuracy
  5. Test with different severity levels
- **Expected Result:**
  - All type errors detected
  - Clear and accurate error messages
  - Appropriate severity levels
- **Acceptance Criteria:** AC-TYP-01
- **Test Data:** Test files with known type issues
- **Post-conditions:** Remove test files

### TC-TYP-003: CI/CD Integration
- **ID:** TC-TYP-003
- **Title:** Verify type checking integration with CI pipeline
- **Type:** Integration
- **Priority:** Medium
- **Preconditions:**
  - CI/CD pipeline configured
  - pyright available in CI environment
- **Test Steps:**
  1. Push code changes to trigger CI
  2. Monitor CI execution for type checking step
  3. Verify pyright runs successfully
  4. Check CI failure on type errors
  5. Validate error reporting in CI output
- **Expected Result:**
  - Type checking runs in CI
  - CI fails on type errors
  - Clear error reporting in CI logs
- **Acceptance Criteria:** AC-TYP-01
- **Test Data:** Code with type errors for CI testing
- **Post-conditions:** Fix type errors before merge

---

## 3. Chat Response Generation Test Cases

### TC-CHA-001: Context Synthesis Validation
- **ID:** TC-CHA-001
- **Title:** Verify response generation uses retrieved contexts
- **Type:** Unit
- **Priority:** Critical
- **Preconditions:**
  - Mock LLM service available
  - Sample contexts and query prepared
- **Test Steps:**
  1. Prepare query and list of retrieved documents
  2. Call response generation function
  3. Analyze generated response content
  4. Check for context utilization:
     - Key terms from contexts appear in response
     - Response addresses query using context information
     - No generic or echo responses
  5. Calculate context similarity score
- **Expected Result:**
  - Response incorporates context information
  - Context similarity >0.8 (cosine similarity)
  - Response directly addresses the query
- **Acceptance Criteria:** AC-CHA-01
- **Test Data:** Query="What is machine learning?", Contexts=[ML definition, examples]
- **Post-conditions:** None

### TC-CHA-002: Empty Context Handling
- **ID:** TC-CHA-002
- **Title:** Test response generation with no retrieved contexts
- **Type:** Unit
- **Priority:** High
- **Preconditions:**
  - Response generation function implemented
  - Mock empty context scenario
- **Test Steps:**
  1. Provide query with empty context list
  2. Call response generation function
  3. Verify fallback behavior
  4. Check error message quality
  5. Ensure no crashes or exceptions
- **Expected Result:**
  - Graceful handling of empty contexts
  - Appropriate fallback message
  - No unhandled exceptions
- **Acceptance Criteria:** AC-CHA-01
- **Test Data:** Query with empty context list
- **Post-conditions:** None

### TC-CHA-003: LLM Integration Testing
- **ID:** TC-CHA-003
- **Title:** Validate integration with LLM service
- **Type:** Integration
- **Priority:** High
- **Preconditions:**
  - LLM service mock or test instance
  - Response generation code
- **Test Steps:**
  1. Set up LLM mock with controlled responses
  2. Provide query and contexts
  3. Call response generation
  4. Verify LLM receives correct prompt
  5. Check response processing
  6. Test error handling for LLM failures
- **Expected Result:**
  - Correct prompt construction
  - Proper response parsing
  - Error handling for LLM issues
- **Acceptance Criteria:** AC-CHA-01
- **Test Data:** Mock LLM responses
- **Post-conditions:** None

---

## 4. UI Badge Correction Test Cases

### TC-BAD-001: Badge Label Mapping
- **ID:** TC-BAD-001
- **Title:** Verify correct badge labels for retrieval sources
- **Type:** Unit
- **Priority:** High
- **Preconditions:**
  - Badge management code implemented
  - Test data with different source types
- **Test Steps:**
  1. Test each source type mapping:
     - 'dense' → 'DENSE'
     - 'lexical' → 'LEXICAL'
     - 'fused' → 'FUSED'
  2. Verify case sensitivity handling
  3. Test invalid source types
  4. Check for consistent formatting
- **Expected Result:**
  - Correct label for each source type
  - Case-insensitive input handling
  - Error handling for invalid types
- **Acceptance Criteria:** AC-BAD-01
- **Test Data:** Source type strings
- **Post-conditions:** None

### TC-BAD-002: UI Badge Rendering
- **ID:** TC-BAD-002
- **Title:** Validate badge display in Gradio interface
- **Type:** E2E
- **Priority:** Medium
- **Preconditions:**
  - Gradio UI running
  - Test query with known retrieval results
- **Test Steps:**
  1. Submit query through UI
  2. Wait for response generation
  3. Inspect citation badges in response
  4. Verify badge labels match expected values
  5. Check visual styling and consistency
  6. Test with different retrieval modes
- **Expected Result:**
  - All badges display correct labels
  - Visual consistency across citations
  - No "SPARSE" labels present
- **Acceptance Criteria:** AC-BAD-01
- **Test Data:** Test query with mixed retrieval sources
- **Post-conditions:** None

### TC-BAD-003: Badge Consistency Across Components
- **ID:** TC-BAD-003
- **Title:** Ensure badge labels consistent across all UI components
- **Type:** Integration
- **Priority:** Medium
- **Preconditions:**
  - Multiple UI components using badges
  - Test scenarios with various retrieval types
- **Test Steps:**
  1. Test badge usage in different components:
     - Chat interface citations
     - Evaluation results
     - Transparency drawer
  2. Verify consistent label usage
  3. Check for hardcoded badge strings
  4. Validate centralized badge management
- **Expected Result:**
  - Consistent badge labels everywhere
  - No hardcoded strings in components
  - Centralized badge management working
- **Acceptance Criteria:** AC-BAD-01
- **Test Data:** Multi-component test scenarios
- **Post-conditions:** None

---

## 5. Evaluation Framework Test Cases

### TC-EVA-001: Ragas Faithfulness Computation
- **ID:** TC-EVA-001
- **Title:** Test Ragas faithfulness metric calculation
- **Type:** Integration
- **Priority:** High
- **Preconditions:**
  - ragas dependency installed
  - Sample question, answer, contexts
- **Test Steps:**
  1. Import Ragas Faithfulness evaluator
  2. Prepare test data:
     - Question: Specific query
     - Answer: Generated response
     - Contexts: Retrieved documents
  3. Execute faithfulness evaluation
  4. Verify metric value (0.0-1.0 range)
  5. Check rationale quality
  6. Validate computation time
- **Expected Result:**
  - Successful faithfulness calculation
  - Value within valid range
  - Meaningful rationale provided
  - Computation within time limits
- **Acceptance Criteria:** AC-EVA-02
- **Test Data:** Curated Q&A with contexts
- **Post-conditions:** None

### TC-EVA-002: Import Failure Handling
- **ID:** TC-EVA-002
- **Title:** Test system behavior when Ragas import fails
- **Type:** Unit
- **Priority:** High
- **Preconditions:**
  - Evaluation code with error handling
  - Mock import failure scenario
- **Test Steps:**
  1. Simulate Ragas import failure
  2. Attempt evaluation initialization
  3. Verify fallback mechanism activation
  4. Check error message quality
  5. Test continued system operation
- **Expected Result:**
  - Graceful handling of import failure
  - Appropriate fallback evaluation
  - Clear error messages
  - System remains functional
- **Acceptance Criteria:** AC-EVA-02
- **Test Data:** Mock import failure
- **Post-conditions:** Restore imports

### TC-EVA-003: Evaluation Performance
- **ID:** TC-EVA-003
- **Title:** Validate evaluation performance meets requirements
- **Type:** Performance
- **Priority:** Medium
- **Preconditions:**
  - Evaluation system operational
  - Performance measurement tools
- **Test Steps:**
  1. Execute evaluation on various input sizes
  2. Measure computation time
  3. Monitor memory usage
  4. Test concurrent evaluation requests
  5. Validate timeout handling
- **Expected Result:**
  - Evaluation completes within 30 seconds
  - Memory usage remains reasonable
  - No performance degradation under load
- **Acceptance Criteria:** AC-EVA-02
- **Test Data:** Various input sizes and complexities
- **Post-conditions:** None

---

## 6. Retrieval Engine Test Cases

### TC-RET-001: Dense Retrieval Functionality
- **ID:** TC-RET-001
- **Title:** Test dense vector retrieval with MiniLM-L6-v2
- **Type:** Integration
- **Priority:** High
- **Preconditions:**
  - Pinecone mock or test instance
  - Dense retriever implementation
  - Test documents embedded
- **Test Steps:**
  1. Index test documents with dense embeddings
  2. Submit test query
  3. Execute dense retrieval
  4. Verify results:
     - Correct number of results
     - Proper Document objects
     - Valid similarity scores
     - Source type = 'dense'
  5. Check embedding dimensions (384)
- **Expected Result:**
  - Successful retrieval of relevant documents
  - Correct metadata and scores
  - 384-dimensional embeddings
- **Acceptance Criteria:** FR-RET-001, AC-RET-001-1 to AC-RET-001-4
- **Test Data:** Test documents and queries
- **Post-conditions:** None

### TC-RET-002: Lexical BM25 Retrieval
- **ID:** TC-RET-002
- **Title:** Validate lexical retrieval with BM25 algorithm
- **Type:** Integration
- **Priority:** High
- **Preconditions:**
  - BM25 implementation (rank-bm25 or bm25s)
  - Test document corpus
- **Test Steps:**
  1. Create BM25 index from test documents
  2. Submit lexical query
  3. Execute retrieval
  4. Verify results:
     - BM25 scores calculated
     - Documents ranked by lexical relevance
     - Source type = 'lexical'
  5. Test preprocessing (tokenization, stemming)
- **Expected Result:**
  - Accurate lexical matching
  - Proper BM25 scoring
  - Correct source identification
- **Acceptance Criteria:** FR-RET-002, AC-RET-002-1 to AC-RET-002-4
- **Test Data:** Text documents with known lexical patterns
- **Post-conditions:** None

### TC-RET-003: Hybrid Retrieval Orchestration
- **ID:** TC-RET-003
- **Title:** Test parallel execution of dense and lexical retrieval
- **Type:** Integration
- **Priority:** High
- **Preconditions:**
  - Both dense and lexical retrievers operational
  - Hybrid retriever implementation
- **Test Steps:**
  1. Configure hybrid mode
  2. Submit test query
  3. Monitor parallel execution
  4. Verify results from both retrievers
  5. Check hybrid result structure
- **Expected Result:**
  - Both retrieval methods executed
  - Results properly combined
  - No execution errors
- **Acceptance Criteria:** FR-RET-003, AC-RET-003-1 to AC-RET-003-4
- **Test Data:** Query requiring both dense and lexical matching
- **Post-conditions:** None

### TC-RET-004: RRF Fusion Correctness
- **ID:** TC-RET-004
- **Title:** Validate Reciprocal Rank Fusion implementation
- **Type:** Unit
- **Priority:** Critical
- **Preconditions:**
  - RRF implementation available
  - Test result sets from multiple retrievers
- **Test Steps:**
  1. Prepare mock results from dense and lexical
  2. Apply RRF fusion with k=60
  3. Verify fusion formula: score(d) = Σᵢ 1/(k + rankᵢ(d))
  4. Check final ranking order
  5. Test different k values
  6. Validate per-retriever score components
- **Expected Result:**
  - Correct RRF calculation
  - Proper ranking fusion
  - Score components preserved
- **Acceptance Criteria:** FR-RET-004, AC-RRF-01
- **Test Data:** Mock retrieval results with known rankings
- **Post-conditions:** None

---

## 7. Ranking and Reranking Test Cases

### TC-RNK-001: Reranking Toggle Functionality
- **ID:** TC-RNK-001
- **Title:** Test optional reranking user control
- **Type:** Integration
- **Priority:** Medium
- **Preconditions:**
  - Reranking implementation
  - UI toggle available
  - BGE-Reranker model accessible
- **Test Steps:**
  1. Disable reranking toggle
  2. Submit query and verify no reranking
  3. Enable reranking toggle
  4. Submit same query and verify reranking applied
  5. Check reranking performance impact
- **Expected Result:**
  - Toggle controls reranking correctly
  - Performance difference measurable
  - No errors in either mode
- **Acceptance Criteria:** FR-RNK-001, AC-RER-01
- **Test Data:** Test query with >20 initial results
- **Post-conditions:** None

### TC-RNK-002: BGE-Reranker Integration
- **ID:** TC-RNK-002
- **Title:** Validate BGE-Reranker-v2-m3 integration
- **Type:** Integration
- **Priority:** Medium
- **Preconditions:**
  - BGE-Reranker model available
  - Test documents for reranking
- **Test Steps:**
  1. Prepare top 20 retrieved documents
  2. Apply BGE-Reranker reranking
  3. Verify output: top 5 reranked results
  4. Check reranking quality (better relevance)
  5. Monitor computation time
- **Expected Result:**
  - Successful reranking to 5 results
  - Improved relevance ordering
  - Reasonable computation time
- **Acceptance Criteria:** FR-RNK-001, AC-RER-01
- **Test Data:** 20 documents with query for reranking
- **Post-conditions:** None

### TC-RNK-003: Performance Optimization
- **ID:** TC-RNK-003
- **Title:** Test reranking performance controls
- **Type:** Performance
- **Priority:** Medium
- **Preconditions:**
  - Reranking with caching enabled
  - Performance measurement tools
- **Test Steps:**
  1. Test reranking without caching
  2. Enable caching and retest
  3. Measure performance improvement
  4. Test timeout handling
  5. Verify fallback to fusion-only
- **Expected Result:**
  - Caching improves performance
  - Timeout prevents hangs
  - Graceful fallback on failure
- **Acceptance Criteria:** FR-RNK-002, AC-RNK-002-1 to AC-RNK-002-4
- **Test Data:** Repeated reranking requests
- **Post-conditions:** None

---

## 8. User Interface Test Cases

### TC-UI-001: Multipage Routing
- **ID:** TC-UI-001
- **Title:** Verify Gradio multipage navigation
- **Type:** E2E
- **Priority:** High
- **Preconditions:**
  - Gradio multipage application running
  - All pages implemented
- **Test Steps:**
  1. Access default route (/)
  2. Navigate to /ingest
  3. Navigate to /evaluate
  4. Navigate to /settings
  5. Verify URL changes and content loading
  6. Test navbar functionality
- **Expected Result:**
  - All routes accessible
  - Content loads correctly
  - Navbar navigation works
- **Acceptance Criteria:** FR-UI-001, AC-MP-01
- **Test Data:** None
- **Post-conditions:** None

### TC-UI-002: Retrieval Transparency Display
- **ID:** TC-UI-002
- **Title:** Test badge and details display
- **Type:** E2E
- **Priority:** Medium
- **Preconditions:**
  - Chat interface with transparency features
  - Test query with results
- **Test Steps:**
  1. Submit query through chat
  2. Inspect citation badges
  3. Open details drawer
  4. Verify displayed information:
     - Badge labels (DENSE/LEXICAL/FUSED)
     - Rank, score, retriever, snippet
  5. Test visual styling
- **Expected Result:**
  - Correct badge display
  - Complete details information
  - Good visual presentation
- **Acceptance Criteria:** FR-UI-003, AC-HYB-01
- **Test Data:** Query with diverse retrieval sources
- **Post-conditions:** None

### TC-UI-003: Streaming Chat Response
- **ID:** TC-UI-003
- **Title:** Validate streaming response functionality
- **Type:** E2E
- **Priority:** Medium
- **Preconditions:**
  - ChatInterface with streaming enabled
  - Mock streaming response
- **Test Steps:**
  1. Submit query
  2. Observe response streaming
  3. Verify partial token display
  4. Check typing indicators
  5. Test interruption handling
- **Expected Result:**
  - Smooth streaming display
  - Proper typing indicators
  - No display artifacts
- **Acceptance Criteria:** FR-UI-002, AC-UI-002-1 to AC-UI-002-4
- **Test Data:** Long-form response for streaming
- **Post-conditions:** None

---

## 9. End-to-End Workflow Test Cases

### TC-E2E-001: Complete Query Processing
- **ID:** TC-E2E-001
- **Title:** Test full query processing pipeline
- **Type:** E2E
- **Priority:** Critical
- **Preconditions:**
  - All components operational
  - Test document corpus indexed
- **Test Steps:**
  1. Submit query through UI
  2. Verify retrieval execution
  3. Check RRF fusion
  4. Validate response generation
  5. Confirm evaluation execution
  6. Review UI display
- **Expected Result:**
  - Complete pipeline execution
  - Correct results at each stage
  - Proper UI updates
- **Acceptance Criteria:** Multiple ACs covered
- **Test Data:** End-to-end test scenario
- **Post-conditions:** None

### TC-E2E-002: Error Recovery Workflow
- **ID:** TC-E2E-002
- **Title:** Test system resilience to errors
- **Type:** E2E
- **Priority:** High
- **Preconditions:**
  - Error injection capabilities
  - Error handling implemented
- **Test Steps:**
  1. Inject retrieval failure
  2. Verify fallback behavior
  3. Inject LLM failure
  4. Check error recovery
  5. Test evaluation failure handling
- **Expected Result:**
  - Graceful error handling
  - Appropriate user feedback
  - System stability maintained
- **Acceptance Criteria:** Error handling ACs
- **Test Data:** Error injection scenarios
- **Post-conditions:** Restore normal operation

---

## 10. Performance Test Cases

### TC-PERF-001: Unit Test Execution Time
- **ID:** TC-PERF-001
- **Title:** Validate unit test suite performance
- **Type:** Performance
- **Priority:** High
- **Preconditions:**
  - Complete unit test suite
  - Performance measurement tools
- **Test Steps:**
  1. Execute full unit test suite
  2. Measure total execution time
  3. Identify slowest tests
  4. Optimize if >30 seconds
  5. Verify parallel execution benefits
- **Expected Result:**
  - Suite completes in <30 seconds
  - No individual test >5 seconds
  - Parallel execution effective
- **Acceptance Criteria:** Performance targets
- **Test Data:** Full test suite
- **Post-conditions:** None

### TC-PERF-002: Retrieval Performance
- **ID:** TC-PERF-002
- **Title:** Test retrieval operation performance
- **Type:** Performance
- **Priority:** Medium
- **Preconditions:**
  - Indexed document corpus
  - Performance monitoring
- **Test Steps:**
  1. Execute retrieval operations
  2. Measure response times
  3. Test different query types
  4. Monitor resource usage
  5. Validate scaling behavior
- **Expected Result:**
  - Retrieval <2 seconds without reranking
  - Reasonable resource usage
  - Consistent performance
- **Acceptance Criteria:** Performance SLAs
- **Test Data:** Various query patterns
- **Post-conditions:** None

---

## Test Case Summary

| Area | Test Cases | Critical | High | Medium | Low | Total |
|------|------------|----------|------|--------|-----|-------|
| Dependencies | 3 | 1 | 2 | 0 | 0 | 3 |
| Type Checking | 3 | 0 | 2 | 1 | 0 | 3 |
| Response Generation | 3 | 1 | 2 | 0 | 0 | 3 |
| UI Badges | 3 | 0 | 1 | 2 | 0 | 3 |
| Evaluation | 3 | 0 | 2 | 1 | 0 | 3 |
| Retrieval | 4 | 1 | 3 | 0 | 0 | 4 |
| Ranking | 3 | 0 | 0 | 3 | 0 | 3 |
| UI | 3 | 0 | 1 | 2 | 0 | 3 |
| E2E | 2 | 1 | 1 | 0 | 0 | 2 |
| Performance | 2 | 0 | 1 | 1 | 0 | 2 |
| **Total** | **29** | **4** | **15** | **10** | **0** | **29** |

**Coverage Analysis:**
- **Acceptance Criteria:** 100% coverage of audit fix ACs
- **Risk Areas:** All high-risk areas covered
- **Test Types:** Balanced mix of unit, integration, E2E
- **Priority Distribution:** Focus on critical and high-priority tests

**Implementation Notes:**
- All test cases include detailed steps and expected results
- Test data requirements clearly specified
- Acceptance criteria linkages established
- Performance benchmarks defined
- Error scenarios covered