# RAG System Evaluation

Evaluate the RAG system performance for strategy: **$ARGUMENTS**

## Process

1. **Strategy Validation**: Verify the specified strategy exists and is configured
2. **Golden Dataset**: Load the curated test dataset (golden_set.jsonl)
3. **Batch Evaluation**: Run RAGAS evaluation across all test cases
4. **Metrics Calculation**: Compute relevancy, precision, recall, and faithfulness scores
5. **Performance Analysis**: Compare against baseline and previous runs
6. **Report Generation**: Create detailed evaluation report with actionable insights

## Evaluation Metrics

- **Answer Relevancy**: How well the answer addresses the question (target: >0.85)
- **Context Precision**: Proportion of retrieved content that's relevant (target: >0.80)
- **Context Recall**: Coverage of relevant information (target: >0.90)
- **Faithfulness**: Accuracy without hallucinations (target: >0.95)

## Strategy Options

- `bm25` - Keyword-based retrieval evaluation
- `vector` - Semantic similarity evaluation
- `parent-doc` - Hierarchical retrieval evaluation
- `multi-query` - Query expansion evaluation
- `rerank` - LLM reranking evaluation
- `ensemble` - Combination strategy evaluation
- `all` - Comprehensive evaluation across all strategies

## Expected Output

- **Overall Score**: Aggregate quality metric
- **Metric Breakdown**: Individual RAGAS scores with explanations
- **Performance Comparison**: vs baseline and historical data
- **Quality Trends**: Improvement or regression analysis
- **Recommendations**: Strategy optimization suggestions
- **Artifacts**: JSON report for CI/CD and dashboard integration

## Usage Examples

- `/project:evaluate-rag ensemble` - Evaluate the ensemble strategy
- `/project:evaluate-rag all` - Compare all strategies
- `/project:evaluate-rag vector` - Focus on vector search quality

Use the MCP tool `evaluate_rag` to execute this comprehensive evaluation workflow.