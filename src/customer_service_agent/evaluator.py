"""
Evaluation and performance monitoring for the customer service agent.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from openai import OpenAI

from .models import EvaluationResult
from .config import AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """Aggregated evaluation metrics."""

    total_interactions: int = 0
    average_score: float = 0.0
    sentiment_trend: float = 0.0
    tool_usage_rate: float = 0.0
    escalation_rate: float = 0.0
    response_time_avg: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_interactions": self.total_interactions,
            "average_score": round(self.average_score, 2),
            "sentiment_trend": round(self.sentiment_trend, 2),
            "tool_usage_rate": round(self.tool_usage_rate, 2),
            "escalation_rate": round(self.escalation_rate, 2),
            "response_time_avg": round(self.response_time_avg, 2),
        }


class PerformanceEvaluator:
    """Evaluates agent performance and generates reports."""

    def __init__(self, config: AgentConfig, openai_client: OpenAI):
        self.config = config
        self.client = openai_client
        self.evaluation_results: List[EvaluationResult] = []

    def evaluate_interaction(
        self,
        user_input: str,
        agent_response: str,
        interaction_id: int,
        tool_used: Optional[str] = None,
        sentiment_score: Optional[float] = None,
        response_time: Optional[float] = None,
    ) -> EvaluationResult:
        """Evaluate a single interaction."""
        try:
            eval_prompt = f"""Evaluate this customer service interaction:

Customer: {user_input}
Agent: {agent_response}

Rate the agent's response on a scale of 1-10 considering:
- Helpfulness and accuracy (0-3 points)
- Professionalism and empathy (0-3 points)  
- Appropriate use of tools (0-2 points)
- Clarity and completeness (0-2 points)

Return JSON with:
- 'score': number from 1-10
- 'reasoning': brief explanation of the score
- 'improvement_suggestions': list of specific suggestions

