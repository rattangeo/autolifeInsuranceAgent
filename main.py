"""
Main entry point for the Insurance Claims Processing Agent.
Provides CLI interface for testing the agent locally.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from src.agent import ClaimsProcessingAgent
from src.models import Claim, ClaimStatus
from src.utils import logger, settings


console = Console()


def load_sample_claims() -> list[dict]:
    """Load sample claims from JSON file."""
    claims_path = Path(__file__).parent / "src" / "data" / "sample_claims.json"
    with open(claims_path, 'r') as f:
        return json.load(f)


def display_claim_report(claim: Claim) -> None:
    """Display formatted claim processing report."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Insurance Claim Processing Report[/bold cyan]",
        border_style="cyan"
    ))
    
    report = claim.to_report()
    
    # Claim Summary Table
    summary_table = Table(title="Claim Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Field", style="cyan", width=20)
    summary_table.add_column("Value", style="white")
    
    for key, value in report['claim_summary'].items():
        summary_table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(summary_table)
    
    # Decision Table
    decision_table = Table(title="Decision", show_header=True, header_style="bold yellow")
    decision_table.add_column("Field", style="cyan", width=20)
    decision_table.add_column("Value", style="white")
    
    # Color code status
    status = report['decision']['status']
    if status == 'approved':
        status_display = f"[bold green]{status.upper()}[/bold green]"
    elif status == 'denied':
        status_display = f"[bold red]{status.upper()}[/bold red]"
    else:
        status_display = f"[bold yellow]{status.upper()}[/bold yellow]"
    
    decision_table.add_row("Status", status_display)
    decision_table.add_row("Approved Amount", report['decision']['approved_amount'])
    decision_table.add_row("Confidence", report['decision']['confidence'])
    decision_table.add_row("Fraud Risk", report['fraud_risk'])
    
    console.print(decision_table)
    
    # Reasoning
    console.print()
    console.print(Panel(
        report['reasoning'],
        title="[bold]Reasoning[/bold]",
        border_style="blue"
    ))
    
    # Next Steps
    if report['next_steps']:
        console.print()
        console.print("[bold cyan]Next Steps:[/bold cyan]")
        for i, step in enumerate(report['next_steps'], 1):
            console.print(f"  {i}. {step}")
    
    # Processing Log
    if claim.processing_log:
        console.print()
        console.print("[bold cyan]Processing Log:[/bold cyan]")
        for log_entry in claim.processing_log[-5:]:  # Show last 5 entries
            console.print(f"  [dim]{log_entry}[/dim]")
    
    console.print()


async def process_claim_interactive(agent: ClaimsProcessingAgent) -> None:
    """Interactive mode for processing claims."""
    console.print()
    console.print(Panel.fit(
        "[bold green]Interactive Claims Processing Mode[/bold green]\n"
        "Enter claim details or type 'quit' to exit",
        border_style="green"
    ))
    
    while True:
        console.print()
        claim_text = console.input("[bold cyan]Enter claim text (or 'quit'):[/bold cyan] ")
        
        if claim_text.lower() in ['quit', 'exit', 'q']:
            console.print("[yellow]Exiting...[/yellow]")
            break
        
        if not claim_text.strip():
            console.print("[red]Please enter claim text[/red]")
            continue
        
        console.print()
        with console.status("[bold green]Processing claim...[/bold green]", spinner="dots"):
            claim = await agent.process_claim(claim_text)
        
        display_claim_report(claim)


async def process_sample_claim(agent: ClaimsProcessingAgent, claim_id: Optional[int] = None) -> None:
    """Process a sample claim by ID."""
    sample_claims = load_sample_claims()
    
    if claim_id is None:
        # Show menu
        console.print()
        console.print("[bold cyan]Sample Claims:[/bold cyan]")
        for claim in sample_claims:
            console.print(f"  {claim['id']}. {claim['name']} - {claim['description']}")
        
        console.print()
        claim_id = int(console.input("[bold cyan]Select claim ID:[/bold cyan] "))
    
    # Find claim
    selected = next((c for c in sample_claims if c['id'] == claim_id), None)
    
    if not selected:
        console.print(f"[red]Claim ID {claim_id} not found[/red]")
        return
    
    console.print()
    console.print(f"[bold cyan]Processing:[/bold cyan] {selected['name']}")
    console.print(f"[dim]{selected['description']}[/dim]")
    
    console.print()
    with console.status("[bold green]Agent is analyzing...[/bold green]", spinner="dots"):
        claim = await agent.process_claim(selected['claim_text'])
    
    display_claim_report(claim)


async def process_custom_claim(agent: ClaimsProcessingAgent, claim_text: str) -> None:
    """Process a custom claim text."""
    console.print()
    console.print("[bold cyan]Processing custom claim...[/bold cyan]")
    
    console.print()
    with console.status("[bold green]Agent is analyzing...[/bold green]", spinner="dots"):
        claim = await agent.process_claim(claim_text)
    
    display_claim_report(claim)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Insurance Claims Processing Agent - Autonomous AI-powered claims analysis"
    )
    parser.add_argument(
        '--claim',
        type=str,
        help='Custom claim text to process'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Process sample claim by ID (1-6)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--list-samples',
        action='store_true',
        help='List all sample claims'
    )
    
    args = parser.parse_args()
    
    # Display banner
    console.print()
    console.print(Panel.fit(
        "[bold blue]Insurance Claims Processing Agent[/bold blue]\n"
        "[cyan]Autonomous LLM-Driven Claims Analysis[/cyan]\n"
        "[dim]Powered by Azure OpenAI & Semantic Kernel[/dim]",
        border_style="blue"
    ))
    
    # List samples if requested
    if args.list_samples:
        sample_claims = load_sample_claims()
        console.print()
        console.print("[bold cyan]Available Sample Claims:[/bold cyan]")
        for claim in sample_claims:
            console.print(f"\n[bold]{claim['id']}. {claim['name']}[/bold]")
            console.print(f"   [dim]{claim['description']}[/dim]")
        console.print()
        return
    
    # Initialize agent
    policies_path = Path(__file__).parent / "src" / "data" / "policies.json"
    
    try:
        console.print()
        with console.status("[bold green]Initializing agent...[/bold green]", spinner="dots"):
            agent = ClaimsProcessingAgent(policies_path)
        
        console.print("[green]✓[/green] Agent initialized successfully")
        
        # Route to appropriate mode
        if args.interactive:
            await process_claim_interactive(agent)
        elif args.claim:
            await process_custom_claim(agent, args.claim)
        elif args.sample:
            await process_sample_claim(agent, args.sample)
        else:
            # Default: process sample claim with menu
            await process_sample_claim(agent)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
        logger.exception("Error in main")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
