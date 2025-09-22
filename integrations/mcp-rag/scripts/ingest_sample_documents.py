#!/usr/bin/env python3
"""Document corpus ingestion pipeline for DeepAgents MCP-RAG testing.

This script creates a sample document corpus to enable full testing of the
retrieval strategies and end-to-end workflows.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_core.documents import Document
from deepagents_mcp_rag.config import get_settings


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "title": "Introduction to Machine Learning",
        "content": """Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. The core idea is to build algorithms that can receive input data and use statistical analysis to predict output values within an acceptable range.

Machine learning algorithms are categorized into three main types:
1. Supervised Learning: Uses labeled training data to learn a mapping function
2. Unsupervised Learning: Finds hidden patterns in data without labeled examples
3. Reinforcement Learning: Learns through interaction with an environment

Common applications include image recognition, natural language processing, recommendation systems, and autonomous vehicles. Popular algorithms include linear regression, decision trees, neural networks, and support vector machines.""",
        "metadata": {
            "category": "AI/ML",
            "difficulty": "beginner",
            "topics": ["machine learning", "artificial intelligence", "algorithms"],
            "author": "AI Education Team",
            "created_at": "2024-01-15"
        }
    },
    {
        "title": "Neural Networks and Deep Learning",
        "content": """Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers that process information using a connectionist approach to computation.

A typical neural network consists of:
- Input Layer: Receives the initial data
- Hidden Layers: Process the data through weighted connections
- Output Layer: Produces the final result

Deep learning refers to neural networks with multiple hidden layers (typically 3 or more). These deep architectures can learn complex patterns and representations from data. Key concepts include:

Backpropagation: The algorithm used to train neural networks by adjusting weights based on errors.
Activation Functions: Functions like ReLU, sigmoid, and tanh that introduce non-linearity.
Gradient Descent: Optimization algorithm that minimizes the loss function.

Applications include computer vision, speech recognition, natural language processing, and game playing AI.""",
        "metadata": {
            "category": "AI/ML",
            "difficulty": "intermediate",
            "topics": ["neural networks", "deep learning", "backpropagation"],
            "author": "Deep Learning Research Team",
            "created_at": "2024-02-20"
        }
    },
    {
        "title": "Model Context Protocol (MCP) Overview",
        "content": """The Model Context Protocol (MCP) is an open protocol that enables AI applications to securely connect to external data sources and tools. MCP provides a standardized way for AI models to access and interact with various systems while maintaining security and privacy.

Key components of MCP:
1. Servers: Provide access to specific resources and tools
2. Clients: AI applications that consume MCP services
3. Transports: Communication mechanisms (stdio, HTTP, WebSocket)
4. Resources: Static or dynamic data sources
5. Tools: Executable functions that can modify state

MCP follows a client-server architecture where:
- Servers expose capabilities through a standardized interface
- Clients can discover and use these capabilities
- Transport layers handle the communication protocol
- Security is built-in with authentication and authorization

Benefits include improved security, standardized interfaces, composability of different services, and easier integration of AI applications with existing systems.""",
        "metadata": {
            "category": "Protocols",
            "difficulty": "intermediate",
            "topics": ["MCP", "protocols", "AI integration", "security"],
            "author": "MCP Working Group",
            "created_at": "2024-03-10"
        }
    },
    {
        "title": "Retrieval-Augmented Generation (RAG)",
        "content": """Retrieval-Augmented Generation (RAG) is a technique that combines the power of large language models with external knowledge retrieval. Instead of relying solely on the model's training data, RAG systems can access and incorporate relevant information from external sources in real-time.

The RAG process involves:
1. Query Processing: Understanding the user's question or request
2. Document Retrieval: Finding relevant documents from a knowledge base
3. Context Assembly: Combining retrieved documents with the original query
4. Generation: Using a language model to generate a response based on the context

Types of retrieval strategies:
- Dense Retrieval: Uses vector embeddings for semantic similarity
- Sparse Retrieval: Uses keyword-based methods like BM25
- Hybrid Retrieval: Combines multiple retrieval approaches
- Multi-hop Retrieval: Performs multiple retrieval steps for complex queries

