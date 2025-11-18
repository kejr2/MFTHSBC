"""KYC Function Tools - Tools that agents can use during processing"""

from typing import Annotated, Dict, Any, Optional
from pydantic import Field
import json


def query_kyc_database(
    customer_id: Annotated[str, Field(description="The customer ID to query in the KYC database.")]
) -> Dict[str, Any]:
    """Query the KYC database for existing customer records.
    
    Args:
        customer_id: The unique customer identifier.
    
    Returns:
        Dictionary containing customer KYC data if found, or empty dict if not found.
    """
    # Mock database - replace with real database in production
    mock_db = {
        "CUST001": {
            "exists": True,
            "kyc_status": "EXPIRED",
            "documents": {
                "pan": "ABCDE1234F",
                "aadhaar": "1234-5678-9012",
                "last_verified": "2023-01-15"
            },
            "customer_name": "Rajesh Kumar",
            "dob": "1985-06-15"
        },
        "CUST999": {"exists": False}
    }
    
    result = mock_db.get(customer_id, {"exists": False})
    return result


def extract_document_data(
    document_type: Annotated[str, Field(description="Type of document (pan_card, aadhaar, passport, etc.)")],
    document_data: Annotated[Dict[str, Any], Field(description="Document data dictionary containing number, name, dob, etc.")]
) -> Dict[str, Any]:
    """Extract and validate data from KYC documents using OCR-like processing.
    
    Args:
        document_type: The type of document being processed.
        document_data: The document data dictionary.
    
    Returns:
        Dictionary containing extracted and validated document information.
    """
    extracted = {
        "document_type": document_type,
        "extracted_data": {
            "number": document_data.get("number", ""),
            "name": document_data.get("name", ""),
            "dob": document_data.get("dob", ""),
            "address": document_data.get("address", "")
        },
        "validation": {
            "is_valid_format": True,
            "confidence": 0.95,
            "issues": []
        }
    }
    
    # Simulate validation checks
    if document_type == "pan_card":
        if len(document_data.get("number", "")) != 10:
            extracted["validation"]["is_valid_format"] = False
            extracted["validation"]["issues"].append("Invalid PAN format")
            extracted["validation"]["confidence"] = 0.5
    
    return extracted


def compare_face_similarity(
    selfie_data: Annotated[Dict[str, Any], Field(description="Selfie image data or reference")],
    id_photo_data: Annotated[Dict[str, Any], Field(description="ID document photo data or reference")]
) -> Dict[str, Any]:
    """Compare face similarity between selfie and ID document photo.
    
    Args:
        selfie_data: Selfie image data or reference.
        id_photo_data: ID document photo data or reference.
    
    Returns:
        Dictionary containing similarity score and match result.
    """
    # Mock face recognition - replace with real face recognition service in production
    # In production, this would use services like Azure Face API, AWS Rekognition, etc.
    
    # Simulate face similarity calculation
    similarity_score = 0.85  # Mock score
    
    # Adjust based on data quality
    if selfie_data.get("uploaded") and id_photo_data.get("available"):
        similarity_score = 0.87
    else:
        similarity_score = 0.65
    
    return {
        "similarity_score": similarity_score,
        "is_match": similarity_score >= 0.75,
        "confidence": 0.90,
        "details": {
            "face_detected": True,
            "quality_check": "passed"
        }
    }


