"""Document Retrieval Agent - Fetches old documents"""

from typing import Any, Callable
from agent_framework import AgentRunResponse, AgentThread, ChatMessage, Role, TextContent
from agents.kyc_base_agent import KYCBaseAgent
from tools.kyc_tools import query_kyc_database


class DocumentRetrievalAgent(KYCBaseAgent):
    """Fetches old documents - Routes based on what's found"""
    
    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tools: list[Callable] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Document Retrieval Agent.
        
        Args:
            name: The name of the agent.
            description: The description of the agent.
            tools: List of function tools available to this agent.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            name=name or "Document Retrieval",
            description=description or "Retrieves existing KYC data from database",
            **kwargs,
        )
        # Agent-level tools (default includes database query tool)
        self.agent_tools = tools or [query_kyc_database]
    
    async def run(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        tools: list[Callable] | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        """Execute the agent and return a complete response.
        
        Args:
            messages: The message(s) to process (optional, uses memory).
            thread: The conversation thread (optional).
            tools: Run-level tools (combined with agent-level tools).
            **kwargs: Additional keyword arguments.
        
        Returns:
            An AgentRunResponse containing retrieval results and routing decision.
        """
        # Get customer_id from memory
        customer_id = self.get_memory('customer_id') or 'UNKNOWN'
        intent = self.get_memory('intent')
        
        # Combine agent-level and run-level tools (run-level takes precedence)
        available_tools = {**{tool.__name__: tool for tool in self.agent_tools}}
        if tools:
            available_tools.update({tool.__name__: tool for tool in tools})
        
        # Use database query tool
        db_tool = available_tools.get('query_kyc_database', query_kyc_database)
        old_data = db_tool(customer_id)
        
        self.update_memory({'old_kyc_data': old_data})
        
        # Create response with routing information
        routing_info = self._create_routing_message(
            analysis_result=old_data,
            next_agent="document_verifier",
            reason="Need to verify submitted documents"
        )
        
        if old_data.get('exists'):
            status_info = f"Found existing KYC: {old_data.get('kyc_status', 'ACTIVE')}"
            if 'documents' in old_data:
                status_info += f"\nLast verified: {old_data['documents'].get('last_verified', 'N/A')}"
        else:
            status_info = "No existing KYC (new customer)"
        
        response_text = f"""
Document Retrieval Complete

Customer ID: {customer_id}
{status_info}

{routing_info}
"""
        
        print(f"\n[{self.name}]")
        if old_data.get('exists'):
            print(f"  Found existing KYC: {old_data.get('kyc_status', 'ACTIVE')}")
            print(f"  Last verified: {old_data.get('documents', {}).get('last_verified', 'N/A')}")
        else:
            print(f"  No existing KYC (new customer)")
        print(f"  → Routing to: Document Verifier Agent")
        
        response_message = ChatMessage(
            role=Role.ASSISTANT,
            contents=[TextContent(text=response_text.strip())]
        )
        
        # Notify thread if provided
        if thread is not None:
            normalized_messages = self._normalize_messages(messages)
            await self._notify_thread_of_new_messages(thread, normalized_messages, response_message)
        
        return AgentRunResponse(messages=[response_message])