RAG offers several advantages:
- Access to up-to-date information beyond training data
- Improved factual accuracy and reduced hallucinations
- Transparency through source attribution
- Cost-effective compared to fine-tuning large models

Evaluation metrics for RAG systems include relevance, faithfulness, answer accuracy, and retrieval precision.""",
        "metadata": {
            "category": "AI/ML",
            "difficulty": "advanced",
            "topics": ["RAG", "information retrieval", "language models"],
            "author": "RAG Research Team",
            "created_at": "2024-04-05"
        }
    },
    {
        "title": "Vector Databases and Embeddings",
        "content": """Vector databases are specialized databases designed to store, index, and query high-dimensional vector data efficiently. They play a crucial role in modern AI applications, particularly for similarity search and retrieval-augmented generation systems.

Key concepts:
Vector Embeddings: Dense numerical representations of data (text, images, audio) in high-dimensional space. Similar items have similar vector representations.

Similarity Search: Finding vectors that are closest to a query vector using distance metrics like cosine similarity, Euclidean distance, or dot product.

Indexing Methods:
- HNSW (Hierarchical Navigable Small World): Graph-based indexing for fast approximate search
- IVF (Inverted File): Quantization-based indexing method
- LSH (Locality Sensitive Hashing): Hash-based approximate search

Popular vector databases include:
- Qdrant: Rust-based with rich filtering capabilities
- Pinecone: Managed cloud service with easy scaling
- Weaviate: GraphQL API with hybrid search
- Chroma: Embedded database for experimentation

Applications:
- Semantic search in documents and code
- Recommendation systems
- Image and video similarity search
- Anomaly detection
- Retrieval-augmented generation (RAG) systems

Performance considerations include index building time, query latency, memory usage, and accuracy trade-offs.""",
        "metadata": {
            "category": "Databases",
            "difficulty": "intermediate",
            "topics": ["vector databases", "embeddings", "similarity search"],
            "author": "Vector DB Team",
            "created_at": "2024-05-12"
        }
    },
    {
        "title": "RAGAS Evaluation Framework",
        "content": """RAGAS (Retrieval-Augmented Generation Assessment) is a framework for evaluating RAG systems. It provides metrics to assess different aspects of RAG pipeline performance, helping developers understand and improve their systems.

Core RAGAS Metrics:

1. Answer Relevancy: Measures how relevant the generated answer is to the given question. Uses question generation to create variations and check consistency.

2. Context Precision: Evaluates whether the retrieved context contains information relevant to answering the question. Higher precision means less irrelevant information.

3. Context Recall: Measures whether all relevant information needed to answer the question is present in the retrieved context.

4. Faithfulness: Assesses whether the generated answer is grounded in the provided context. Checks for hallucinations and unsupported claims.

5. Answer Semantic Similarity: Compares the semantic similarity between generated and ground truth answers.

6. Answer Correctness: Evaluates factual accuracy of generated answers against reference answers.

Evaluation Process:
1. Prepare a dataset with questions, contexts, and ground truth answers
2. Run your RAG system to generate answers
3. Apply RAGAS metrics to score the results
4. Analyze scores to identify improvement areas

