"""Main CLI entry point for stats_solver."""

import logging

import typer
from rich.console import Console
from rich.table import Table

from .. import setup_logging
from ..llm.manager import LLMManager

# Initialize components
logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer(
    name="skills-applier",
    help="Intelligent statistics method recommendation system powered by local LLM",
    add_completion=False,
)

# Global state
llm_manager: LLMManager | None = None


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
):
    """Skills Applier - Intelligent statistics method recommendation."""
    # Setup logging
    log_level = "DEBUG" if debug else "INFO" if verbose else "WARNING"
    setup_logging(log_level)

    logger.debug("Skills applier initialized")


@app.command()
def solve(
    problem: str = typer.Argument(None, help="Problem description to analyze"),
    method: str = typer.Option(
        "auto", "--method", "-m", help="Method to use (auto, template, llm)"
    ),
    output: str = typer.Option(
        "markdown", "--output", "-o", help="Output format (markdown, json, code)"
    ),
):
    """Get recommendations and generate solutions."""
    if problem is None:
        console.print("[bold cyan]Describe your data problem:[/bold cyan] ", end="")
        problem = input()

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
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
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
    console.print("\n[dim]Use 'skills-applier init' to initialize the system.[/dim]")


@app.command()
def check():
    """Check LLM connection and system status."""
    import asyncio

    console.print("[bold cyan]Checking LLM connection...[/bold cyan]")
    console.print("[dim]Run 'skills-applier init' first if not initialized.[/dim]\n")

    async def _check():
        global llm_manager
        if llm_manager is None:
            try:
                llm_manager = LLMManager.from_env()
                await llm_manager.initialize()
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to initialize LLM manager: {e}")
                return

        if llm_manager:
            try:
                health = await llm_manager.health_check()

                if health["available"]:
                    console.print("[green]✓[/green] LLM is available")
                    console.print(f"  Provider: {health['provider']}")
                    console.print(f"  Model: {health['model']}")
                    console.print(f"  Available models: {health['models_count']}")
                else:
                    console.print(
                        f"[red]✗[/red] LLM not available: {health.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                console.print(f"[red]✗[/red] Health check failed: {e}")
        else:
            console.print("[yellow]![/yellow] LLM manager not initialized")

    asyncio.run(_check())


@app.command()
def init():
    """Initialize the system (scan skills, connect to LLM)."""
    import asyncio

    console.print("[bold cyan]Initializing Skills Applier...[/bold cyan]\n")

    async def _init():
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
                    console.print(
                        f"[yellow]![/yellow] LLM not available: {health.get('error', 'Unknown error')}"
                    )
            else:
                console.print("[red]✗[/red] Failed to initialize LLM manager")
        except Exception as e:
            console.print(f"[red]✗[/red] LLM initialization error: {e}")

    # Run async initialization
    asyncio.run(_init())

    # Scan skills
    console.print("\n[cyan]Scanning skills...[/cyan]")
    # This will be implemented with full integration
    console.print("[yellow]![/yellow] Skill scanning coming soon")

    console.print("\n[green]Initialization complete![/green]")


@app.command()
def skills(
    action: str = typer.Argument("list", help="Action: list, search, show"),
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    data_type: str | None = typer.Option(None, "--data-type", "-d", help="Filter by data type"),
):
    """Manage and browse skills."""
    if action == "list":
        console.print("[bold cyan]Available Skills[/bold cyan]\n")
        if category:
            console.print(f"[dim]Category: {category}[/dim]\n")
        # This will be implemented with full integration
        console.print("[yellow]Skill browser coming soon![/yellow]")
        console.print("This will display and filter available statistical and mathematical skills.")
    elif action == "search":
        console.print("[bold cyan]Search Skills[/bold cyan]\n")
        if tag:
            console.print(f"[dim]Tag: {tag}[/dim]\n")
        if data_type:
            console.print(f"[dim]Data Type: {data_type}[/dim]\n")
        # This will be implemented with full integration
        console.print("[yellow]Skill search coming soon![/yellow]")
    elif action == "show":
        console.print("[bold cyan]Show Skill Details[/bold cyan]\n")
        console.print("[yellow]Skill details coming soon![/yellow]")
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Use: skills-applier skills [list|search|show] [options]")


@app.command()
def config(
    action: str = typer.Argument("list", help="Action: list, get, set, validate"),
    key: str | None = typer.Argument(None, help="Configuration key"),
    value: str | None = typer.Argument(None, help="Configuration value"),
):
    """Manage configuration."""
    if action == "list" or action == "get" and key is None:
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
    elif action == "get" and key:
        console.print(f"[bold cyan]{key}:[/bold cyan] (Configuration retrieval coming soon)")
    elif action == "set" and key and value:
        console.print(f"[yellow]Setting {key} = {value}[/yellow]")
        console.print("[yellow]Configuration update coming soon![/yellow]")
    elif action == "validate":
        console.print("[bold cyan]Validating configuration...[/bold cyan]")
        console.print("[yellow]Configuration validation coming soon![/yellow]")
    else:
        console.print(f"[red]Unknown or incomplete action: {action}[/red]")
        console.print("Use: skills-applier config [list|get|set|validate] [key] [value]")


if __name__ == "__main__":
    app()
