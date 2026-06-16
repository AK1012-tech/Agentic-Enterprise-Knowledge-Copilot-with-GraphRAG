import json
import logging

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Intelligent planning agent that uses LLM reasoning to decide retrieval strategy.
    
    Uses semantic understanding to determine whether to:
    - Use document retrieval (for factual lookup questions)
    - Use graph retrieval (for relationship/dependency questions)
    - Use both (for complex questions requiring both evidence and context)
    """

    def __init__(self, llm=None):
        """
        Initialize planner with optional LLM for intelligent routing.
        
        Args:
            llm: OpenAIClient instance for LLM-based reasoning (optional for fallback mode)
        """
        self.llm = llm
        self.keyword_fallback = {
            "relationship": True,
            "relate": True,
            "connected": True,
            "depends": True,
            "dependency": True,
            "impact": True,
            "influence": True,
            "between": True,
            "how": True,
            "why": True,
            "association": True,
            "linked": True,
        }

    def plan(self, question: str) -> dict[str, bool]:
        """
        Determine optimal retrieval strategy for the question.
        
        Uses LLM-based reasoning if available, falls back to keyword matching.
        
        Args:
            question: User's question
            
        Returns:
            dict with "use_retrieval" and "use_graph" boolean flags
        """
        if self.llm:
            return self._llm_based_plan(question)
        else:
            return self._keyword_based_fallback(question)

    def _llm_based_plan(self, question: str) -> dict[str, bool]:
        """
        Use LLM to intelligently analyze the question and determine strategy.
        """
        try:
            prompt = f"""Analyze this question and determine what retrieval strategy is needed.

Question: "{question}"

Decide based on:
1. "use_retrieval": Does this question ask for factual information, data, policies, or specific knowledge? (yes/no)
2. "use_graph": Does this question ask about relationships, dependencies, impacts, connections, or how things are related? (yes/no)

Respond with ONLY valid JSON, no markdown or extra text:
{{"use_retrieval": true/false, "use_graph": true/false}}"""

            response = self.llm.complete(
                system="You are a query analyzer. Respond with only valid JSON.",
                prompt=prompt,
            )

            # Parse JSON response
            result = json.loads(response.strip())
            
            # Ensure at least one strategy is selected
            if not result.get("use_retrieval") and not result.get("use_graph"):
                result["use_retrieval"] = True
            
            logger.info(
                f"[PLANNER] LLM-based plan: use_retrieval={result['use_retrieval']}, "
                f"use_graph={result['use_graph']}"
            )
            return result

        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.warning(f"[PLANNER] LLM planning failed ({e}), falling back to keyword matching")
            return self._keyword_based_fallback(question)

    def _keyword_based_fallback(self, question: str) -> dict[str, bool]:
        """
        Fallback keyword-based routing when LLM is unavailable.
        """
        question_lower = question.lower()
        wants_graph = any(term in question_lower for term in self.keyword_fallback.keys())
        return {"use_retrieval": True, "use_graph": wants_graph}

