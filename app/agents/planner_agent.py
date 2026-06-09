class PlannerAgent:
    def plan(self, question: str) -> dict[str, bool]:
        graph_terms = {"relationship", "relate", "connected", "depends", "impact", "between"}
        wants_graph = any(term in question.lower() for term in graph_terms)
        return {"use_retrieval": True, "use_graph": wants_graph}

