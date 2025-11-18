"""KYC Base Agent - Extends Microsoft Agent Framework BaseAgent"""

import json
import asyncio
import google.generativeai as genai
from typing import Dict, Any
from collections.abc import AsyncIterable
from agent_framework import BaseAgent, AgentRunResponseUpdate, Role, TextContent

# Import config to ensure API key is configured before model initialization
import config


# Shared memory (agents read/write)
WORKFLOW_MEMORY: Dict[str, Any] = {}


class KYCBaseAgent(BaseAgent):
    """Base class for KYC agents - extends Microsoft Agent Framework BaseAgent"""
    
    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the KYC agent.
        
        Args:
            name: The name of the agent.
            description: The description of the agent.
            **kwargs: Additional keyword arguments passed to BaseAgent.
        """
        super().__init__(
            name=name or "KYC Agent",
            description=description or "KYC processing agent",
            **kwargs,
        )
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def update_memory(self, updates: Dict[str, Any]) -> None:
        """Write to shared memory"""
        WORKFLOW_MEMORY.update(updates)
        
    def get_memory(self, key: str) -> Any:
        """Read from shared memory"""
        return WORKFLOW_MEMORY.get(key)
    
    def get_all_memory(self) -> Dict[str, Any]:
        """Get entire memory state"""
        return WORKFLOW_MEMORY.copy()
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown wrappers"""
        try:
            # Clean JSON if wrapped in markdown
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
    
    def _create_routing_message(
        self,
        analysis_result: Dict[str, Any],
        next_agent: str,
        reason: str,
        status: str = "success"
    ) -> str:
        """Create a formatted message with routing information"""
        return json.dumps({
            "agent": self.name,
            "status": status,
            "analysis": analysis_result,
            "next_agent": next_agent,
            "reason": reason,
            "routing": True
        }, indent=2)
    
    async def _stream_text(self, text: str, delay: float = 0.05) -> AsyncIterable[AgentRunResponseUpdate]:
        """Helper method to stream text word by word"""
        words = text.split()
        for i, word in enumerate(words):
            # Add space before word except for the first one
            chunk_text = f" {word}" if i > 0 else word
            
            yield AgentRunResponseUpdate(
                contents=[TextContent(text=chunk_text)],
                role=Role.ASSISTANT,
            )
            
            # Small delay to simulate streaming
            await asyncio.sleep(delay)

