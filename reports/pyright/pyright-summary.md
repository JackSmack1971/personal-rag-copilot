# Pyright Summary

| Run | Errors | Warnings | Total |
| --- | --- | --- | --- |
| Baseline | 733 | 1 | 734 |
| After fixes | 639 | 1 | 640 |

## Top Rules
|Rule|Count|
|---|---|
|reportUnknownMemberType|130|
|reportUnknownParameterType|126|
|reportUnknownVariableType|110|
|reportMissingParameterType|105|
|reportUnknownArgumentType|80|
|reportUnknownLambdaType|44|
|reportArgumentType|38|
|reportUnusedImport|21|
|reportAttributeAccessIssue|16|
|reportPrivateUsage|16|
|reportOptionalCall|9|
|reportOptionalMemberAccess|8|
|reportUnusedVariable|6|
|reportMissingTypeArgument|5|
|reportMissingTypeStubs|5|
|reportCallIssue|4|
|reportGeneralTypeIssues|3|
|reportMissingImports|2|
|reportReturnType|2|
|reportUnsupportedDunderAll|2|

## Top Files
|File|Count|
|---|---|
|/workspace/personal-rag-copilot/tests/test_ui/test_ingest.py|67|
|/workspace/personal-rag-copilot/tests/test_integrations/test_pinecone_client.py|56|
|/workspace/personal-rag-copilot/tests/test_services/test_document_service.py|55|
|/workspace/personal-rag-copilot/src/integrations/pinecone_client.py|50|
|/workspace/personal-rag-copilot/src/ranking/reranker.py|43|
|/workspace/personal-rag-copilot/src/ui/settings.py|41|
|/workspace/personal-rag-copilot/src/ui/ingest.py|40|
|/workspace/personal-rag-copilot/src/ui/evaluate.py|35|
|/workspace/personal-rag-copilot/tests/conftest.py|27|
|/workspace/personal-rag-copilot/tests/test_retrieval/test_hybrid_rerank.py|26|
|/workspace/personal-rag-copilot/tests/test_retrieval/test_dense.py|25|
|/workspace/personal-rag-copilot/tests/test_ranking/test_reranker.py|21|
|/workspace/personal-rag-copilot/src/monitoring/performance.py|16|
|/workspace/personal-rag-copilot/src/retrieval/dense.py|16|
|/workspace/personal-rag-copilot/tests/test_ui/test_evaluate.py|16|
|/workspace/personal-rag-copilot/tests/test_query_service.py|15|
|/workspace/personal-rag-copilot/tests/test_retrieval/conftest.py|14|
|/workspace/personal-rag-copilot/src/retrieval/lexical.py|13|
|/workspace/personal-rag-copilot/tests/test_ui/test_chat.py|13|
|/workspace/personal-rag-copilot/tests/test_retrieval/test_hybrid.py|12|

## Heuristic Suggestions
- Consider downgrading or disabling the noisiest rules in `pyrightconfig.json` via `"<ruleName>": "warning"|"none"` under `report*` keys.
- Exclude generated or vendor code if it appears in Top Files (add to `exclude`).
- If stubs are missing for third-party libs, add packages to `typings/` or install types (e.g., `types-<pkg>`).
- For external modules flagged as missing, ensure they are in your runtime env or mark as optional in settings if intentional.
