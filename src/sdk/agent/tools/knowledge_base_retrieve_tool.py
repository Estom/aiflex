"""
Knowledge Base Retrieve Tool - 知识库检索工具

从 RagFlow 知识库检索相关内容
"""

from typing import Any

from ..core.interfaces import AgentContext, Tool, ToolDefinition
from ...integration.ragflow_client import RagFlowClient, RetrieveChunksRequest


type KnowledgeBaseRetrieveOptions = dict[str, Any]


class KnowledgeBaseRetrieveTool(Tool):
    """
    知识库检索工具

    从配置的 RagFlow 知识库中检索相关内容
    """

    def __init__(self, options: KnowledgeBaseRetrieveOptions, ragflow: RagFlowClient):
        self._options = options
        self._ragflow = ragflow

    @property
    def name(self) -> str:
        return "knowledge_base_retrieve"

    @property
    def description(self) -> str:
        return "Retrieve relevant knowledge chunks from the configured RagFlow knowledge bases linked to this agent. Provide a query string."

    @property
    def display_name(self) -> str:
        return "Knowledge Base Retrieve"

    def get_definition(self) -> ToolDefinition:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query / question for retrieving knowledge chunks.",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(self, input: Any, context: AgentContext | None = None) -> str:
        """执行检索"""
        payload = self._parse(input)

        dataset_ids = self._options.get("datasetIds", [])
        if not dataset_ids:
            return "No knowledge bases are linked to this agent."

        retrieval = self._options.get("retrieval", {})
        similarity_threshold = retrieval.get("similarityThreshold", 0.2)
        vector_similarity_weight = retrieval.get("vectorSimilarityWeight", 0.3)
        recall_count = retrieval.get("recallCount", 5)
        top_k = retrieval.get("topK", 5)

        result = await self._ragflow.retrieve_chunks(
            RetrieveChunksRequest(
                question=payload["query"],
                dataset_ids=dataset_ids,
                page=1,
                page_size=min(100, max(1, recall_count)),
                similarity_threshold=similarity_threshold,
                vector_similarity_weight=vector_similarity_weight,
                top_k=top_k,
            ),
        )

        if not result.get("chunks"):
            return "No relevant knowledge chunks found."

        lines = []
        for idx, chunk in enumerate(result["chunks"][:20]):
            score = f"similarity: {chunk.get('similarity', 0):.3f}" if chunk.get("similarity") else None
            doc = chunk.get("document_id")
            header = f"#{idx + 1}"
            if doc:
                header += f" | doc: {doc}"
            if score:
                header += f" | {score}"

            lines.append(f"{header}\n{chunk['content']}")

        return "\n\n".join(lines)

    def _parse(self, input: Any) -> dict:
        """解析输入"""
        if isinstance(input, str):
            query = input.strip()
            if not query:
                raise ValueError("query is required")
            return {"query": query}

        if isinstance(input, dict):
            query = input.get("query", "").strip() if isinstance(input.get("query"), str) else ""
            if not query:
                raise ValueError("query is required")
            return {"query": query}

        raise ValueError("Input must be a string or object with query field")
