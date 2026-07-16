#!/usr/bin/env python3
"""
Sentinel-RAG Demo Script

Demonstrates:
1. The vulnerability of standard RAG to indirect prompt injection
2. How Sentinel detects and neutralizes attacks
3. Comparison between protected and unprotected responses
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from main import SentinelRAG


console = Console()


def demo_vulnerability():
    """Demonstrate the indirect prompt injection vulnerability"""
    console.print("\n" + "="*60)
    console.print("[bold red]DEMO 1: Demonstrating the Vulnerability[/bold red]")
    console.print("="*60 + "\n")
    
    # Initialize system
    console.print("[yellow]Initializing Sentinel-RAG system...[/yellow]\n")
    system = SentinelRAG(
        persist_directory="./data/demo_embeddings",
        sentinel_enabled=False  # Start with Sentinel OFF to show vulnerability
    )
    
    # Ingest poisoned documents
    console.print("[yellow]Ingesting poisoned documents...[/yellow]")
    chunks = system.ingest("./data/poisoned")
    console.print(f"[green]Ingested {chunks} chunks[/green]\n")
    
    # Query without protection
    console.print("[bold]Query:[/bold] Summarize the candidate's qualifications")
    console.print("[red]⚠️  Sentinel: DISABLED[/red]\n")
    
    result = system.query("Summarize the candidate's qualifications from the resume")
    
    console.print(Panel(
        result.response,
        title="[red]UNPROTECTED Response[/red]",
        border_style="red"
    ))
    
    # Show what was retrieved
    console.print("\n[bold]Retrieved chunks (containing hidden attack):[/bold]")
    for i, chunk in enumerate(result.retrieval.chunks[:2]):
        console.print(f"\n[dim]Chunk {i+1}:[/dim]")
        console.print(chunk[:500] + "..." if len(chunk) > 500 else chunk)
    
    return system


def demo_protection(system: SentinelRAG):
    """Demonstrate Sentinel protection"""
    console.print("\n" + "="*60)
    console.print("[bold green]DEMO 2: Sentinel Protection Active[/bold green]")
    console.print("="*60 + "\n")
    
    # Enable Sentinel
    system.enable_sentinel()
    console.print("[green]✓ Sentinel: ENABLED[/green]\n")
    
    # Same query, now protected
    console.print("[bold]Query:[/bold] Summarize the candidate's qualifications")
    
    result = system.query("Summarize the candidate's qualifications from the resume")
    
    console.print(Panel(
        result.response,
        title="[green]PROTECTED Response[/green]",
        border_style="green"
    ))
    
    # Show Sentinel activity
    console.print(f"\n[bold]Sentinel Report:[/bold]")
    console.print(f"  Threats detected: {result.threats_detected}")
    console.print(f"  Threats neutralized: {result.threats_neutralized}")
    
    # Show what Sentinel did
    for i, sr in enumerate(result.sentinel_results):
        if sr.was_threat:
            console.print(f"\n[yellow]Threat {i+1}:[/yellow]")
            console.print(f"  Level: {sr.threat_level.value}")
            console.print(f"  Confidence: {sr.confidence:.2f}")
            if sr.neutralization_result:
                console.print(f"\n  [red]Original:[/red] {sr.original_text[:200]}...")
                console.print(f"\n  [green]Neutralized:[/green] {sr.neutralization_result.neutralized_text[:200]}...")


def demo_comparison(system: SentinelRAG):
    """Side-by-side comparison"""
    console.print("\n" + "="*60)
    console.print("[bold blue]DEMO 3: Side-by-Side Comparison[/bold blue]")
    console.print("="*60 + "\n")
    
    comparison = system.compare("What does the policy document say about security?")
    
    table = Table(title="Response Comparison")
    table.add_column("Unprotected", style="red", width=40)
    table.add_column("Protected", style="green", width=40)
    
    table.add_row(
        comparison["unsafe_response"][:300] + "...",
        comparison["safe_response"][:300] + "..."
    )
    
    console.print(table)
    console.print(f"\n[bold]Analysis:[/bold] {comparison['analysis']}")


def main():
    """Run the complete demo"""
    console.print(Panel.fit(
        "[bold]Sentinel-RAG: Indirect Prompt Injection Defense Demo[/bold]\n\n"
        "This demo shows how malicious content hidden in documents\n"
        "can hijack LLM responses, and how Sentinel neutralizes these attacks.",
        border_style="blue"
    ))
    
    try:
        # Demo 1: Show vulnerability
        system = demo_vulnerability()
        
        input("\n[Press Enter to continue to protection demo...]\n")
        
        # Demo 2: Show protection
        demo_protection(system)
        
        input("\n[Press Enter to continue to comparison...]\n")
        
        # Demo 3: Comparison
        demo_comparison(system)
        
        # Final summary
        console.print("\n" + "="*60)
        console.print(system.get_sentinel_summary())
        console.print("="*60)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Make sure Ollama is running: ollama serve[/dim]")
        raise


if __name__ == "__main__":
    main()
