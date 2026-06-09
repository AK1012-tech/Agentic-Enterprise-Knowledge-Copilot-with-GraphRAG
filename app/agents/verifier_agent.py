class VerifierAgent:
    def verify(self, answer: str, contexts: list[dict]) -> bool:
        if not contexts:
            return False
        return "not have enough indexed evidence" not in answer.lower()

