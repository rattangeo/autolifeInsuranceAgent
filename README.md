# Insurance Claims Processing Agent

An autonomous AI agent built with Microsoft Semantic Kernel that processes insurance claims using LLM-driven control flow. Designed for Manulife's insurance operations.

## 🎯 Features

- **Autonomous Agent**: LLM decides the control flow and reasoning steps
- **Multi-Step Processing**: Extract → Validate → Assess → Recommend
- **Policy Coverage Checking**: Validates claims against predefined insurance policies
- **Fraud Detection**: Identifies potential fraud indicators
- **Document Intelligence**: Extracts information from claim documents using Azure AI
- **Production-Ready**: Comprehensive logging, error handling, and testing

## 🏗️ Architecture

The agent uses a **ReAct (Reasoning + Acting)** pattern:

1. **Reason**: Analyzes the current state and decides next action
2. **Act**: Executes tools autonomously (extract, validate, assess)
3. **Observe**: Reviews results and determines if more actions needed
4. **Conclude**: Generates final recommendation when sufficient information gathered

### Agent Tools

- `extract_claim_information`: Extracts structured data from claim text
- `check_policy_coverage`: Validates coverage against policy database
- `assess_fraud_risk`: Calculates fraud risk score with indicators
- `calculate_approved_amount`: Computes final approved claim amount
- `generate_recommendation`: Creates final decision with reasoning

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Azure OpenAI access (GPT-4)
- Azure Document Intelligence (optional, for PDF processing)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd agent
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

### Running the Agent

**Process a sample claim:**
```bash
python main.py
```

**Process a specific claim:**
```bash
python main.py --claim "I was in a car accident on 11/20/2025. My car needs $8,500 in repairs. Policy number: POL-AUTO-001"
```

**Interactive mode:**
```bash
python main.py --interactive
```

## 📋 Example Claims

The agent comes with pre-configured sample claims for testing:

1. **Auto Collision** - Standard approval case
2. **Home Water Damage** - Partial coverage scenario
3. **Health Emergency** - High-value claim
4. **Suspicious Auto Claim** - Fraud detection test
5. **Expired Policy** - Rejection case

## 🏢 Policy Database

Pre-configured insurance policies:

- **Auto Insurance**: Collision, comprehensive, liability coverage
- **Home Insurance**: Property damage, theft, natural disasters
- **Health Insurance**: Emergency care, hospitalization, prescriptions
- **Life Insurance**: Term and whole life policies

See `src/data/policies.json` for full policy definitions.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_agent.py -v
```

## 📊 Project Structure

```
agent/
├── src/
│   ├── agent/
│   │   ├── claims_agent.py      # Main agent implementation
│   │   └── tools.py             # Agent tool functions
│   ├── models/
│   │   ├── claim.py             # Claim data models
│   │   └── policy.py            # Policy data models
│   ├── data/
│   │   ├── policies.json        # Policy database
│   │   └── sample_claims.json   # Example claims
│   ├── utils/
│   │   ├── config.py            # Configuration management
│   │   └── logger.py            # Logging setup
│   └── services/
│       └── document_service.py  # Azure Document Intelligence
├── tests/
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_models.py
├── main.py                      # CLI entry point
├── requirements.txt
├── .env                         # Environment variables
└── README.md
```

## 🔧 Configuration

Key environment variables:

```bash
# Required
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT=<deployment-name>
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional (for PDF processing)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=<endpoint>
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=<key>

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TEMPERATURE=0.7
LOG_LEVEL=INFO
```

## 🎓 How It Works

### Agent Decision Flow

```
User submits claim
    ↓
Agent analyzes and decides: "What should I do first?"
    ↓
Tool 1: Extract information from claim text
    ↓
Agent observes: "Do I have policy number? Yes. What next?"
    ↓
Tool 2: Check policy coverage
    ↓
Agent observes: "Policy active? Coverage limits? Now check fraud."
    ↓
Tool 3: Assess fraud risk
    ↓
Agent observes: "Risk acceptable? Calculate amount."
    ↓
Tool 4: Calculate approved amount
    ↓
Agent decides: "I have enough information to conclude."
    ↓
Tool 5: Generate final recommendation
    ↓
Output: APPROVED/DENIED with reasoning
```

The LLM autonomously decides:
- Which tool to use next
- Whether more information is needed
- When to conclude the analysis
- How to handle edge cases

## 🚀 Deployment (Coming Soon)

- Docker containerization
- Azure Container Apps deployment
- API endpoint with authentication
- CI/CD pipeline

## 📝 License

MIT License

## 👥 Author

Created for Avanade/Manulife demonstration
Contact: rattan@example.com
