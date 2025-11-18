"""Workflow Graph Executor - Uses Microsoft Agent Framework with autonomous routing"""

import json
import asyncio
from typing import Dict, Any
from agents.intent_classifier import IntentClassifierAgent
from agents.document_retrieval import DocumentRetrievalAgent
from agents.document_verifier import DocumentVerifierAgent
from agents.compliance_checker import ComplianceCheckerAgent
from agents.kyc_base_agent import WORKFLOW_MEMORY


class KYCWorkflowGraph:
    """Executes the agent graph - lets agents route themselves using Microsoft Agent Framework"""
    
    def __init__(self):
        self.agents = {
            'intent_classifier': IntentClassifierAgent(),
            'document_retrieval': DocumentRetrievalAgent(),
            'document_verifier': DocumentVerifierAgent(),
            'compliance_checker': ComplianceCheckerAgent()
        }
        self.execution_path = []
    
    def _extract_routing_info(self, response_text: str) -> Dict[str, Any]:
        """Extract routing information from agent response"""
        try:
            # Look for JSON routing info in response
            if '"routing": true' in response_text:
                # Find the JSON block
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    routing_data = json.loads(json_str)
                    if routing_data.get('routing'):
                        return routing_data
        except Exception:
            pass
        
        return {}
    
    async def run_async(
        self,
        customer_id: str,
        customer_input: str,
        new_documents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow asynchronously - agents decide their own routing"""
        
        # Clear memory for new workflow run
        WORKFLOW_MEMORY.clear()
        
        print("\n" + "="*70)
        print("🏦 AUTONOMOUS KYC WORKFLOW (Microsoft Agent Framework)")
        print("="*70)
        
        # Start with Intent Classifier
        current_agent_name = 'intent_classifier'
        current_response = await self.agents[current_agent_name].run(
            messages=customer_input,
            customer_id=customer_id
        )
        self.execution_path.append(self.agents[current_agent_name].name)
        
        # Extract routing info from response using .text property
        response_text = current_response.text if current_response.text else ""
        routing_info = self._extract_routing_info(response_text)
        next_agent_name = routing_info.get('next_agent', 'document_retrieval')
        
        # Keep routing until we reach a terminal state
        terminal_states = ['auto_approve', 'reject', 'human_review', 'end']
        
        while next_agent_name not in terminal_states:
            if next_agent_name == 'document_retrieval':
                current_agent_name = 'document_retrieval'
                current_response = await self.agents[current_agent_name].run()
            
            elif next_agent_name == 'document_verifier':
                current_agent_name = 'document_verifier'
                current_response = await self.agents[current_agent_name].run(
                    new_documents=new_documents
                )
            
            elif next_agent_name == 'compliance_checker':
                current_agent_name = 'compliance_checker'
                current_response = await self.agents[current_agent_name].run()
            
            else:
                # Unknown agent - break to avoid infinite loop
                print(f"\n⚠️  Unknown next agent: {next_agent_name}")
                break
            
            self.execution_path.append(self.agents[current_agent_name].name)
            
            # Extract next routing decision using .text property
            response_text = current_response.text if current_response.text else ""
            routing_info = self._extract_routing_info(response_text)
            next_agent_name = routing_info.get('next_agent', 'end')
        
        # Extract detailed information from memory for final output
        verification = WORKFLOW_MEMORY.get('verification', {})
        compliance = WORKFLOW_MEMORY.get('compliance', {})
        
        # Final output with enhanced failure/human approval display
        print("\n" + "="*70)
        print("📊 WORKFLOW COMPLETE")
        print("="*70)
        
        # Determine status and display accordingly
        if next_agent_name == 'reject':
            print("\n❌ FINAL DECISION: REJECTED")
            print("="*70)
            print(f"Reason: {routing_info.get('reason', 'Workflow completed')}")
            
            # Show critical failures
            if verification.get('critical_failure', False):
                print("\n🚨 CRITICAL FAILURES DETECTED:")
                if verification.get('issues'):
                    for issue in verification.get('issues', [])[:5]:
                        print(f"  • {issue}")
            
            # Show compliance violations
            if compliance.get('violations'):
                print("\n⚠️  COMPLIANCE VIOLATIONS:")
                for violation in compliance.get('violations', [])[:5]:
                    print(f"  • {violation}")
            
            # Show verification issues
            if verification.get('issues') and not verification.get('critical_failure', False):
                print("\n⚠️  VERIFICATION ISSUES:")
                for issue in verification.get('issues', [])[:5]:
                    print(f"  • {issue}")
                    
        elif next_agent_name == 'human_review':
            print("\n⚠️  FINAL DECISION: HUMAN REVIEW REQUIRED")
            print("="*70)
            print(f"Reason: {routing_info.get('reason', 'Workflow completed')}")
            
            # Show why human review is needed
            risk_level = compliance.get('risk_level', 'UNKNOWN')
            print(f"\n📋 REVIEW DETAILS:")
            print(f"  Risk Level: {risk_level}")
            
            if compliance.get('violations'):
                print(f"\n⚠️  Issues Requiring Review:")
                for violation in compliance.get('violations', [])[:5]:
                    print(f"  • {violation}")
            
            if verification.get('issues'):
                print(f"\n⚠️  Verification Issues:")
                for issue in verification.get('issues', [])[:5]:
                    print(f"  • {issue}")
            
            if verification.get('face_similarity', 1.0) < 0.75:
                print(f"\n⚠️  Face Similarity: {verification.get('face_similarity', 0.0):.2f} (Threshold: 0.75)")
            
            print(f"\n👤 ACTION REQUIRED: Manual review by compliance officer")
            
        elif next_agent_name == 'auto_approve':
            print("\n✅ FINAL DECISION: AUTO-APPROVED")
            print("="*70)
            print(f"Reason: {routing_info.get('reason', 'All checks passed')}")
        else:
            print(f"\n📋 Final Decision: {next_agent_name.upper()}")
            print(f"Reason: {routing_info.get('reason', 'Workflow completed')}")
        
        print(f"\n📊 Execution Path: {' → '.join(self.execution_path)}")
        print("="*70 + "\n")
        
        return {
            'final_decision': next_agent_name,
            'execution_path': self.execution_path,
            'reason': routing_info.get('reason', 'Workflow completed'),
            'memory_state': WORKFLOW_MEMORY.copy(),
            'verification': verification,
            'compliance': compliance
        }
    
    def run(
        self,
        customer_id: str,
        customer_input: str,
        new_documents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronous wrapper for async execution"""
        return asyncio.run(self.run_async(customer_id, customer_input, new_documents))
