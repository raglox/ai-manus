from typing import Optional
from app.domain.external.llm import LLM
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
import logging

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Web Search tool using Blackbox AI's search capability"""

    name: str = "websearch"
    
    def __init__(self, llm: LLM):
        """Initialize web search tool
        
        Args:
            llm: LLM service (should support blackbox-search model)
        """
        super().__init__()
        self.llm = llm
    
    @tool(
        name="web_search",
        description="Search the web for real-time information using Blackbox AI. Use this when you need current information, news, facts, or data from the internet. Returns search results with source citations.",
        parameters={
            "query": {
                "type": "string",
                "description": "The search query. Be specific and clear about what information you need."
            }
        },
        required=["query"]
    )
    async def web_search(self, query: str) -> ToolResult:
        """Search the web for information
        
        Args:
            query: Search query string
            
        Returns:
            Search results with citations
        """
        try:
            logger.info(f"Performing web search: {query[:100]}")
            
            # Use Blackbox AI's search model with web search capability
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides accurate, up-to-date information from web searches. Always cite your sources."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # Call LLM with blackbox-search model for web search
            # The model will automatically search the web and provide results with citations
            response = await self.llm.chat(
                messages=messages,
                model="blackboxai/blackbox-search",
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract content and citations
            content = response.get("content", "")
            citations = []
            
            # Extract annotations if available
            if "annotations" in response:
                for annotation in response["annotations"]:
                    if annotation.get("type") == "url_citation":
                        url_citation = annotation.get("url_citation", {})
                        citations.append({
                            "url": url_citation.get("url", ""),
                            "title": url_citation.get("title", ""),
                            "excerpt": url_citation.get("content", "")
                        })
            
            # Format result with citations
            result_text = content
            if citations:
                result_text += "\n\n## Sources:\n"
                for i, citation in enumerate(citations, 1):
                    result_text += f"{i}. [{citation['title']}]({citation['url']})\n"
            
            logger.info(f"Web search completed, found {len(citations)} sources")
            
            return ToolResult(
                success=True,
                message=result_text,
                data={
                    "query": query,
                    "content": content,
                    "citations": citations,
                    "source_count": len(citations)
                }
            )
            
        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return ToolResult(
                success=False,
                message=f"Web search failed: {str(e)}",
                data={"query": query, "error": str(e)}
            )