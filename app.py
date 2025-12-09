"""
Flask web application for Insurance Claims Processing Agent.
Provides a simple UI for demonstrating the agent to clients.
"""

import asyncio
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from src.agent import ClaimsProcessingAgent
from src.models import Claim
from src.utils import logger

app = Flask(__name__)
agent = None


def load_sample_claims():
    """Load sample claims from JSON file."""
    claims_path = Path(__file__).parent / "src" / "data" / "sample_claims.json"
    with open(claims_path, 'r') as f:
        return json.load(f)


def load_policies():
    """Load policies from JSON file."""
    policies_path = Path(__file__).parent / "src" / "data" / "policies.json"
    with open(policies_path, 'r') as f:
        return json.load(f)


@app.route('/')
def index():
    """Main page with claim selection."""
    return render_template('index.html')


@app.route('/api/claims')
def get_claims():
    """Get all sample claims."""
    claims = load_sample_claims()
    return jsonify(claims)


@app.route('/api/policies')
def get_policies():
    """Get all policies."""
    policies = load_policies()
    return jsonify(policies)


@app.route('/api/process', methods=['POST'])
def process_claim():
    """Process a claim."""
    global agent
    
    try:
        data = request.json
        claim_id = data.get('claim_id')
        
        # Load the claim
        claims = load_sample_claims()
        claim_data = next((c for c in claims if c['id'] == claim_id), None)
        
        if not claim_data:
            return jsonify({'error': 'Claim not found'}), 404
        
        # Initialize agent if needed
        if agent is None:
            policies_path = Path(__file__).parent / "src" / "data" / "policies.json"
            agent = ClaimsProcessingAgent(policies_path)
        
        # Get the claim text
        claim_text = claim_data.get('claim_text', '')
        
        # Process the claim (run async function in sync context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(agent.process_claim(claim_text))
        loop.close()
        
        # Convert result to dict
        reasoning_text = result.recommendation.reasoning if result.recommendation else 'Processing...'
        logger.info(f"Reasoning length: {len(reasoning_text)} characters")
        logger.info(f"Full reasoning: {reasoning_text}")
        
        response = {
            'claim_summary': {
                'id': claim_data['id'],
                'title': claim_data['title'],
                'policy_number': result.information.policy_number if result.information else 'N/A',
                'claim_type': result.information.claim_type.value if result.information else 'N/A',
                'amount': f"${result.information.claim_amount:,.2f}" if result.information else '$0.00',
                'description': claim_data['description']
            },
            'decision': {
                'status': result.recommendation.status.value if result.recommendation else 'pending',
                'approved_amount': f"${result.recommendation.approved_amount:,.2f}" if result.recommendation else '$0.00',
                'confidence': f"{result.recommendation.confidence * 100:.0f}%" if result.recommendation else 'N/A',
                'fraud_risk': result.fraud_assessment.risk_level.value if result.fraud_assessment else 'N/A'
            },
            'reasoning': reasoning_text,
            'next_steps': result.recommendation.next_steps if result.recommendation else [],
            'processing_log': [
                {
                    'timestamp': log.split(']')[0].strip('[') if ']' in log else '',
                    'message': log.split(']')[1].strip() if ']' in log else log
                }
                for log in result.processing_log
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing claim: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Insurance Claims Processing Agent - Web Interface")
    print("="*60)
    print("\nStarting server at http://localhost:5000")
    print("Press CTRL+C to stop the server\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
