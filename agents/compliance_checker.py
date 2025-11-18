"""Compliance Checker Agent - Final decision maker"""

import json
from typing import Any, Callable
from agent_framework import AgentRunResponse, AgentThread, ChatMessage, Role, TextContent
from agents.kyc_base_agent import KYCBaseAgent
from tools.kyc_tools import verify_compliance_rules


class ComplianceCheckerAgent(KYCBaseAgent):
    """Applies rules - Routes to Approve/Review/Reject"""
    
    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tools: list[Callable] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Compliance Checker Agent.
        
        Args:
            name: The name of the agent.
            description: The description of the agent.
            tools: List of function tools available to this agent.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            name=name or "Compliance Checker",
            description=description or "Applies RBI KYC rules and makes final routing decision",
            **kwargs,
        )
        # Agent-level tools (default includes compliance verification tool)
        self.agent_tools = tools or [verify_compliance_rules]
    
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
            An AgentRunResponse containing compliance check results and final routing decision.
        """
        # Combine agent-level and run-level tools (run-level takes precedence)
        available_tools = {**{tool.__name__: tool for tool in self.agent_tools}}
        if tools:
            available_tools.update({tool.__name__: tool for tool in tools})
        
        intent = self.get_memory('intent')
        verification = self.get_memory('verification')
        old_data = self.get_memory('old_kyc_data')
        
        # Use compliance verification tool
        intent_type = intent.get('intent', 'NEW') if intent else 'NEW'
        documents_present = {
            "pan": verification.get('extracted_data', {}).get('pan', '') != '',
            "aadhaar": verification.get('extracted_data', {}).get('aadhaar', '') != '',
            "selfie": verification.get('face_similarity', 0.0) > 0
        }
        
        compliance_tool = available_tools.get('verify_compliance_rules', verify_compliance_rules)
        tool_result = compliance_tool(intent_type, documents_present, verification)
        
        # Combine tool results with LLM analysis
        prompt = f"""
You are a Compliance Rules Agent for RBI KYC regulations.

Intent: {intent.get('intent') if intent else 'UNKNOWN'}
Verification Results: {json.dumps(verification, indent=2)}
Old Data: {json.dumps(old_data, indent=2)}

Tool Compliance Check Results:
- Compliant: {tool_result.get('compliant', False)}
- Risk Level: {tool_result.get('risk_level', 'UNKNOWN')}
- Violations: {tool_result.get('violations', [])}
- Tool Decision: {tool_result.get('final_decision', 'UNKNOWN')}

Based on tool results and additional context, make final decision:
1. Review tool-detected violations
2. Consider verification quality and confidence
3. Apply additional RBI KYC rules if needed

Return JSON:
{{
    "compliant": {str(tool_result.get('compliant', False)).lower()},
    "risk_level": "{tool_result.get('risk_level', 'MEDIUM')}",
    "violations": {json.dumps(tool_result.get('violations', []))},
    "final_decision": "{tool_result.get('final_decision', 'HUMAN_REVIEW')}"
}}

You may override tool decision if additional context warrants it.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            # Merge tool results (tool results take precedence for compliance)
            result['compliant'] = tool_result.get('compliant', result.get('compliant', False))
            result['risk_level'] = tool_result.get('risk_level', result.get('risk_level', 'MEDIUM'))
            result['violations'] = tool_result.get('violations', result.get('violations', []))
            result['final_decision'] = tool_result.get('final_decision', result.get('final_decision', 'HUMAN_REVIEW'))
            result['rules_applied'] = tool_result.get('rules_applied', {})
            
            # Fallback if parsing failed
            if not result:
                result = tool_result.copy()
        except Exception as e:
            # Use tool result as fallback
            result = tool_result.copy()
        
        self.update_memory({'compliance': result})
        
        # AUTONOMOUS ROUTING DECISION (Final)
        decision = result.get('final_decision', 'HUMAN_REVIEW')
        
        if decision == "AUTO_APPROVE":
            next_agent = "auto_approve"
            reason = "All compliance checks passed"
            status = "approved"
        elif decision == "HUMAN_REVIEW":
            next_agent = "human_review"
            reason = f"Risk level {result.get('risk_level', 'UNKNOWN')} requires review"
            status = "review_required"
        else:  # REJECT
            next_agent = "reject"
            reason = "Compliance violations detected"
            status = "rejected"
        
        # Create response with routing information
        routing_info = self._create_routing_message(
            analysis_result=result,
            next_agent=next_agent,
            reason=reason,
            status=status
        )
        
        violations_text = ""
        if result.get('violations'):
            violations_text = f"\nViolations: {', '.join(result['violations'][:2])}"
        
        response_text = f"""
Compliance Check Complete

Compliant: {result.get('compliant', False)}
Risk Level: {result.get('risk_level', 'UNKNOWN')}
Final Decision: {decision}{violations_text}

{routing_info}
"""
        
        print(f"\n[{self.name}]")
        print(f"  Compliant: {result.get('compliant', False)}")
        print(f"  Risk Level: {result.get('risk_level', 'UNKNOWN')}")
        
        if decision == "AUTO_APPROVE":
            print(f"  ✅ AUTO APPROVE")
            print(f"  → Routing to: END (Approved)")
        elif decision == "HUMAN_REVIEW":
            print(f"  ⚠️  HUMAN REVIEW REQUIRED")
            print(f"  → Routing to: Human Review Queue")
        else:
            print(f"  ❌ REJECT")
            print(f"  → Routing to: END (Rejected)")
        
        response_message = ChatMessage(
            role=Role.ASSISTANT,
            contents=[TextContent(text=response_text.strip())]
        )
        
        # Notify thread if provided
        if thread is not None:
            normalized_messages = self._normalize_messages(messages)
            await self._notify_thread_of_new_messages(thread, normalized_messages, response_message)
        
        return AgentRunResponse(messages=[response_message])
