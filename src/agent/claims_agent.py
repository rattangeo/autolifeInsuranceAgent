"""
Insurance Claims Processing Agent using Semantic Kernel.
The agent autonomously decides which tools to use and when to conclude.
"""

import json
from pathlib import Path
from typing import Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelPlugin

from ..models import Claim
from ..utils import settings, logger
from .tools import ClaimsTools


class ClaimsProcessingAgent:
    """
    Autonomous agent for processing insurance claims.
    Uses LLM to decide control flow and which tools to use.
    """
    
    def __init__(self, policies_path: Path):
        """
        Initialize the agent.
        
        Args:
            policies_path: Path to policies JSON database
        """
        self.kernel = Kernel()
        self.tools = ClaimsTools(policies_path)
        
        # Add Azure OpenAI chat service
        chat_service_id = "default"
        self.kernel.add_service(
            AzureChatCompletion(
                service_id=chat_service_id,
                deployment_name=settings.azure_openai_deployment,
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
        )
        
        # Register tools as plugin
        plugin = KernelPlugin.from_object(
            plugin_name="ClaimsTools",
            plugin_instance=self.tools
        )
        self.kernel.add_plugin(plugin)
        
        # Configure function calling behavior
        from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
        self.execution_settings = OpenAIChatPromptExecutionSettings(
            service_id=chat_service_id,
            temperature=settings.agent_temperature,
            max_tokens=2000
        )
        self.execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        
        logger.info("Claims Processing Agent initialized")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt that guides agent behavior."""
        return """You are an expert insurance claims processing agent for AutoLife Insurance.

Your role is to autonomously analyze insurance claims and make decisions about approval or denial.

PROCESS:
1. First, extract claim information using extract_claim_information
2. Then, check policy coverage using check_policy_coverage
3. Assess fraud risk using assess_fraud_risk
4. Calculate the approved amount using calculate_approved_amount
5. Make a final recommendation

DECISION RULES:
- DENY claims if:
  * Policy is expired, cancelled, or not found
  * Claim type is not covered by the policy
  * Fraud risk is CRITICAL (score >= 70)
  * Claim amount is $0 after deductible

- NEEDS_REVIEW if:
  * Fraud risk is HIGH or MEDIUM (score >= 20)
  * Claim amount exceeds coverage limits significantly
  * Missing critical information

- APPROVE if:
  * Policy is active and valid
  * Claim type is covered
  * Fraud risk is LOW (score < 20)
  * Approved amount is > $0

IMPORTANT:
- Be thorough but decisive
- Use ALL relevant tools before making a decision
- Explain your reasoning clearly
- Calculate exact approved amounts (claim - deductible, capped at coverage limit)
- Be fair but protect against fraud

After gathering all information, provide a final recommendation with:
- Status (APPROVED/DENIED/NEEDS_REVIEW)
- Approved amount
- Clear reasoning
- Confidence level (0-1)
- Next steps

Think step by step and use tools autonomously to make the best decision."""

    async def process_claim(self, claim_text: str) -> Claim:
        """
        Process an insurance claim autonomously.
        
        Args:
            claim_text: Raw claim submission text
            
        Returns:
            Processed Claim object with all analysis
        """
        logger.info("Starting claim processing")
        logger.info(f"Claim text: {claim_text[:100]}...")
        
        claim = Claim(raw_claim_text=claim_text)
        claim.add_log("Claim submitted for processing")
        
        # Create chat history
        chat_history = ChatHistory()
        chat_history.add_system_message(self._create_system_prompt())
        
        # Initial user message
        user_message = f"""Please process this insurance claim and make a decision:

CLAIM TEXT:
{claim_text}

Analyze this claim step-by-step using your tools, then provide a final recommendation."""
        
        chat_history.add_user_message(user_message)
        claim.add_log("Agent analysis started")
        
        # Let the agent work autonomously
        iteration = 0
        max_iterations = settings.agent_max_iterations
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}/{max_iterations}")
            
            # Get agent response (will automatically call tools as needed)
            from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
            chat_service: ChatCompletionClientBase = self.kernel.get_service()
            response = await chat_service.get_chat_message_contents(
                chat_history=chat_history,
                settings=self.execution_settings,
                kernel=self.kernel,
            )
            
            # Get the response content
            if response and len(response) > 0:
                assistant_message = response[0]
                content = str(assistant_message)
                
                # Add to history
                chat_history.add_assistant_message(content)
                claim.add_log(f"Agent reasoning: {content[:200]}...")
                
                logger.info(f"Agent response: {content[:150]}...")
                
                # Check if agent has made a final decision
                if self._has_final_decision(content):
                    logger.info("Agent has reached a decision")
                    claim.add_log("Agent decision finalized")
                    
                    # Parse the final recommendation
                    recommendation = self._parse_recommendation(content)
                    if recommendation:
                        claim.recommendation = recommendation
                        claim.add_log(f"Decision: {recommendation.status.value} - ${recommendation.approved_amount:,.2f}")
                    
                    break
                
                # If no tool calls and no decision, prompt agent to conclude
                if iteration >= max_iterations - 1:
                    chat_history.add_user_message(
                        "Please provide your final recommendation now based on the information gathered."
                    )
            else:
                logger.warning("Empty response from agent")
                break
        
        if not claim.recommendation:
            # Fallback if agent didn't provide recommendation
            logger.warning("Agent did not provide recommendation, creating default")
            from ..models import ClaimRecommendation, ClaimStatus
            claim.recommendation = ClaimRecommendation(
                status=ClaimStatus.NEEDS_REVIEW,
                approved_amount=0.0,
                reasoning="Unable to complete automated processing. Manual review required.",
                confidence=0.0,
                next_steps=["Manual review by claims adjuster", "Verify all claim details"]
            )
            claim.add_log("Defaulted to manual review")
        
        logger.info("Claim processing complete")
        return claim
    
    def _has_final_decision(self, content: str) -> bool:
        """Check if the agent message contains a final decision."""
        decision_keywords = [
            "final recommendation",
            "my recommendation",
            "decision:",
            "approved for",
            "deny this claim",
            "denied",
            "needs review",
            "requires manual review"
        ]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in decision_keywords)
    
    def _parse_recommendation(self, content: str) -> Optional['ClaimRecommendation']:
        """Parse recommendation from agent's response."""
        from ..models import ClaimRecommendation, ClaimStatus
        import re
        
        content_lower = content.lower()
        
        # Determine status - check denied first as it's more specific
        if any(word in content_lower for word in ['denied', 'deny', 'reject']):
            status = ClaimStatus.DENIED
        elif any(word in content_lower for word in ['approved', 'approve']):
            status = ClaimStatus.APPROVED
        else:
            status = ClaimStatus.NEEDS_REVIEW
        
        # Extract approved amount
        amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars'
        ]
        
        approved_amount = 0.0
        for pattern in amount_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Get the largest amount mentioned
                amounts = [float(m.replace(',', '')) for m in matches]
                approved_amount = max(amounts)
                break
        
        # Extract confidence (if mentioned)
        confidence = 0.8  # default
        confidence_match = re.search(r'confidence[:\s]+(\d+)%', content_lower)
        if confidence_match:
            confidence = float(confidence_match.group(1)) / 100
        
        # Reasoning is the content itself (truncated)
        reasoning = content[:500] if len(content) > 500 else content
        
        # Generate next steps based on status
        if status == ClaimStatus.APPROVED:
            next_steps = [
                "Issue payment to claimant",
                "Send approval notification",
                "Close claim"
            ]
        elif status == ClaimStatus.DENIED:
            next_steps = [
                "Send denial letter with explanation",
                "Provide appeals process information",
                "Close claim"
            ]
        else:
            next_steps = [
                "Assign to claims adjuster for review",
                "Request additional documentation",
                "Schedule follow-up investigation"
            ]
        
        return ClaimRecommendation(
            status=status,
            approved_amount=approved_amount,
            reasoning=reasoning,
            confidence=confidence,
            next_steps=next_steps
        )
