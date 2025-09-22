"""RAGAS evaluation harness for comprehensive RAG system assessment."""

import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

from .metrics import calculate_ragas_metrics, batch_calculate_ragas_metrics, RAGASResults
from .dataset import GoldenDataset, load_golden_dataset
from ..retrievers.factory import RetrieverFactory
from ..utils.logging import get_logger


class RAGASEvaluator:
    """Comprehensive RAGAS evaluation harness for retrieval strategies."""

    def __init__(
        self,
        strategy: str = "ensemble",
        output_dir: Optional[str] = None
    ):
        """Initialize RAGAS evaluator.

        Args:
            strategy: Retrieval strategy to evaluate
            output_dir: Directory for evaluation outputs
        """
        self.strategy = strategy
        self.output_dir = Path(output_dir) if output_dir else Path("eval_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

    async def evaluate_dataset(
        self,
        dataset: List[Dict[str, Any]],
        save_results: bool = True
    ) -> Dict[str, Any]:
        """Evaluate a dataset using RAGAS metrics.

        Args:
            dataset: List of test cases with questions and optional ground truth
            save_results: Whether to save results to disk

        Returns:
            Comprehensive evaluation results
        """
        self.logger.info(f"Starting RAGAS evaluation with {len(dataset)} samples")
        start_time = time.time()

        # Create retriever for the strategy
        retriever = RetrieverFactory.create(self.strategy, k=5)

        # Process each sample
        evaluation_samples = []

        for i, sample in enumerate(dataset):
            try:
                # Retrieve documents
                question = sample["question"]
                self.logger.info(f"Processing sample {i+1}/{len(dataset)}: {question[:50]}...")

                documents = await retriever.retrieve(question)

                # Generate answer (simplified for evaluation)
                contexts = [doc.page_content for doc in documents]
                answer = await self._generate_answer(question, contexts)

                evaluation_samples.append({
                    "question": question,
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": sample.get("ground_truth"),
                    "metadata": {
                        "strategy": self.strategy,
                        "num_documents": len(documents),
                        "retrieval_time": documents[0].metadata.get("latency_ms", 0) if documents else 0
                    }
                })

            except Exception as e:
                self.logger.error(f"Error processing sample {i}: {e}")
                evaluation_samples.append({
                    "question": sample["question"],
                    "answer": "Error during retrieval",
                    "contexts": [],
                    "error": str(e)
                })

        # Calculate RAGAS metrics
        results = await batch_calculate_ragas_metrics(evaluation_samples)

        # Add metadata
        results["metadata"] = {
            "strategy": self.strategy,
            "dataset_size": len(dataset),
            "evaluation_time_seconds": time.time() - start_time,
            "timestamp": time.time()
        }

        # Calculate strategy-specific insights
        results["insights"] = self._generate_insights(results)

        # Save results if requested
        if save_results:
            await self._save_results(results)

        self.logger.info(f"Evaluation completed in {time.time() - start_time:.2f}s")
        self.logger.info(f"Overall score: {results['aggregate_scores']['overall_score']:.3f}")

        return results

    async def _generate_answer(self, question: str, contexts: List[str]) -> str:
        """Generate an answer from retrieved contexts.

        Args:
            question: Question to answer
            contexts: Retrieved contexts

        Returns:
            Generated answer
        """
        if not contexts:
            return "No relevant information found."

        from ..utils.llm import get_llm

        llm = get_llm()

        # Create prompt
        context_text = "\n\n".join([
            f"Document {i+1}: {context[:500]}..."
            for i, context in enumerate(contexts[:3])
        ])

        prompt = f"""Answer this question based on the retrieved documents:

Question: {question}

Retrieved Documents:
{context_text}

Provide a clear, concise answer based only on the information in the documents."""

        try:
            response = await llm.ainvoke(prompt)
            return response.content

        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return "Error generating answer from contexts."

    def _generate_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from evaluation results.

        Args:
            results: Evaluation results

        Returns:
            Strategic insights and recommendations
        """
        scores = results.get("aggregate_scores", {})
        insights = {
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }

        # Analyze strengths
        if scores.get("answer_relevancy", 0) > 0.85:
            insights["strengths"].append("Excellent answer relevancy")
        if scores.get("context_precision", 0) > 0.80:
            insights["strengths"].append("High precision in document retrieval")
        if scores.get("faithfulness", 0) > 0.90:
            insights["strengths"].append("Minimal hallucination, high faithfulness")

        # Identify weaknesses
        if scores.get("answer_relevancy", 0) < 0.70:
            insights["weaknesses"].append("Low answer relevancy")
            insights["recommendations"].append("Consider refining query processing")

        if scores.get("context_precision", 0) < 0.65:
            insights["weaknesses"].append("Poor context precision")
            insights["recommendations"].append("Improve retrieval strategy or filtering")

        if scores.get("context_recall", 0) < 0.70:
            insights["weaknesses"].append("Insufficient context recall")
            insights["recommendations"].append("Increase retrieval count or use multi-query")

        if scores.get("faithfulness", 0) < 0.80:
            insights["weaknesses"].append("Faithfulness issues detected")
            insights["recommendations"].append("Strengthen answer grounding in contexts")

        # Strategy-specific insights
        insights["strategy_analysis"] = self._analyze_strategy_performance(scores)

        return insights

    def _analyze_strategy_performance(self, scores: Dict[str, float]) -> Dict[str, Any]:
        """Analyze performance specific to the strategy.

        Args:
            scores: Aggregate scores

        Returns:
            Strategy-specific analysis
        """
        overall = scores.get("overall_score", 0)

        if self.strategy == "bm25":
            return {
                "type": "Keyword-based",
                "suitable_for": "Exact term matching, technical queries",
                "performance": "Good" if overall > 0.75 else "Needs improvement",
                "suggestion": "Consider hybrid approach for semantic queries"
            }

        elif self.strategy == "vector":
            return {
                "type": "Semantic similarity",
                "suitable_for": "Conceptual understanding, related topics",
                "performance": "Excellent" if overall > 0.85 else "Good",
                "suggestion": "Add BM25 for exact term requirements"
            }

        elif self.strategy == "ensemble":
            return {
                "type": "Multi-strategy fusion",
                "suitable_for": "General purpose, balanced performance",
                "performance": "Optimal" if overall > 0.80 else "Good",
                "suggestion": "Fine-tune strategy weights for specific domains"
            }

        else:
            return {
                "type": self.strategy,
                "performance": "Good" if overall > 0.75 else "Needs analysis",
                "suggestion": "Compare with ensemble for baseline"
            }

    async def _save_results(self, results: Dict[str, Any]) -> None:
        """Save evaluation results to disk.

        Args:
            results: Evaluation results to save
        """
        timestamp = int(time.time())
        filename = self.output_dir / f"ragas_eval_{self.strategy}_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            self.logger.info(f"Results saved to {filename}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

    async def compare_strategies(
        self,
        strategies: List[str],
        dataset: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare multiple strategies using RAGAS evaluation.

        Args:
            strategies: List of strategies to compare
            dataset: Test dataset

        Returns:
            Comparative analysis of strategies
        """
        self.logger.info(f"Comparing {len(strategies)} strategies")

        comparison_results = {
            "strategies": strategies,
            "dataset_size": len(dataset),
            "strategy_results": {},
            "rankings": {}
        }

        # Evaluate each strategy
        for strategy in strategies:
            self.logger.info(f"Evaluating strategy: {strategy}")

            evaluator = RAGASEvaluator(strategy=strategy, output_dir=self.output_dir)
            results = await evaluator.evaluate_dataset(dataset, save_results=False)

            comparison_results["strategy_results"][strategy] = {
                "scores": results["aggregate_scores"],
                "insights": results.get("insights", {})
            }

        # Generate rankings
        comparison_results["rankings"] = self._rank_strategies(
            comparison_results["strategy_results"]
        )

        # Generate recommendations
        comparison_results["recommendations"] = self._generate_comparison_recommendations(
            comparison_results["strategy_results"],
            comparison_results["rankings"]
        )

        # Save comparison results
        timestamp = int(time.time())
        filename = self.output_dir / f"strategy_comparison_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)

        self.logger.info(f"Comparison results saved to {filename}")

        return comparison_results

    def _rank_strategies(
        self,
        strategy_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Rank strategies by different metrics.

        Args:
            strategy_results: Results for each strategy

        Returns:
            Rankings by metric
        """
        rankings = {}

        # Metrics to rank by
        metrics = ["overall_score", "answer_relevancy", "context_precision", "faithfulness"]

        for metric in metrics:
            # Sort strategies by metric score
            sorted_strategies = sorted(
                strategy_results.items(),
                key=lambda x: x[1]["scores"].get(metric, 0),
                reverse=True
            )

            rankings[metric] = [
                {
                    "strategy": strategy,
                    "score": results["scores"].get(metric, 0)
                }
                for strategy, results in sorted_strategies
            ]

        return rankings

    def _generate_comparison_recommendations(
        self,
        strategy_results: Dict[str, Dict[str, Any]],
        rankings: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Generate recommendations from strategy comparison.

        Args:
            strategy_results: Results for each strategy
            rankings: Strategy rankings

        Returns:
            Recommendations for strategy selection
        """
        # Get best overall strategy
        best_overall = rankings["overall_score"][0]["strategy"]
        best_score = rankings["overall_score"][0]["score"]

        recommendations = {
            "best_overall": best_overall,
            "best_overall_score": best_score,
            "use_cases": {}
        }

        # Recommend strategies for different use cases
        if rankings["context_precision"][0]["score"] > 0.85:
            recommendations["use_cases"]["high_precision"] = rankings["context_precision"][0]["strategy"]

        if rankings["answer_relevancy"][0]["score"] > 0.90:
            recommendations["use_cases"]["best_relevancy"] = rankings["answer_relevancy"][0]["strategy"]

        if rankings["faithfulness"][0]["score"] > 0.95:
            recommendations["use_cases"]["minimal_hallucination"] = rankings["faithfulness"][0]["strategy"]

        # General recommendation
        if best_score > 0.85:
            recommendations["general"] = f"Use {best_overall} for excellent overall performance"
        elif best_score > 0.75:
            recommendations["general"] = f"{best_overall} provides good performance, consider ensemble for improvement"
        else:
            recommendations["general"] = "Consider combining strategies or refining retrieval parameters"

        return recommendations


async def evaluate_retrieval_strategy(
    strategy: str,
    num_samples: int = 10
) -> Dict[str, Any]:
    """Quick evaluation of a retrieval strategy.

    Args:
        strategy: Strategy to evaluate
        num_samples: Number of samples to test

    Returns:
        Evaluation results
    """
    evaluator = RAGASEvaluator(strategy=strategy)
    dataset = await load_golden_dataset(limit=num_samples)
    return await evaluator.evaluate_dataset(dataset)