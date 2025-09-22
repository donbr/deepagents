# Multi-Strategy Retrieval Comparison

Compare all retrieval strategies for the query: **$ARGUMENTS**

## Process

1. **Query Preparation**: Normalize and prepare the query for consistent evaluation
2. **Parallel Execution**: Run all 6 retrieval strategies simultaneously
3. **Result Collection**: Gather documents, timing, and metadata from each strategy
4. **Quality Assessment**: Evaluate relevance and accuracy of retrieved content
5. **Performance Analysis**: Compare latency, token usage, and efficiency
6. **Recommendation**: Identify optimal strategy for the query type

## Strategies Compared

1. **BM25**: Keyword-based exact matching
2. **Vector**: Semantic similarity search
3. **Parent Document**: Hierarchical context retrieval
4. **Multi-Query**: Query expansion and aggregation
5. **Rerank**: LLM-based result reranking
6. **Ensemble**: Reciprocal Rank Fusion combination

## Comparison Metrics

- **Retrieval Time**: Latency for each strategy (target: <2s)
- **Document Quality**: Relevance scoring of retrieved content
- **Overlap Analysis**: Common documents across strategies
- **Unique Insights**: Strategy-specific valuable results
- **Cost Analysis**: Token usage and computational overhead
- **Accuracy Score**: Semantic similarity to expected results

## Expected Output

- **Strategy Rankings**: Performance-ordered list with scores
- **Timing Comparison**: Latency breakdown and efficiency analysis
- **Quality Matrix**: Relevance scores across all strategies
- **Recommendation**: Best strategy for this query type with reasoning
- **Insights**: Unique findings and strategy-specific advantages
- **Visualization**: Performance comparison charts and metrics

## Usage Examples

- `/project:strategy-compare "How does machine learning work?"` - Compare for educational query
- `/project:strategy-compare "Fix authentication bug in login.py"` - Compare for technical query
- `/project:strategy-compare "Latest trends in AI research"` - Compare for current events query

## Query Types & Strategy Recommendations

- **Factual Questions**: BM25 often excels for exact matches
- **Conceptual Queries**: Vector search for semantic understanding
- **Complex Topics**: Multi-query or ensemble for comprehensive coverage
- **Technical Issues**: Parent document for code context
- **Precision Required**: Rerank for highest accuracy

Use the MCP tool `strategy_compare` to execute this comprehensive comparison workflow.