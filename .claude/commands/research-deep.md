# Deep Research with Multi-Strategy RAG

Research the following topic using the DeepAgents multi-strategy RAG system: **$ARGUMENTS**

## Process

1. **Query Analysis**: Analyze the query characteristics to determine optimal retrieval strategy
2. **Strategy Selection**: Choose from available strategies (auto/bm25/vector/parent-doc/multi-query/rerank/ensemble)
3. **Document Retrieval**: Execute retrieval using the selected strategy
4. **Synthesis**: Generate comprehensive answer with proper citations
5. **Quality Evaluation**: Assess result quality using RAGAS metrics
6. **Performance Report**: Report timing, strategy effectiveness, and recommendations

## Expected Output

- **Answer**: Comprehensive response with citations
- **Sources**: List of retrieved documents with metadata
- **Strategy Used**: Which retrieval method was selected and why
- **RAGAS Scores**: Quality metrics (relevancy, precision, recall, faithfulness)
- **Performance**: Timing and token usage statistics
- **Recommendations**: Suggestions for query optimization if needed

## Usage Examples

- `/project:research-deep "What is the difference between vector and keyword search?"`
- `/project:research-deep "How does ensemble retrieval improve accuracy?"`
- `/project:research-deep "Explain parent document retrieval with examples"`

Use the MCP tool `research_deep` to execute this workflow with full DeepAgents orchestration.