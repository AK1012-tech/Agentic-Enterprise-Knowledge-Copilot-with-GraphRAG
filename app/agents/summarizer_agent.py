class SummarizerAgent:
    def build_prompt(self, question: str, contexts: list[dict], graph_context: list[dict]) -> str:
        context_text = "\n\n".join(
            f"[{index}] {chunk['source']} :: {chunk['text']}" for index, chunk in enumerate(contexts, start=1)
        )
        graph_text = "\n".join(
            f"{edge['source']} -{edge['relation']}-> {edge['target']}" for edge in graph_context
        )
        return (
            "Context:\n"
            f"{context_text or 'No retrieved context.'}\n\n"
            "Graph Context:\n"
            f"{graph_text or 'No graph context.'}\n\n"
            f"Question: {question}\n"
            "Answer with grounded citations using [1], [2], etc."
        )

