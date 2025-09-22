"""RAGAS metrics implementation for RAG evaluation."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from ..utils.llm import get_llm_for_evaluation
from ..utils.logging import get_logger


@dataclass
class RAGASResults:
    """Container for RAGAS evaluation results."""

    answer_relevancy: float
    context_precision: float
    context_recall: float
    faithfulness: float
    overall_score: float

    def to_dict(self) -> Dict[str, float]:
        """Convert results to dictionary."""
        return {
            "answer_relevancy": self.answer_relevancy,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "faithfulness": self.faithfulness,
            "overall_score": self.overall_score
        }

    def __str__(self) -> str:
        """String representation of results."""
        return (
            f"RAGAS Results:\n"
            f"  Answer Relevancy: {self.answer_relevancy:.3f}\n"
            f"  Context Precision: {self.context_precision:.3f}\n"
            f"  Context Recall: {self.context_recall:.3f}\n"
            f"  Faithfulness: {self.faithfulness:.3f}\n"
            f"  Overall Score: {self.overall_score:.3f}"
        )


async def calculate_ragas_metrics(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate RAGAS metrics for a RAG response.

    Args:
        question: Original question
        answer: Generated answer
        contexts: Retrieved contexts used for answer
        ground_truth: Optional ground truth answer

    Returns:
        Dictionary with RAGAS metric scores
    """
    logger = get_logger(__name__)

    try:
        # Try to use actual RAGAS library if available
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness
        )

        # Prepare data for RAGAS
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts]
        }

        if ground_truth:
            data["ground_truth"] = [ground_truth]

        # Run RAGAS evaluation
        result = evaluate(
            dataset=data,
            metrics=[answer_relevancy, context_precision, context_recall, faithfulness]
        )

        return result.to_dict()

    except ImportError:
        logger.info("RAGAS not available, using LLM-based evaluation")
        return await _llm_based_ragas_evaluation(question, answer, contexts, ground_truth)