def verify_compliance_rules(
    intent: Annotated[str, Field(description="KYC intent: NEW, RENEWAL, or UPDATE")],
    documents_present: Annotated[Dict[str, bool], Field(description="Dictionary indicating which documents are present (pan, aadhaar, selfie, etc.)")],
    verification_results: Annotated[Dict[str, Any], Field(description="Results from document verification")]
) -> Dict[str, Any]:
    """Verify compliance with RBI KYC rules based on intent and documents.
    
    Args:
        intent: The KYC intent (NEW, RENEWAL, UPDATE).
        documents_present: Dictionary of which documents are present.
        verification_results: Results from document verification.
    
    Returns:
        Dictionary containing compliance check results and risk assessment.
    """
    violations = []
    risk_level = "LOW"
    
    # Check required documents based on intent
    if intent == "NEW":
        if not documents_present.get("pan", False):
            violations.append("PAN card required for NEW KYC")
        if not documents_present.get("aadhaar", False):
            violations.append("Aadhaar required for NEW KYC")
        if not documents_present.get("selfie", False):
            violations.append("Selfie required for NEW KYC")
    
    elif intent == "RENEWAL":
        if not documents_present.get("pan", False):
            violations.append("PAN card required for RENEWAL")
        if not documents_present.get("aadhaar", False):
            violations.append("Aadhaar required for RENEWAL")
    
    # Check face similarity
    face_similarity = verification_results.get("face_similarity", 0.0)
    if face_similarity < 0.75:
        violations.append(f"Face similarity too low: {face_similarity:.2f}")
        risk_level = "MEDIUM"
    
    if face_similarity < 0.6:
        risk_level = "HIGH"
    
    # Determine final decision
    if violations:
        if risk_level == "HIGH":
            final_decision = "REJECT"
        else:
            final_decision = "HUMAN_REVIEW"
    else:
        final_decision = "AUTO_APPROVE"
    
    return {
        "compliant": len(violations) == 0,
        "risk_level": risk_level,
        "violations": violations,
        "final_decision": final_decision,
        "rules_applied": {
            "rbi_kyc_guidelines": True,
            "document_requirements": True,
            "face_verification": True
        }
    }


def verify_aadhaar_number(
    aadhaar_number: Annotated[str, Field(description="Aadhaar number to verify (format: XXXX-XXXX-XXXX)")]
) -> Dict[str, Any]:
    """Verify Aadhaar number format and perform basic validation.
    
    Args:
        aadhaar_number: The Aadhaar number to verify.
    
    Returns:
        Dictionary containing verification results.
    """
    # Mock Aadhaar verification - in production, this would call UIDAI API
    # Note: Real Aadhaar verification requires proper authentication and API access
    
    # Basic format validation
    cleaned = aadhaar_number.replace("-", "").replace(" ", "")
    is_valid_format = len(cleaned) == 12 and cleaned.isdigit()
    
    # Mock verification result
    if is_valid_format:
        return {
            "is_valid": True,
            "is_verified": True,  # Mock - would be actual API result
            "format_valid": True,
            "verification_method": "uidai_api",  # Mock
            "confidence": 0.95
        }
    else:
        return {
            "is_valid": False,
            "is_verified": False,
            "format_valid": False,
            "error": "Invalid Aadhaar format",
            "confidence": 0.0
        }


def check_name_consistency(
    names: Annotated[Dict[str, str], Field(description="Dictionary of names from different documents (pan_name, aadhaar_name, etc.)")]
) -> Dict[str, Any]:
    """Check if names are consistent across different documents.
    
    Args:
        names: Dictionary containing names from different documents.
    
    Returns:
        Dictionary containing consistency check results.
    """
    name_list = [v for v in names.values() if v]
    
    if not name_list:
        return {
            "is_consistent": False,
            "match_score": 0.0,
            "issues": ["No names provided"]
        }
    
    # Simple name matching (normalize and compare)
    normalized_names = [name.lower().strip() for name in name_list]
    unique_names = set(normalized_names)
    
    if len(unique_names) == 1:
        return {
            "is_consistent": True,
            "match_score": 1.0,
            "issues": []
        }
    else:
        # Calculate similarity (simple approach)
        # In production, use fuzzy matching libraries
        match_score = 0.7 if len(unique_names) == 2 else 0.5
        
        return {
            "is_consistent": False,
            "match_score": match_score,
            "issues": [f"Name mismatch detected: {', '.join(unique_names)}"]
        }

