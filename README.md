# KYC Multi-Agent System - Microsoft Agent Framework

## 🎯 Overview

A clean, production-ready KYC (Know Your Customer) multi-agent system built with Microsoft Agent Framework. Agents autonomously route the workflow based on their analysis.

**Built with**: Microsoft Agent Framework (`agent-framework-core`) + Google Gemini API

## 📁 Project Structure

```
MFT_HSBC/
├── agents/                    # Agent modules
│   ├── kyc_base_agent.py      # Base agent (extends Microsoft BaseAgent)
│   ├── intent_classifier.py   # Classifies customer intent
│   ├── document_retrieval.py  # Retrieves existing KYC data
│   ├── document_verifier.py   # Verifies documents
│   └── compliance_checker.py  # Final compliance check
├── tools/                     # Function tools
│   └── kyc_tools.py           # KYC function tools
├── workflow/                  # Orchestration
│   └── orchestrator.py        # Workflow executor
├── config.py                  # Configuration
├── main.py                    # Main entry point
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/akilo/MFT_HSBC
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Get your API key from: [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Run

```bash
python main.py
```

## 🤖 Agents

All agents extend `KYCBaseAgent` which extends Microsoft's `BaseAgent`.

1. **Intent Classifier** - Classifies customer intent (NEW/RENEWAL/UPDATE)
2. **Document Retrieval** - Retrieves existing KYC records
3. **Document Verifier** - Verifies document authenticity
4. **Compliance Checker** - Applies RBI KYC rules and makes final decision

## 🔄 How It Works

Each agent autonomously decides where to route the workflow next:

```
[Intent Classifier] → [Document Retrieval] → [Document Verifier] → [Compliance Checker]
                                                                         ↓
                                                                    [Decision]
```

Agents use Microsoft Agent Framework's `AgentRunResponse` to communicate routing decisions.

## 🛠️ Tools

Agents use function tools from `tools/kyc_tools.py`:
- `query_kyc_database()` - Query existing records
- `extract_document_data()` - Extract document information
- `compare_face_similarity()` - Face verification
- `check_name_consistency()` - Name matching
- `verify_compliance_rules()` - Compliance checking

## 📊 Example Output

```
🏦 AUTONOMOUS KYC WORKFLOW (Microsoft Agent Framework)
======================================================================
[Intent Classifier]
  Intent: RENEWAL
  → Routing to: Document Retrieval Agent

[Document Retrieval]
  Found existing KYC: EXPIRED
  → Routing to: Document Verifier Agent

[Document Verifier]
  Checks Passed: True
  → Routing to: Compliance Checker

[Compliance Checker]
  ✅ AUTO APPROVE

📊 WORKFLOW COMPLETE
Final Decision: AUTO_APPROVE
Execution Path: Intent Classifier → Document Retrieval → Document Verifier → Compliance Checker
```

## 🔧 Requirements

- Python 3.8+
- `google-generativeai` - Gemini API
- `agent-framework-core` - Microsoft Agent Framework

## 📝 Notes

- **Memory**: Shared via `WORKFLOW_MEMORY` dict
- **Error Handling**: Basic JSON parsing fallbacks included
- **Database**: Currently mocked - replace with real DB in production
- **API Key**: Store in environment variables for security

---

**Built with**: Python 3.8+, Microsoft Agent Framework, Google Gemini API
