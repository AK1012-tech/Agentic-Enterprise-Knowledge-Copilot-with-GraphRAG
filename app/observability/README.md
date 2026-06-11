"""
Observability Documentation: LangGraph + LangSmith Integration

This module provides detailed information about the observability layer
for the Enterprise Knowledge Copilot with GraphRAG.

## Overview

The system now uses:
1. **LangGraph StateGraph** - Orchestrates agent workflow with explicit state machine
2. **LangSmith Tracing** - Records all agent node executions, inputs/outputs, timings

## Architecture

### State Machine Flow

    Question Input
        ↓
    [PLANNER] → Decides use_retrieval, use_graph
        ↓
    [RETRIEVER] → Hybrid search + Graph retrieval
        ↓
    [SUMMARIZER] → Build LLM prompt
        ↓
    [COMPLETER] → LLM inference
        ↓
    [VERIFIER] → Validate answer
        ↓
    Response Output

Each node receives and updates the shared AgentState, enabling full traceability.

## Key Components

### 1. AgentState (app/graph/agent_state.py)

Defines the TypedDict schema for data flowing through the graph:

```python
class AgentState(TypedDict):
    question: str
    document_ids: list[str] | None
    session_id: str
    tenant_id: str
    user_id: str
    plan: PlanDecision
    contexts: list[dict]           # Retrieved chunks
    graph_context: list[GraphEdge]  # Retrieved relationships
    prompt: str
    answer: str
    verified: bool
    metadata: AgentMetadata
    error: str | None
```

The metadata field tracks:
- Session and tenant info
- Question hash for tracing
- Execution times per node (plan_time, retrieval_time, etc.)

### 2. State Graph (app/graph/state_graph.py)

Implements AgentGraphBuilder which:
- Creates nodes for each agent (planner, retriever, summarizer, completer, verifier)
- Each node logs its execution time and outputs
- Handles errors gracefully without breaking the pipeline
- Returns compiled graph ready for execution

Example node:
```python
def planner_node(self, state: AgentState) -> dict:
    start_time = time.time()
    plan = self.planner.plan(state["question"])
    elapsed = time.time() - start_time
    logger.info(f"[PLANNER] Execution time: {elapsed:.3f}s | use_retrieval={plan['use_retrieval']}")
    return {"plan": plan, "metadata": {...}, "error": None}
```

### 3. LangSmith Configuration (app/observability/langsmith_config.py)

Manages LangSmith integration:
- Singleton pattern ensures one configuration instance
- Checks `LANGCHAIN_TRACING_V2` env var to enable/disable
- Creates metadata for trace tagging and filtering
- Client available for advanced tracing patterns

### 4. Updated Workflow (app/workflows/agentic_workflow.py)

Uses compiled StateGraph instead of manual orchestration:

```python
class AgenticGraphRagWorkflow:
    def __init__(self, settings: Settings):
        self.graph = build_agent_graph(settings)
        self.langsmith_config = get_langsmith_config(settings)

    def answer(self, request: ChatRequest) -> dict:
        initial_state: AgentState = {...}
        
        # LangSmith traces this entire execution
        final_state = self.graph.invoke(initial_state, config=config)
        
        return response
```

## Enabling Observability

### Step 1: Get LangSmith API Key
1. Visit https://smith.langchain.com
2. Create account / login
3. Go to Settings → API Keys
4. Copy your API key

### Step 2: Configure Environment
In `.env`:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_api_key_here
LANGCHAIN_PROJECT=enterprise-knowledge-copilot
```

### Step 3: Run Application
```bash
uvicorn app.main:app --reload
```

### Step 4: View Traces
1. Go to https://smith.langchain.com
2. Navigate to project "enterprise-knowledge-copilot"
3. Each chat request creates a trace showing:
   - Full execution graph
   - Node execution times
   - Input/output at each step
   - Session and tenant info

## Trace Hierarchy

Each chat request creates a trace with this structure:

```
Chat Request Trace (root)
├── Planner Node
│   ├── Input: question
│   └── Output: plan (use_retrieval, use_graph)
├── Retriever Node
│   ├── Input: question, plan
│   ├── Hybrid Search
│   └── Graph Retrieval
├── Summarizer Node
│   ├── Input: question, contexts, graph_context
│   └── Output: prompt
├── Completer Node
│   ├── Input: prompt
│   └── Output: answer
└── Verifier Node
    ├── Input: answer, contexts
    └── Output: verified (bool)
```

## Metrics Available in LangSmith

### Per-Node Metrics
- **Latency**: Time each agent node took to execute
- **Input Size**: Size of inputs passed to node
- **Output Size**: Size of data returned by node
- **Error Rate**: % of executions that failed at this node

### Trace-Level Metrics
- **Total Latency**: Full end-to-end request time
- **Citation Count**: Number of sources retrieved
- **Verification Score**: Answer was verified or not
- **Cache Hit**: Whether response was served from cache

### Aggregated Insights
- **Average planner latency**: Helps identify slow planning
- **Retrieval performance**: Compare hybrid vs graph retrieval
- **LLM inference time**: Track model performance
- **End-to-end latency**: Overall system responsiveness

## Logging Output

Each node logs to stdout/logs:

```
[PLANNER] Execution time: 0.001s | use_retrieval=True | use_graph=False
[RETRIEVER] Hybrid search returned 5 chunks | Question: What is...?
[RETRIEVER] Graph retrieval returned 2 edges
[SUMMARIZER] Prompt built in 0.002s | Prompt length: 1523 chars
[COMPLETER] LLM response generated in 1.234s
[VERIFIER] Verification completed in 0.001s | verified=True
[WORKFLOW] Graph execution completed | answer_length=156 | citations=5 | verified=True
```

## Code Examples

### 1. Basic Usage (No Change to API Consumers)

```python
from app.api.schemas.chat_schema import ChatRequest
from app.workflows.agentic_workflow import AgenticGraphRagWorkflow
from app.utils.config import get_settings

workflow = AgenticGraphRagWorkflow(get_settings())
result = workflow.answer(ChatRequest(question="What is X?", tenant_id="demo"))
```

All tracing happens automatically when LangSmith is enabled!

### 2. Advanced: Custom Tracing

If you need to add custom tracing:

```python
from langsmith import trace

@trace
def my_custom_function(data):
    # This function's execution will be traced
    pass
```

## Testing Observability

Run the tests with tracing enabled:

```bash
LANGCHAIN_TRACING_V2=true LANGCHAIN_API_KEY=xxx pytest tests/
```

Each test execution will create traces you can inspect in LangSmith dashboard.

## Performance Impact

- **With Tracing Disabled**: Minimal overhead (env var check only)
- **With Tracing Enabled**: ~5-10ms per request for trace submission
  - Async submission doesn't block request processing
  - Configurable batch sizes for production

## Troubleshooting

### Traces Not Appearing
1. Verify `LANGCHAIN_TRACING_V2=true` is set
2. Check `LANGCHAIN_API_KEY` is correct (starts with `ls_`)
3. Verify `LANGCHAIN_PROJECT` name matches in smith.langchain.com
4. Check logs for connection errors

### Performance Issues
1. If trace submission is slow:
   - Reduce batch size in LangSmith config
   - Or disable tracing in production and enable selectively
2. Use `LANGSMITH_DEBUG=1` for detailed debug logs

### High Memory Usage
1. Traces are submitted asynchronously in batches
2. For high-volume systems, configure batch_size or timeout
3. Or sample traces (trace only 1% of requests)

## Future Enhancements

1. **Custom Metrics**: Track domain-specific KPIs
   - Document retrieval precision
   - Answer relevance scores
   - Cache hit rate by query type

2. **Sampling Strategies**: 
   - Trace 100% of errors
   - Sample 10% of successes
   - Trace all high-latency requests

3. **Alerts & Monitors**:
   - Alert if planner latency > 100ms
   - Alert if verification fails on high-confidence queries
   - Monitor cache hit rate degradation

4. **Integration Tests**:
   - Automated tests that verify trace structure
   - Performance regression tests
   - Trace comparison across versions

## References

- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- LangSmith Docs: https://docs.smith.langchain.com/
- LangChain Tracing: https://python.langchain.com/docs/langsmith/
"""

# This file serves as comprehensive documentation.
# Import this module or reference this docstring for detailed information.
