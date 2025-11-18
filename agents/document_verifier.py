"""Document Verifier Agent - Verifies documents and routes based on validation"""

import json
from typing import Any, Dict, Callable
from agent_framework import AgentRunResponse, AgentThread, ChatMessage, Role, TextContent
from agents.kyc_base_agent import KYCBaseAgent
from tools.kyc_tools import (
    extract_document_data,
    compare_face_similarity,
    check_name_consistency,
    verify_aadhaar_number
)


class DocumentVerifierAgent(KYCBaseAgent):
    """Verifies documents - Routes based on validation results"""
    
    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tools: list[Callable] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Document Verifier Agent.
        
        Args:
            name: The name of the agent.
            description: The description of the agent.
            tools: List of function tools available to this agent.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            name=name or "Document Verifier",
            description=description or "Verifies document authenticity and routes based on validation results",
            **kwargs,
        )
        # Agent-level tools (default includes verification tools)
        self.agent_tools = tools or [
            extract_document_data,
            compare_face_similarity,
            check_name_consistency,
            verify_aadhaar_number
        ]
    
    async def run(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        new_documents: Dict[str, Any] | None = None,
        tools: list[Callable] | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        """Execute the agent and return a complete response.
        
        Args:
            messages: The message(s) to process (optional).
            thread: The conversation thread (optional).
            new_documents: New documents submitted by customer.
            tools: Run-level tools (combined with agent-level tools).
            **kwargs: Additional keyword arguments.
        
        Returns:
            An AgentRunResponse containing verification results and routing decision.
        """
        # Get documents from kwargs or memory
        if not new_documents:
            new_documents = kwargs.get('new_documents', {})
        
        # Combine agent-level and run-level tools (run-level takes precedence)
        available_tools = {**{tool.__name__: tool for tool in self.agent_tools}}
        if tools:
            available_tools.update({tool.__name__: tool for tool in tools})
        
        intent = self.get_memory('intent')
        old_data = self.get_memory('old_kyc_data')
        
        # Use tools for document verification
        extracted_data = {}
        face_similarity_result = {"similarity_score": 0.0, "is_match": False}
        name_consistency_result = {"is_consistent": True}
        
        # Extract document data using tools
        if 'pan_card' in new_documents:
            extract_tool = available_tools.get('extract_document_data', extract_document_data)
            extracted_data['pan'] = extract_tool('pan_card', new_documents['pan_card'])
        
        if 'aadhaar' in new_documents:
            extract_tool = available_tools.get('extract_document_data', extract_document_data)
            extracted_data['aadhaar'] = extract_tool('aadhaar', new_documents['aadhaar'])
            
            # Verify Aadhaar number
            verify_aadhaar_tool = available_tools.get('verify_aadhaar_number', verify_aadhaar_number)
            aadhaar_verification = verify_aadhaar_tool(new_documents['aadhaar'].get('number', ''))
        
        # Check name consistency
        if 'pan_card' in new_documents and 'aadhaar' in new_documents:
            names = {
                'pan_name': new_documents['pan_card'].get('name', ''),
                'aadhaar_name': new_documents['aadhaar'].get('name', '')
            }
            name_tool = available_tools.get('check_name_consistency', check_name_consistency)
            name_consistency_result = name_tool(names)
        
        # Compare face similarity if selfie provided
        if 'selfie' in new_documents:
            face_tool = available_tools.get('compare_face_similarity', compare_face_similarity)
            face_similarity_result = face_tool(
                new_documents.get('selfie', {}),
                {'available': True}  # ID photo reference
            )
        
        # Combine tool results with LLM analysis
        tool_results = {
            "extracted_data": extracted_data,
            "face_similarity": face_similarity_result.get("similarity_score", 0.0),
            "face_match": face_similarity_result.get("is_match", False),
            "name_consistent": name_consistency_result.get("is_consistent", True),
            "name_issues": name_consistency_result.get("issues", [])
        }
        
        # Use Gemini for final analysis combining tool results
        prompt = f"""
You are a Document Verifier for KYC operations.

Intent: {intent.get('intent') if intent else 'UNKNOWN'}
Old Data: {json.dumps(old_data, indent=2)}
New Documents: {json.dumps(new_documents, indent=2)}

Tool Results:
- Face Similarity: {tool_results['face_similarity']:.2f} (Match: {tool_results['face_match']})
- Name Consistency: {tool_results['name_consistent']} (Issues: {tool_results['name_issues']})
- Extracted Data: {json.dumps(extracted_data, indent=2)}

Based on tool results, verify:
1. Name consistency (already checked by tool)
2. DOB match across documents
3. Face similarity (already checked by tool)
4. Document validity and completeness
5. Required documents present (PAN, Aadhaar for NEW/RENEWAL)

Return JSON:
{{
    "all_checks_passed": true/false,
    "face_similarity": {tool_results['face_similarity']:.2f},
    "issues": ["list of problems found"],
    "critical_failure": true/false,
    "extracted_data": {json.dumps(extracted_data, indent=2)}
}}

Critical failure should be true if:
- Fake/forged documents detected
- Major name/DOB mismatches
- Face similarity < 0.3
- Missing critical documents
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            # Merge tool results with LLM analysis
            result['face_similarity'] = tool_results['face_similarity']
            result['face_match'] = tool_results['face_match']
            result['name_consistent'] = tool_results['name_consistent']
            
            # Add tool-detected issues
            if not result.get('issues'):
                result['issues'] = []
            result['issues'].extend(tool_results['name_issues'])
            
            # Fallback if parsing failed
            if not result:
                result = {
                    "all_checks_passed": False,
                    "face_similarity": tool_results['face_similarity'],
                    "issues": ["JSON parsing error - manual review required"],
                    "critical_failure": False,
                    "extracted_data": extracted_data
                }
        except Exception as e:
            result = {
                "all_checks_passed": False,
                "face_similarity": tool_results['face_similarity'],
                "issues": ["Error during verification - manual review required"],
                "critical_failure": False,
                "extracted_data": extracted_data
            }
        
        self.update_memory({'verification': result})
        
        # AUTONOMOUS ROUTING DECISION
        if result.get('critical_failure', False):
            next_agent = "reject"
            reason = "Critical document verification failure"
            status = "critical_failure"
        elif not result.get('all_checks_passed', False) or result.get('face_similarity', 0.0) < 0.75:
            next_agent = "compliance_checker"
            reason = "Issues detected - need compliance review"
            status = "issues_found"
        else:
            next_agent = "compliance_checker"
            reason = "Verification passed - final compliance check"
            status = "success"
        
        # Create response with routing information
        routing_info = self._create_routing_message(
            analysis_result=result,
            next_agent=next_agent,
            reason=reason,
            status=status
        )
        
        issues_text = ""
        if result.get('issues'):
            issues_text = f"\nIssues: {', '.join(result['issues'][:3])}"
        
        response_text = f"""
Document Verification Complete

Checks Passed: {result.get('all_checks_passed', False)}
Face Similarity: {result.get('face_similarity', 0.0):.2f}{issues_text}

{routing_info}
"""
        
        print(f"\n[{self.name}]")
        print(f"  Checks Passed: {result.get('all_checks_passed', False)}")
        print(f"  Face Similarity: {result.get('face_similarity', 0.0):.2f}")
        
        if result.get('critical_failure', False):
            print(f"  ❌ Critical failure detected")
            print(f"  → Routing to: REJECT")
        elif status == "issues_found":
            print(f"  ⚠️  Issues found, needs review")
            print(f"  → Routing to: Compliance Checker (strict mode)")
        else:
            print(f"  ✅ All checks passed")
            print(f"  → Routing to: Compliance Checker (standard mode)")
        
        response_message = ChatMessage(
            role=Role.ASSISTANT,
            contents=[TextContent(text=response_text.strip())]
        )
        
        # Notify thread if provided
        if thread is not None:
            normalized_messages = self._normalize_messages(messages)
            await self._notify_thread_of_new_messages(thread, normalized_messages, response_message)
        
        return AgentRunResponse(messages=[response_message])
