"""Intent Classifier Agent - Entry point for KYC workflow"""

import asyncio
from typing import Any
from collections.abc import AsyncIterable
from agent_framework import (
    AgentRunResponse,
    AgentRunResponseUpdate,
    AgentThread,
    ChatMessage,
    Role,
    TextContent
)
from agents.kyc_base_agent import KYCBaseAgent


class IntentClassifierAgent(KYCBaseAgent):
    """Entry point - routes based on customer intent"""
    
    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Intent Classifier Agent."""
        super().__init__(
            name=name or "Intent Classifier",
            description=description or "Classifies customer intent (NEW/RENEWAL/UPDATE) and routes to Document Retrieval",
            **kwargs,
        )
    
    async def run(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        customer_id: str | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        """Execute the agent and return a complete response.
        
        Args:
            messages: The message(s) to process (customer input).
            thread: The conversation thread (optional).
            customer_id: Customer ID for the KYC request.
            **kwargs: Additional keyword arguments.
        
        Returns:
            An AgentRunResponse containing the agent's reply and routing decision.
        """
        # Normalize input messages
        normalized_messages = self._normalize_messages(messages)
        
        # Extract customer input
        if normalized_messages:
            customer_input = normalized_messages[-1].text or ""
        else:
            customer_input = str(messages) if messages else ""
        
        # Get customer_id from kwargs or memory
        if not customer_id:
            customer_id = kwargs.get('customer_id', 'UNKNOWN')
        
        # Classify intent using Gemini
        prompt = f"""
You are an Intent Classifier for KYC operations.

Customer says: "{customer_input}"

Classify into ONE category:
- NEW: First-time KYC
- RENEWAL: Documents expired
- UPDATE: Address/phone change

Return JSON:
{{
    "intent": "NEW|RENEWAL|UPDATE",
    "confidence": 0.0-1.0,
    "requires_old_data": true/false
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            # Fallback if parsing failed
            if not result:
                result = {
                    "intent": "NEW",
                    "confidence": 0.5,
                    "requires_old_data": True
                }
        except Exception as e:
            result = {
                "intent": "NEW",
                "confidence": 0.5,
                "requires_old_data": True
            }
        
        # Update memory
        self.update_memory({
            'customer_id': customer_id,
            'intent': result,
            'customer_input': customer_input
        })
        
        # Create response with routing information
        routing_info = self._create_routing_message(
            analysis_result=result,
            next_agent="document_retrieval",
            reason="Need to fetch existing KYC data (if any)"
        )
        
        response_text = f"""
Intent Classification Complete

Intent: {result.get('intent', 'UNKNOWN')}
Confidence: {result.get('confidence', 0.0):.2f}
Requires Old Data: {result.get('requires_old_data', False)}

{routing_info}
"""
        
        print(f"\n[{self.name}]")
        print(f"  Intent: {result.get('intent')}")
        print(f"  Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"  → Routing to: Document Retrieval Agent")
        
        response_message = ChatMessage(
            role=Role.ASSISTANT,
            contents=[TextContent(text=response_text.strip())]
        )
        
        # Notify thread if provided
        if thread is not None:
            await self._notify_thread_of_new_messages(thread, normalized_messages, response_message)
        
        return AgentRunResponse(messages=[response_message])
    
    async def run_stream(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        customer_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentRunResponseUpdate]:
        """Execute the agent and yield streaming response updates.
        
        Args:
            messages: The message(s) to process (customer input).
            thread: The conversation thread (optional).
            customer_id: Customer ID for the KYC request.
            **kwargs: Additional keyword arguments.
        
        Yields:
            AgentRunResponseUpdate objects containing chunks of the response.
        """
        # Normalize input messages
        normalized_messages = self._normalize_messages(messages)
        
        # Extract customer input
        if normalized_messages:
            customer_input = normalized_messages[-1].text or ""
        else:
            customer_input = str(messages) if messages else ""
        
        # Get customer_id from kwargs or memory
        if not customer_id:
            customer_id = kwargs.get('customer_id', 'UNKNOWN')
        
        # Classify intent using Gemini
        prompt = f"""
You are an Intent Classifier for KYC operations.

Customer says: "{customer_input}"

Classify into ONE category:
- NEW: First-time KYC
- RENEWAL: Documents expired
- UPDATE: Address/phone change

Return JSON:
{{
    "intent": "NEW|RENEWAL|UPDATE",
    "confidence": 0.0-1.0,
    "requires_old_data": true/false
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            # Fallback if parsing failed
            if not result:
                result = {
                    "intent": "NEW",
                    "confidence": 0.5,
                    "requires_old_data": True
                }
        except Exception as e:
            result = {
                "intent": "NEW",
                "confidence": 0.5,
                "requires_old_data": True
            }
        
        # Update memory
        self.update_memory({
            'customer_id': customer_id,
            'intent': result,
            'customer_input': customer_input
        })
        
        # Create response with routing information
        routing_info = self._create_routing_message(
            analysis_result=result,
            next_agent="document_retrieval",
            reason="Need to fetch existing KYC data (if any)"
        )
        
        response_text = f"""
Intent Classification Complete

Intent: {result.get('intent', 'UNKNOWN')}
Confidence: {result.get('confidence', 0.0):.2f}
Requires Old Data: {result.get('requires_old_data', False)}

{routing_info}
"""
        
        print(f"\n[{self.name}]")
        print(f"  Intent: {result.get('intent')}")
        print(f"  Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"  → Routing to: Document Retrieval Agent")
        
        # Stream the response
        async for update in self._stream_text(response_text.strip()):
            yield update
        
        # Notify thread if provided
        if thread is not None:
            complete_response = ChatMessage(
                role=Role.ASSISTANT,
                contents=[TextContent(text=response_text.strip())]
            )
            await self._notify_thread_of_new_messages(thread, normalized_messages, complete_response)