RAGAS supports both with and without reference evaluation modes, making it flexible for different evaluation scenarios. The framework integrates with popular tools like LangChain and provides detailed scoring explanations.""",
        "metadata": {
            "category": "Evaluation",
            "difficulty": "advanced",
            "topics": ["RAGAS", "evaluation", "RAG assessment", "metrics"],
            "author": "RAGAS Development Team",
            "created_at": "2024-06-18"
        }
    }
]


async def create_documents() -> List[Document]:
    """Create Document objects from sample data."""
    documents = []

    for i, doc_data in enumerate(SAMPLE_DOCUMENTS):
        # Create the main document
        doc = Document(
            page_content=f"# {doc_data['title']}\n\n{doc_data['content']}",
            metadata={
                **doc_data['metadata'],
                "document_id": f"doc_{i+1:03d}",
                "chunk_id": f"doc_{i+1:03d}_chunk_001",
                "source": "sample_corpus",
                "ingestion_timestamp": time.time(),
                "word_count": len(doc_data['content'].split()),
                "char_count": len(doc_data['content'])
            }
        )
        documents.append(doc)

        # Create smaller chunks for parent-document retrieval testing
        content_paragraphs = doc_data['content'].split('\n\n')
        for j, paragraph in enumerate(content_paragraphs):
            if len(paragraph.strip()) > 100:  # Only chunk substantial paragraphs
                chunk_doc = Document(
                    page_content=paragraph.strip(),
                    metadata={
                        **doc_data['metadata'],
                        "document_id": f"doc_{i+1:03d}",
                        "chunk_id": f"doc_{i+1:03d}_chunk_{j+2:03d}",
                        "parent_document_id": f"doc_{i+1:03d}",
                        "source": "sample_corpus",
                        "ingestion_timestamp": time.time(),
                        "word_count": len(paragraph.split()),
                        "char_count": len(paragraph),
                        "chunk_type": "paragraph"
                    }
                )
                documents.append(chunk_doc)

    return documents


async def ingest_to_qdrant(documents: List[Document]) -> None:
    """Ingest documents into Qdrant vector database."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
        from sentence_transformers import SentenceTransformer
        import uuid

        settings = get_settings()

        # Initialize Qdrant client
        client = QdrantClient(url=settings.qdrant_url)
        collection_name = settings.collection_name

        # Initialize embedding model
        model = SentenceTransformer(settings.embed_model)
        vector_size = model.get_sentence_embedding_dimension()

        # Create collection if it doesn't exist
        try:
            client.get_collection(collection_name)
            print(f"Collection '{collection_name}' already exists")
        except Exception:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"Created collection '{collection_name}' with dimension {vector_size}")

        # Generate embeddings and create points
        texts = [doc.page_content for doc in documents]
        embeddings = model.encode(texts, show_progress_bar=True)

        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
            )
            points.append(point)

        # Upload points to Qdrant
        client.upsert(collection_name=collection_name, points=points)
        print(f"Ingested {len(points)} documents into Qdrant")

        # Verify ingestion
        collection_info = client.get_collection(collection_name)
        print(f"Collection status: {collection_info.points_count} points total")

    except Exception as e:
        print(f"❌ Failed to ingest to Qdrant: {e}")
        raise


async def create_golden_dataset() -> None:
    """Create a golden dataset for RAGAS evaluation."""
    golden_dataset = [
        {
            "question": "What are the three main types of machine learning?",
            "ground_truth": "The three main types of machine learning are: 1) Supervised Learning - uses labeled training data to learn a mapping function, 2) Unsupervised Learning - finds hidden patterns in data without labeled examples, and 3) Reinforcement Learning - learns through interaction with an environment.",
            "contexts": ["Machine learning algorithms are categorized into three main types:\n1. Supervised Learning: Uses labeled training data to learn a mapping function\n2. Unsupervised Learning: Finds hidden patterns in data without labeled examples\n3. Reinforcement Learning: Learns through interaction with an environment"],
            "metadata": {
                "category": "basic_concepts",
                "difficulty": "beginner",
                "topics": ["machine learning", "classification"]
            }
        },
        {
            "question": "How does the RAG process work?",
            "ground_truth": "The RAG process involves four main steps: 1) Query Processing - understanding the user's question, 2) Document Retrieval - finding relevant documents from a knowledge base, 3) Context Assembly - combining retrieved documents with the original query, and 4) Generation - using a language model to generate a response based on the context.",
            "contexts": ["The RAG process involves:\n1. Query Processing: Understanding the user's question or request\n2. Document Retrieval: Finding relevant documents from a knowledge base\n3. Context Assembly: Combining retrieved documents with the original query\n4. Generation: Using a language model to generate a response based on the context"],
            "metadata": {
                "category": "rag_concepts",
                "difficulty": "intermediate",
                "topics": ["RAG", "information retrieval"]
            }
        },
        {
            "question": "What are the core RAGAS metrics for evaluation?",
            "ground_truth": "The core RAGAS metrics are: 1) Answer Relevancy - measures how relevant the generated answer is to the question, 2) Context Precision - evaluates whether retrieved context contains relevant information, 3) Context Recall - measures if all relevant information is present, 4) Faithfulness - assesses whether the answer is grounded in the provided context, 5) Answer Semantic Similarity - compares semantic similarity with ground truth, and 6) Answer Correctness - evaluates factual accuracy.",
            "contexts": ["Core RAGAS Metrics:\n\n1. Answer Relevancy: Measures how relevant the generated answer is to the given question\n2. Context Precision: Evaluates whether the retrieved context contains information relevant to answering the question\n3. Context Recall: Measures whether all relevant information needed to answer the question is present\n4. Faithfulness: Assesses whether the generated answer is grounded in the provided context\n5. Answer Semantic Similarity: Compares the semantic similarity between generated and ground truth answers\n6. Answer Correctness: Evaluates factual accuracy of generated answers"],
            "metadata": {
                "category": "evaluation",
                "difficulty": "advanced",
                "topics": ["RAGAS", "metrics", "evaluation"]
            }
        }
    ]

    # Save golden dataset
    output_file = Path(__file__).parent.parent / "src" / "deepagents_mcp_rag" / "eval" / "golden_dataset.json"
    with open(output_file, "w") as f:
        json.dump(golden_dataset, f, indent=2)

    print(f"📊 Created golden dataset with {len(golden_dataset)} entries: {output_file}")