async def _llm_based_ragas_evaluation(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> Dict[str, Any]:
    """LLM-based RAGAS metric calculation when library is not available.

    Args:
        question: Original question
        answer: Generated answer
        contexts: Retrieved contexts
        ground_truth: Optional ground truth

    Returns:
        Estimated RAGAS metrics
    """
    logger = get_logger(__name__)
    llm = get_llm_for_evaluation()

    # Calculate each metric using LLM
    relevancy = await _calculate_answer_relevancy(llm, question, answer)
    precision = await _calculate_context_precision(llm, question, contexts)
    recall = await _calculate_context_recall(llm, question, answer, contexts, ground_truth)
    faithfulness = await _calculate_faithfulness(llm, answer, contexts)

    # Calculate overall score
    overall = (relevancy + precision + recall + faithfulness) / 4.0

    results = RAGASResults(
        answer_relevancy=relevancy,
        context_precision=precision,
        context_recall=recall,
        faithfulness=faithfulness,
        overall_score=overall
    )

    logger.info(f"RAGAS evaluation completed: {results}")

    return results.to_dict()


async def _calculate_answer_relevancy(llm, question: str, answer: str) -> float:
    """Calculate answer relevancy score.

    Args:
        llm: Language model
        question: Original question
        answer: Generated answer

    Returns:
        Relevancy score (0.0 to 1.0)
    """
    prompt = f"""Evaluate how relevant this answer is to the question.

Question: {question}

Answer: {answer}

Rate the relevancy on a scale of 0.0 to 1.0 where:
- 1.0 = Perfectly relevant, directly answers the question
- 0.8-0.9 = Highly relevant with minor omissions
- 0.6-0.7 = Somewhat relevant but missing key aspects
- <0.6 = Poor relevance or off-topic

Provide only a decimal number between 0.0 and 1.0."""

    try:
        response = await llm.ainvoke(prompt)
        score_text = response.content.strip()

        # Extract numeric score
        score = float(score_text.split()[0].replace(',', '.'))
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error calculating answer relevancy: {e}")
        return 0.5  # Default middle score on error


async def _calculate_context_precision(llm, question: str, contexts: List[str]) -> float:
    """Calculate context precision score.

    Args:
        llm: Language model
        question: Original question
        contexts: Retrieved contexts

    Returns:
        Precision score (0.0 to 1.0)
    """
    context_text = "\n\n".join([f"Context {i+1}: {c[:500]}" for i, c in enumerate(contexts[:5])])

    prompt = f"""Evaluate the precision of retrieved contexts for answering this question.

Question: {question}

Retrieved Contexts:
{context_text}

Rate the precision on a scale of 0.0 to 1.0 where:
- 1.0 = All contexts are highly relevant
- 0.8-0.9 = Most contexts are relevant with minor irrelevant parts
- 0.6-0.7 = Mixed relevance
- <0.6 = Mostly irrelevant contexts

Consider what proportion of the retrieved information is actually useful for answering the question.

Provide only a decimal number between 0.0 and 1.0."""

    try:
        response = await llm.ainvoke(prompt)
        score_text = response.content.strip()
        score = float(score_text.split()[0].replace(',', '.'))
        return min(max(score, 0.0), 1.0)

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error calculating context precision: {e}")
        return 0.5


async def _calculate_context_recall(
    llm,
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> float:
    """Calculate context recall score.

    Args:
        llm: Language model
        question: Original question
        answer: Generated answer
        contexts: Retrieved contexts
        ground_truth: Optional ground truth

    Returns:
        Recall score (0.0 to 1.0)
    """
    context_text = "\n\n".join([f"Context {i+1}: {c[:500]}" for i, c in enumerate(contexts[:5])])

    if ground_truth:
        reference = ground_truth
    else:
        reference = answer

    prompt = f"""Evaluate whether the retrieved contexts contain all necessary information.

Question: {question}

Expected Information (from answer): {reference}

Retrieved Contexts:
{context_text}

Rate the recall on a scale of 0.0 to 1.0 where:
- 1.0 = All necessary information is present in contexts
- 0.8-0.9 = Most necessary information is present
- 0.6-0.7 = Some key information is missing
- <0.6 = Major information gaps

Provide only a decimal number between 0.0 and 1.0."""

    try:
        response = await llm.ainvoke(prompt)
        score_text = response.content.strip()
        score = float(score_text.split()[0].replace(',', '.'))
        return min(max(score, 0.0), 1.0)

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error calculating context recall: {e}")
        return 0.5


async def _calculate_faithfulness(llm, answer: str, contexts: List[str]) -> float:
    """Calculate faithfulness score.

    Args:
        llm: Language model
        answer: Generated answer
        contexts: Retrieved contexts

    Returns:
        Faithfulness score (0.0 to 1.0)
    """
    context_text = "\n\n".join([f"Context {i+1}: {c[:500]}" for i, c in enumerate(contexts[:5])])

    prompt = f"""Evaluate the faithfulness of this answer to the provided contexts.

Answer: {answer}

Source Contexts:
{context_text}

Rate the faithfulness on a scale of 0.0 to 1.0 where:
- 1.0 = All statements in answer are directly supported by contexts
- 0.8-0.9 = Most statements are supported with minor unsupported details
- 0.6-0.7 = Some unsupported statements or mild hallucinations
- <0.6 = Significant hallucinations or unsupported claims

Focus on whether the answer invents information not present in the contexts.

Provide only a decimal number between 0.0 and 1.0."""

    try:
        response = await llm.ainvoke(prompt)
        score_text = response.content.strip()
        score = float(score_text.split()[0].replace(',', '.'))
        return min(max(score, 0.0), 1.0)

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Error calculating faithfulness: {e}")
        return 0.5


async def batch_calculate_ragas_metrics(
    samples: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate RAGAS metrics for multiple samples.

    Args:
        samples: List of samples with question, answer, contexts

    Returns:
        Aggregated metrics and per-sample scores
    """
    logger = get_logger(__name__)

    all_scores = []
    failed_samples = []

    for i, sample in enumerate(samples):
        try:
            scores = await calculate_ragas_metrics(
                question=sample["question"],
                answer=sample["answer"],
                contexts=sample["contexts"],
                ground_truth=sample.get("ground_truth")
            )
            all_scores.append(scores)

        except Exception as e:
            logger.error(f"Failed to evaluate sample {i}: {e}")
            failed_samples.append(i)

    if not all_scores:
        return {"error": "All samples failed evaluation"}

    # Calculate aggregate metrics
    avg_relevancy = sum(s["answer_relevancy"] for s in all_scores) / len(all_scores)
    avg_precision = sum(s["context_precision"] for s in all_scores) / len(all_scores)
    avg_recall = sum(s["context_recall"] for s in all_scores) / len(all_scores)
    avg_faithfulness = sum(s["faithfulness"] for s in all_scores) / len(all_scores)
    avg_overall = sum(s["overall_score"] for s in all_scores) / len(all_scores)

    return {
        "num_samples": len(samples),
        "num_successful": len(all_scores),
        "num_failed": len(failed_samples),
        "aggregate_scores": {
            "answer_relevancy": avg_relevancy,
            "context_precision": avg_precision,
            "context_recall": avg_recall,
            "faithfulness": avg_faithfulness,
            "overall_score": avg_overall
        },
        "per_sample_scores": all_scores,
        "failed_samples": failed_samples
    }