Be strict but fair in your evaluation."""

            response = self.client.chat.completions.create(
                model=self.config.default_model,
                messages=[{"role": "user", "content": eval_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent evaluation
            )

            eval_data = json.loads(response.choices[0].message.content)

            result = EvaluationResult(
                timestamp=datetime.now().isoformat(),
                interaction_id=interaction_id,
                user_input=user_input,
                agent_response=agent_response,
                score=eval_data.get("score", 0),
                reasoning=eval_data.get("reasoning", "No reasoning provided"),
                tool_used=tool_used,
                sentiment_score=sentiment_score,
                response_time=response_time,
            )

            self.evaluation_results.append(result)
            logger.info(f"Evaluation completed - Score: {result.score}/10")

            return result

        except Exception as e:
            logger.error(f"Error evaluating interaction: {str(e)}")
            # Return a default evaluation result on error
            return EvaluationResult(
                timestamp=datetime.now().isoformat(),
                interaction_id=interaction_id,
                user_input=user_input,
                agent_response=agent_response,
                score=5.0,
                reasoning=f"Evaluation failed: {str(e)}",
                tool_used=tool_used,
                sentiment_score=sentiment_score,
                response_time=response_time,
            )

    def calculate_metrics(self, last_n: Optional[int] = None) -> EvaluationMetrics:
        """Calculate aggregated performance metrics."""
        if not self.evaluation_results:
            return EvaluationMetrics()

        results = self.evaluation_results
        if last_n:
            results = results[-last_n:]

        scores = [r.score for r in results]
        sentiment_scores = [
            r.sentiment_score for r in results if r.sentiment_score is not None
        ]
        tool_uses = [r for r in results if r.tool_used]
        response_times = [
            r.response_time for r in results if r.response_time is not None
        ]

        metrics = EvaluationMetrics(
            total_interactions=len(results),
            average_score=sum(scores) / len(scores) if scores else 0,
            sentiment_trend=(
                sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            ),
            tool_usage_rate=len(tool_uses) / len(results) if results else 0,
            escalation_rate=(
                len([r for r in results if r.tool_used == "escalate_to_human"])
                / len(results)
                if results
                else 0
            ),
            response_time_avg=(
                sum(response_times) / len(response_times) if response_times else 0
            ),
        )

        return metrics

    def generate_performance_report(
        self, last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        metrics = self.calculate_metrics(last_n)

        recent_results = self.evaluation_results
        if last_n:
            recent_results = recent_results[-last_n:]

        # Analyze trends
        if len(recent_results) >= 2:
            first_half = recent_results[: len(recent_results) // 2]
            second_half = recent_results[len(recent_results) // 2 :]

            first_avg = sum(r.score for r in first_half) / len(first_half)
            second_avg = sum(r.score for r in second_half) / len(second_half)
            score_trend = (
                "improving"
                if second_avg > first_avg
                else "declining" if second_avg < first_avg else "stable"
            )
        else:
            score_trend = "insufficient data"

        # Common issues
        low_score_interactions = [
            r for r in recent_results if r.score < self.config.evaluation_threshold
        ]
        common_issues = []
        if low_score_interactions:
            # Simple issue detection based on reasoning
            issue_keywords = {
                "unhelpful": "Lack of helpful information",
                "inaccurate": "Inaccurate information",
                "unprofessional": "Unprofessional tone",
                "confusing": "Unclear response",
                "incomplete": "Incomplete information",
            }

            for keyword, issue in issue_keywords.items():
                if any(keyword in r.reasoning.lower() for r in low_score_interactions):
                    common_issues.append(issue)

        report = {
            "summary": {
                "period": (
                    f"Last {len(recent_results)} interactions"
                    if last_n
                    else "All interactions"
                ),
                "total_evaluated": len(recent_results),
                "overall_performance": self._get_performance_label(
                    metrics.average_score
                ),
                "score_trend": score_trend,
            },
            "metrics": metrics.to_dict(),
            "recent_interactions": [
                {
                    "id": r.interaction_id,
                    "score": r.score,
                    "tool_used": r.tool_used,
                    "user_input_preview": (
                        r.user_input[:50] + "..."
                        if len(r.user_input) > 50
                        else r.user_input
                    ),
                }
                for r in recent_results[-5:]  # Last 5 interactions
            ],
            "recommendations": self._generate_recommendations(metrics, common_issues),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def _get_performance_label(self, score: float) -> str:
        """Convert score to performance label."""
        if score >= 9:
            return "Excellent"
        elif score >= 8:
            return "Very Good"
        elif score >= 7:
            return "Good"
        elif score >= 6:
            return "Satisfactory"
        else:
            return "Needs Improvement"

    def _generate_recommendations(
        self, metrics: EvaluationMetrics, common_issues: List[str]
    ) -> List[str]:
        """Generate recommendations based on metrics and issues."""
        recommendations = []

        if metrics.average_score < self.config.evaluation_threshold:
            recommendations.append("Focus on improving response quality and accuracy")

        if metrics.sentiment_trend < -0.3:
            recommendations.append("Increase emphasis on empathetic responses")

        if metrics.tool_usage_rate < 0.3:
            recommendations.append("Encourage more effective tool usage")

        if metrics.escalation_rate > 0.4:
            recommendations.append(
                "Review escalation criteria - may be escalating too frequently"
            )

        for issue in common_issues:
            recommendations.append(f"Address: {issue}")

        if not recommendations:
            recommendations.append("Maintain current performance standards")

        return recommendations

    def save_evaluation_data(self, filepath: str):
        """Save evaluation results to file."""
        data = {
            "evaluation_results": [r.to_dict() for r in self.evaluation_results],
            "exported_at": datetime.now().isoformat(),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Evaluation data saved to {filepath}")

    def load_evaluation_data(self, filepath: str):
        """Load evaluation results from file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            self.evaluation_results = [
                EvaluationResult.from_dict(r)
                for r in data.get("evaluation_results", [])
            ]

            logger.info(f"Evaluation data loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading evaluation data: {str(e)}")