async def verify_ingestion() -> Dict[str, Any]:
    """Verify that document ingestion was successful."""
    verification_results = {}

    try:
        from deepagents_mcp_rag.retrievers.factory import RetrieverFactory

        # Test different retrieval strategies
        strategies = ["bm25", "vector"]
        test_query = "What is machine learning?"

        for strategy in strategies:
            try:
                retriever = RetrieverFactory.create(strategy, k=3)
                start_time = time.time()
                documents = await retriever.retrieve(test_query)
                latency = (time.time() - start_time) * 1000

                verification_results[strategy] = {
                    "status": "✅ Success" if documents else "⚠️ No results",
                    "document_count": len(documents),
                    "latency_ms": round(latency, 2),
                    "sample_content": documents[0].page_content[:100] + "..." if documents else None
                }

            except Exception as e:
                verification_results[strategy] = {
                    "status": "❌ Failed",
                    "error": str(e)
                }

        return verification_results

    except Exception as e:
        return {"error": f"Verification failed: {e}"}


async def main():
    """Main ingestion pipeline."""
    print("=" * 60)
    print("DeepAgents MCP-RAG Document Ingestion Pipeline")
    print("=" * 60)

    # Load settings
    try:
        settings = get_settings()
        print(f"Configuration loaded successfully")
        print(f"Target collection: {settings.collection_name}")
        print(f"Qdrant URL: {settings.qdrant_url}")
        print()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return

    # Create sample documents
    print("1. Creating sample documents...")
    documents = await create_documents()
    print(f"   Created {len(documents)} documents and chunks")

    # Ingest to Qdrant
    print("\n2. Ingesting documents to Qdrant...")
    try:
        await ingest_to_qdrant(documents)
        print("   ✅ Qdrant ingestion completed")
    except Exception as e:
        print(f"   ❌ Qdrant ingestion failed: {e}")
        return

    # Create golden dataset
    print("\n3. Creating golden dataset for evaluation...")
    try:
        await create_golden_dataset()
        print("   ✅ Golden dataset created")
    except Exception as e:
        print(f"   ❌ Golden dataset creation failed: {e}")

    # Verify ingestion
    print("\n4. Verifying document retrieval...")
    verification_results = await verify_ingestion()

    for strategy, result in verification_results.items():
        print(f"   {strategy}: {result.get('status', 'Unknown')}")
        if 'document_count' in result:
            print(f"      Documents: {result['document_count']}, Latency: {result['latency_ms']}ms")

    print("\n" + "=" * 60)
    print("✅ Document ingestion pipeline completed!")
    print()
    print("Next steps:")
    print("   1. Run test suite: pytest tests/ -v")
    print("   2. Test MCP server: python -m deepagents_mcp_rag.mcp.server")
    print("   3. Run performance benchmark: python scripts/performance_baseline.py")


if __name__ == "__main__":
    asyncio.run(main())