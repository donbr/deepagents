"""Dataset management for RAGAS evaluation."""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class GoldenDataset:
    """Golden dataset for evaluation."""

    samples: List[Dict[str, Any]]

    def __len__(self) -> int:
        return len(self.samples)

    def __iter__(self):
        return iter(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


async def load_golden_dataset(
    path: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Load golden dataset for evaluation.

    Args:
        path: Path to dataset file (defaults to golden_set.jsonl)
        limit: Maximum number of samples to load

    Returns:
        List of test samples
    """
    if path is None:
        # Try multiple default locations
        possible_paths = [
            Path(__file__).parent / "golden_set.jsonl",
            Path("integrations/mcp-rag/src/deepagents_mcp_rag/eval/golden_set.jsonl"),
            Path("golden_set.jsonl")
        ]

        for p in possible_paths:
            if p.exists():
                path = p
                break
        else:
            # Return default dataset if file not found
            return _get_default_dataset(limit)

    samples = []

    try:
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))

                if limit and len(samples) >= limit:
                    break

    except FileNotFoundError:
        return _get_default_dataset(limit)

    return samples


def _get_default_dataset(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get default golden dataset for testing.

    Args:
        limit: Maximum number of samples

    Returns:
        Default test dataset
    """
    dataset = [
        {
            "question": "What is the difference between BM25 and vector search?",
            "ground_truth": "BM25 is a keyword-based sparse retrieval method that uses term frequency and inverse document frequency for exact matching, while vector search uses dense embeddings to find semantically similar content through vector similarity calculations.",
            "domain": "information_retrieval"
        },
        {
            "question": "How does parent document retrieval preserve context?",
            "ground_truth": "Parent document retrieval splits documents into small chunks for accurate matching but returns larger parent documents to preserve the full context around the matched content, ensuring comprehensive information is available.",
            "domain": "rag_techniques"
        },
        {
            "question": "What are the benefits of ensemble retrieval?",
            "ground_truth": "Ensemble retrieval combines multiple strategies using techniques like Reciprocal Rank Fusion to achieve better overall performance, leveraging the strengths of different approaches while mitigating individual weaknesses.",
            "domain": "rag_techniques"
        },
        {
            "question": "How does multi-query expansion improve recall?",
            "ground_truth": "Multi-query expansion generates multiple query variations to capture different perspectives and phrasings, improving recall by retrieving documents that might be missed with a single query formulation.",
            "domain": "rag_techniques"
        },
        {
            "question": "What is the role of reranking in retrieval?",
            "ground_truth": "Reranking uses language models to re-order initially retrieved documents based on relevance to the query, improving precision by better understanding the semantic relationship between queries and documents.",
            "domain": "rag_techniques"
        },
        {
            "question": "How do RAGAS metrics evaluate RAG systems?",
            "ground_truth": "RAGAS provides reference-free evaluation through four metrics: answer relevancy (how well answers address questions), context precision (relevance of retrieved documents), context recall (completeness of retrieval), and faithfulness (accuracy without hallucination).",
            "domain": "evaluation"
        },
        {
            "question": "What is the CQRS pattern in MCP?",
            "ground_truth": "CQRS (Command Query Responsibility Segregation) in MCP separates write operations (Tools for full RAG processing) from read operations (Resources for fast document retrieval), optimizing performance by using different models for each pattern.",
            "domain": "architecture"
        },
        {
            "question": "How does DeepAgents implement sub-agent delegation?",
            "ground_truth": "DeepAgents allows creation of specialized sub-agents with specific tools and prompts, enabling task delegation while maintaining context isolation to prevent main agent pollution and improve modularity.",
            "domain": "deepagents"
        },
        {
            "question": "What is the virtual file system in DeepAgents?",
            "ground_truth": "The virtual file system in DeepAgents provides a sandboxed file storage within the agent's state, allowing file operations without accessing the actual file system, ensuring security and enabling persistent workspace across interactions.",
            "domain": "deepagents"
        },
        {
            "question": "How does Reciprocal Rank Fusion work?",
            "ground_truth": "Reciprocal Rank Fusion (RRF) combines rankings from multiple retrieval methods by assigning scores based on reciprocal rank (1/(rank + constant)), summing scores across methods, and reranking by total score to create an optimal combined ranking.",
            "domain": "algorithms"
        },
        {
            "question": "What are the performance characteristics of different retrieval strategies?",
            "ground_truth": "BM25 offers ~5ms latency for exact matching, vector search provides ~20ms for semantic similarity, parent document takes ~50ms for context preservation, multi-query requires ~100ms for coverage, reranking needs ~200ms for precision, and ensemble balances at ~180ms for optimal F1 score.",
            "domain": "performance"
        },
        {
            "question": "How does FastMCP enable MCP server development?",
            "ground_truth": "FastMCP provides a Python framework for rapid MCP server development with decorators for tools and resources, automatic type inference, built-in transport support (stdio/HTTP), and integration with authentication providers.",
            "domain": "mcp"
        },
        {
            "question": "What is the role of embeddings in vector search?",
            "ground_truth": "Embeddings convert text into dense numerical vectors that capture semantic meaning, enabling similarity calculations in high-dimensional space to find conceptually related content even when exact keywords don't match.",
            "domain": "machine_learning"
        },
        {
            "question": "How does caching improve RAG performance?",
            "ground_truth": "Caching in RAG systems operates at multiple levels: embedding cache avoids recomputation, result cache stores query-document pairs, and semantic cache matches similar queries, reducing latency by 70-85% with typical hit rates of 35-45%.",
            "domain": "optimization"
        },
        {
            "question": "What are the security considerations for MCP servers?",
            "ground_truth": "MCP servers require authentication (OAuth/bearer tokens), rate limiting, audit logging, sandboxed execution environments, input validation, and secure transport (HTTPS) to prevent unauthorized access and tool misuse.",
            "domain": "security"
        },
        {
            "question": "How does Claude Code configuration support team collaboration?",
            "ground_truth": "Claude Code uses .mcp.json for project-scoped server configuration with environment variable expansion, .claude/ folder for settings and commands, all version-controlled for team sharing while keeping secrets secure through environment variables.",
            "domain": "claude_code"
        },
        {
            "question": "What is the difference between MCP tools and resources?",
            "ground_truth": "MCP tools implement the command pattern for state-changing operations with full processing (like complete RAG pipelines), while resources implement the query pattern for fast, read-only data access (like raw document retrieval), achieving 3-5x performance improvement.",
            "domain": "mcp"
        },
        {
            "question": "How do you evaluate retrieval quality without ground truth?",
            "ground_truth": "Reference-free evaluation uses techniques like RAGAS that assess answer relevancy through reverse question generation, context precision via relevance scoring, and faithfulness by checking answer support in retrieved documents, all without requiring ground truth annotations.",
            "domain": "evaluation"
        },
        {
            "question": "What are the benefits of hierarchical chunking?",
            "ground_truth": "Hierarchical chunking creates small chunks for precise retrieval while maintaining parent-child relationships, allowing retrieval of small relevant sections but returning larger context windows, balancing retrieval accuracy with context completeness.",
            "domain": "rag_techniques"
        },
        {
            "question": "How does Phoenix provide observability for RAG systems?",
            "ground_truth": "Phoenix offers OpenTelemetry-based tracing for LLM applications, providing embedding analysis, prompt debugging, span visualization across retrieval-synthesis pipelines, and performance metrics with automatic instrumentation for LangChain and other frameworks.",
            "domain": "observability"
        }
    ]

    if limit:
        return dataset[:limit]

    return dataset


async def create_golden_dataset(
    output_path: str,
    num_samples: int = 20,
    domains: Optional[List[str]] = None
) -> None:
    """Create a new golden dataset file.

    Args:
        output_path: Path to save the dataset
        num_samples: Number of samples to generate
        domains: Specific domains to include
    """
    samples = _get_default_dataset(num_samples)

    # Filter by domains if specified
    if domains:
        samples = [s for s in samples if s.get("domain") in domains]

    # Save as JSONL
    with open(output_path, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')

    print(f"Created golden dataset with {len(samples)} samples at {output_path}")