import json
import logging

logger = logging.getLogger(__name__)


class VerifierAgent:
    """
    Intelligent verification agent that uses LLM to validate answer grounding.
    
    Checks that:
    - Answer is supported by provided contexts
    - Answer doesn't make unsupported claims
    - Evidence is directly relevant to the question
    - No hallucinations or speculation
    """

    def __init__(self, llm=None):
        """
        Initialize verifier with optional LLM for intelligent validation.
        
        Args:
            llm: OpenAIClient instance for grounding verification (optional for fallback mode)
        """
        self.llm = llm

    def verify(self, answer: str, contexts: list[dict]) -> bool:
        """
        Verify that the answer is grounded in the provided contexts.
        
        Uses LLM-based grounding verification if available, falls back to simple checks.
        
        Args:
            answer: Generated answer from LLM
            contexts: List of context chunks used for retrieval
            
        Returns:
            bool indicating if answer is properly grounded
        """
        # If no contexts provided, answer cannot be grounded
        if not contexts:
            logger.info("[VERIFIER] No contexts provided - answer cannot be grounded")
            return False

        # Check for explicit "no evidence" statements
        if self._has_explicit_no_evidence(answer):
            logger.info("[VERIFIER] Answer explicitly states insufficient evidence")
            return False

        # Use LLM-based verification if available
        if self.llm:
            return self._llm_based_verification(answer, contexts)
        else:
            return self._simple_verification(answer, contexts)

    def _llm_based_verification(self, answer: str, contexts: list[dict]) -> bool:
        """
        Use LLM to verify answer is grounded in contexts.
        """
        try:
            # Prepare context summary
            context_text = "\n\n".join(
                f"[{i}] {chunk.get('source', 'Unknown')}: {chunk.get('text', '')[:500]}"
                for i, chunk in enumerate(contexts[:5], 1)  # Limit to first 5
            )

            prompt = f"""Verify if this answer is grounded in the provided context.

CONTEXT:
{context_text}

ANSWER:
"{answer}"

Analyze:
1. Is the answer directly supported by the context? 
2. Are there any unsupported claims or hallucinations?
3. Does the answer stay within the scope of provided evidence?

Respond with ONLY valid JSON:
{{"grounded": true/false, "confidence": 0.0-1.0, "issues": "string describing any issues or empty string"}}

Be strict: answer must be clearly supported by context, not just related."""

            response = self.llm.complete(
                system="You are a fact-checking AI. Verify answers against context. Respond with only valid JSON.",
                prompt=prompt,
            )

            result = json.loads(response.strip())
            grounded = result.get("grounded", False)
            confidence = result.get("confidence", 0.0)

            logger.info(
                f"[VERIFIER] LLM verification: grounded={grounded}, "
                f"confidence={confidence}, issues={result.get('issues', 'none')}"
            )

            # Require high confidence for verification
            return grounded and confidence >= 0.7

        except (json.JSONDecodeError, KeyError, Exception) as e:
            logger.warning(f"[VERIFIER] LLM verification failed ({e}), falling back to simple check")
            return self._simple_verification(answer, contexts)

    def _simple_verification(self, answer: str, contexts: list[dict]) -> bool:
        """
        Simple fallback verification: check if answer references context.
        """
        if not contexts:
            return False

        # Check if answer is too generic or empty
        answer_lower = answer.lower().strip()
        if len(answer_lower) < 20:
            logger.info("[VERIFIER] Answer too short to be grounded")
            return False

        # Check if answer contains any content from contexts
        context_snippets = []
        for chunk in contexts:
            text = chunk.get("text", "").lower()
            if len(text) > 10:
                # Extract meaningful snippets (words, not single chars)
                words = [w for w in text.split() if len(w) > 3]
                context_snippets.extend(words[:10])  # Take first 10 meaningful words

        # Check if answer contains at least some context words
        answer_words = set(w.lower() for w in answer_lower.split() if len(w) > 3)
        context_word_set = set(context_snippets)
        overlap = answer_words.intersection(context_word_set)

        is_grounded = len(overlap) >= 3  # At least 3 content words match

        logger.info(
            f"[VERIFIER] Simple verification: {len(overlap)} context word matches "
            f"(need 3+) - grounded={is_grounded}"
        )

        return is_grounded

    def _has_explicit_no_evidence(self, answer: str) -> bool:
        """
        Check if answer explicitly states insufficient evidence.
        """
        no_evidence_markers = [
            "not have enough indexed evidence",
            "insufficient evidence",
            "no relevant information",
            "not found in the provided",
            "cannot find",
            "i do not have",
            "no indexed content",
        ]
        answer_lower = answer.lower()
        return any(marker in answer_lower for marker in no_evidence_markers)

