# AutoLife Insurance Claims Agent

AI agent that processes insurance claims autonomously using Azure OpenAI.

## What it does

The agent analyzes insurance claims and decides whether to approve or deny them. It extracts claim details, checks policy coverage, assesses fraud risk, and calculates approved amounts.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your Azure OpenAI credentials to `.env`:

```
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

## Usage

Test with sample claims:
```bash
python main.py --sample 1
```

Interactive mode:
```bash
python main.py --interactive
```

Process custom claim:
```bash
python main.py --claim "Your claim text here"
```

## How it works

The agent uses LLM to decide which actions to take:

1. Extracts claim information (policy number, amount, date)
2. Validates policy coverage and limits
3. Checks for fraud indicators
4. Calculates approved amount
5. Makes final decision with reasoning

The LLM controls the flow - it decides which tools to use and when it has enough information to conclude.

## Project structure

```
src/
  agent/          # Agent logic and tools
  models/         # Data models
  data/           # Policy database and sample claims
  utils/          # Config and logging
tests/            # Unit tests
main.py           # CLI interface
```

## Running tests

```bash
pytest
```

## Tech stack

- Semantic Kernel - agent framework
- Azure OpenAI - GPT-4 for reasoning
- Pydantic - data validation
- Rich - terminal UI
