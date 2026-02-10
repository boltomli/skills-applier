"""Main CLI entry point for stats_solver."""

import logging
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .. import setup_logging
from ..llm.manager import LLMManager

# Initialize components
logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer(
    name="stats-solver",
    help="Intelligent statistics method recommendation system powered by local LLM",
    add_completion=False,
)

# Global state
llm_manager: Optional[LLMManager] = None


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Stats Solver - Intelligent statistics method recommendation."""
    # Setup logging
    log_level = "DEBUG" if debug else "INFO" if verbose else "WARNING"
    setup_logging(log_level)
    
    logger.debug("Stats solver initialized")


@app.command()
def analyze(
    problem: str = typer.Argument(..., help="Problem description to analyze"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Analyze a problem and recommend statistical methods."""
    console.print(f"[bold cyan]Analyzing problem:[/bold cyan] {problem}")
    
    # This will be implemented with full integration
    console.print("\n[yellow]Analysis feature coming soon![/yellow]")
    console.print("This will analyze your problem and recommend appropriate statistical methods.")


@app.command()
def recommend(
    query: str = typer.Argument(..., help="Query for skill recommendations"),
    top_k: int = typer.Option(5, "--top", "-k", help="Number of recommendations"),
):
    """Get skill recommendations for a query."""
    console.print(f"[bold cyan]Searching for:[/bold cyan] {query}")
    console.print(f"[dim]Top {top_k} recommendations[/dim]")
    
    # This will be implemented with full integration
    console.print("\n[yellow]Recommendation feature coming soon![/yellow]")
    console.print("This will search the skill index and recommend relevant skills.")


@app.command()
def generate(
    skill_id: str = typer.Argument(..., help="Skill ID to generate code for"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate Python code for a skill."""
    console.print(f"[bold cyan]Generating code for:[/bold cyan] {skill_id}")
    
    # This will be implemented with full integration
    console.print("\n[yellow]Code generation feature coming soon![/yellow]")
    console.print("This will generate Python code for the specified skill.")


@app.command()
def interactive():
    """Start interactive mode."""
    console.print("[bold green]Starting interactive mode...[/bold green]")
    console.print("\n[yellow]Interactive mode coming soon![/yellow]")
    console.print("This will launch an interactive session for exploring problems and solutions.")


@app.command()
def status():
    """Show system status and configuration."""
    console.print("[bold cyan]System Status[/bold cyan]\n")
    
    # Create status table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    table.add_row("LLM Integration", "Pending", "Not initialized")
    table.add_row("Skill Index", "Pending", "Not loaded")
    table.add_row("Recommendation Engine", "Ready", "Available")
    table.add_row("Code Generator", "Ready", "Available")
    
    console.print(table)
    console.print("\n[dim]Use 'stats-solver init' to initialize the system.[/dim]")


@app.command()
def init():
    """Initialize the system (scan skills, connect to LLM)."""
    console.print("[bold cyan]Initializing Stats Solver...[/bold cyan]\n")
    
    # Initialize LLM manager
    global llm_manager
    try:
        llm_manager = LLMManager.from_env()
        initialized = await llm_manager.initialize()
        
        if initialized:
            console.print("[green]✓[/green] LLM manager initialized")
            health = await llm_manager.health_check()
            
            if health["available"]:
                console.print(f"[green]✓[/green] Connected to {health['provider']}")
                console.print(f"  Model: {health['model']}")
                console.print(f"  Available models: {health['models_count']}")
            else:
                console.print(f"[yellow]![/yellow] LLM not available: {health.get('error', 'Unknown error')}")
        else:
            console.print("[red]✗[/red] Failed to initialize LLM manager")
    except Exception as e:
        console.print(f"[red]✗[/red] LLM initialization error: {e}")
    
    # Scan skills
    console.print("\n[cyan]Scanning skills...[/cyan]")
    # This will be implemented with full integration
    console.print("[yellow]![/yellow] Skill scanning coming soon")
    
    console.print("\n[green]Initialization complete![/green]")


@app.command()
def skills(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search term"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
):
    """Browse available skills."""
    console.print("[bold cyan]Available Skills[/bold cyan]\n")
    
    # This will be implemented with full integration
    console.print("[yellow]Skill browser coming soon![/yellow]")
    console.print("This will display and filter available statistical and mathematical skills.")


@app.command()
def config(
    list_: bool = typer.Option(False, "--list", "-l", help="List configuration"),
    set_: Optional[str] = typer.Option(None, "--set", "-s", help="Set configuration (KEY=VALUE)"),
):
    """Manage configuration."""
    if list_ or (not set_):
        # List configuration
        console.print("[bold cyan]Current Configuration[/bold cyan]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        table.add_column("Description")
        
        table.add_row("LLM_PROVIDER", "ollama", "LLM provider (ollama, lm_studio)")
        table.add_row("LLM_HOST", "localhost", "LLM server host")
        table.add_row("LLM_PORT", "11434", "LLM server port")
        table.add_row("LLM_MODEL", "llama3", "Default LLM model")
        table.add_row("LOG_LEVEL", "INFO", "Logging level")
        
        console.print(table)
    else:
        # Set configuration
        console.print(f"[yellow]Setting configuration:[/yellow] {set_}")
        console.print("[yellow]Configuration update coming soon![/yellow]")


if __name__ == "__main__":
    app()