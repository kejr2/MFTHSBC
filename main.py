"""KYC Multi-Agent System - Microsoft Agent Framework

Simple, clean workflow demonstrating Microsoft Agent Framework features.
"""

import asyncio
from workflow.orchestrator import KYCWorkflowGraph
from agents.kyc_base_agent import WORKFLOW_MEMORY


async def main():
    """Run KYC workflow scenarios"""
    
    print("\n" + "="*70)
    print("🏦 KYC Multi-Agent System - Microsoft Agent Framework")
    print("="*70)
    
    # Scenario 1: Clean KYC Renewal
    print("\n📝 SCENARIO 1: Clean KYC Renewal")
    print("-" * 70)
    
    WORKFLOW_MEMORY.clear()
    workflow = KYCWorkflowGraph()
    
    result = await workflow.run_async(
        customer_id="CUST001",
        customer_input="My KYC documents have expired, need renewal",
        new_documents={
            "pan_card": {
                "number": "ABCDE1234F",
                "name": "Rajesh Kumar",
                "dob": "1985-06-15"
            },
            "aadhaar": {
                "number": "1234-5678-9012",
                "name": "Rajesh Kumar",
                "dob": "1985-06-15",
                "address": "123 MG Road, Mumbai"
            },
            "selfie": {"uploaded": True}
        }
    )
    
    # Display result summary
    decision = result['final_decision']
    if decision == 'reject':
        print(f"\n❌ RESULT: REJECTED")
        if result.get('verification', {}).get('critical_failure'):
            print("   Critical document verification failure detected")
    elif decision == 'human_review':
        print(f"\n⚠️  RESULT: HUMAN REVIEW REQUIRED")
        compliance = result.get('compliance', {})
        if compliance.get('risk_level'):
            print(f"   Risk Level: {compliance.get('risk_level')}")
        if compliance.get('violations'):
            print(f"   Violations: {len(compliance.get('violations', []))} found")
    elif decision == 'auto_approve':
        print(f"\n✅ RESULT: AUTO-APPROVED")
    else:
        print(f"\n📋 RESULT: {decision.upper()}")
    
    print(f"📊 Execution Path: {' → '.join(result['execution_path'])}")
    
    # Scenario 2: New customer with issues
    print("\n\n📝 SCENARIO 2: New KYC with Missing Documents")
    print("-" * 70)
    
    WORKFLOW_MEMORY.clear()
    workflow2 = KYCWorkflowGraph()
    
    result2 = await workflow2.run_async(
        customer_id="CUST999",
        customer_input="I want to open a new account",
        new_documents={
            "pan_card": {
                "number": "XYZAB9999X",
                "name": "New Customer",
                "dob": "1990-03-20"
            }
            # Missing Aadhaar and Selfie
        }
    )
    
    # Display result summary
    decision2 = result2['final_decision']
    if decision2 == 'reject':
        print(f"\n❌ RESULT: REJECTED")
        if result2.get('verification', {}).get('critical_failure'):
            print("   Critical document verification failure detected")
    elif decision2 == 'human_review':
        print(f"\n⚠️  RESULT: HUMAN REVIEW REQUIRED")
        compliance2 = result2.get('compliance', {})
        if compliance2.get('risk_level'):
            print(f"   Risk Level: {compliance2.get('risk_level')}")
        if compliance2.get('violations'):
            print(f"   Violations: {len(compliance2.get('violations', []))} found")
    elif decision2 == 'auto_approve':
        print(f"\n✅ RESULT: AUTO-APPROVED")
    else:
        print(f"\n📋 RESULT: {decision2.upper()}")
    
    print(f"📊 Execution Path: {' → '.join(result2['execution_path'])}")
    
    print("\n" + "="*70)
    print("✅ Workflow Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    import config
    asyncio.run(main())
