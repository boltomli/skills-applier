"""Interactive mode for the CLI."""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class SessionState:
    """State for an interactive session."""
    
    conversation_history: list[dict]
    current_problem: Optional[str]
    recommended_skills: list[Any]
    generated_code: Optional[str]
    user_preferences: Dict[str, Any]
    
    def __init__(self):
        self.conversation_history = []
        self.current_problem = None
        self.recommended_skills = []
        self.generated_code = None
        self.user_preferences = {}


class InteractiveMode:
    """Interactive mode for user conversations."""
    
    def __init__(self):
        """Initialize interactive mode."""
        self.state = SessionState()
        self.running = False
    
    async def start(self):
        """Start interactive session."""
        self.running = True
        
        console.print(Panel(
            "[bold cyan]Stats Solver - Interactive Mode[/bold cyan]\n\n"
            "Type your problem description to get started.\n"
            "Commands: [bold]/help[/bold], [bold]/quit[/bold], [bold]/clear[/bold]",
            title="Welcome",
            border_style="cyan"
        ))
        
        while self.running:
            try:
                await self.process_input()
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                console.print(f"[red]Error: {e}[/red]")
    
    async def process_input(self):
        """Process user input."""
        user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]", default="")
        
        if not user_input.strip():
            return
        
        # Handle commands
        if user_input.startswith("/"):
            await self.handle_command(user_input)
            return
        
        # Add to conversation history
        self.state.conversation_history.append({"role": "user", "content": user_input})
        
        # Process the input
        await self.handle_query(user_input)
    
    async def handle_command(self, command: str):
        """Handle special commands.
        
        Args:
            command: Command string starting with /
        """
        cmd = command.lower().strip()
        
        if cmd == "/quit" or cmd == "/exit":
            self.running = False
            console.print("[green]Goodbye![/green]")
        
        elif cmd == "/help":
            self.show_help()
        
        elif cmd == "/clear":
            self.state = SessionState()
            console.print("[yellow]Session cleared.[/yellow]")
        
        elif cmd == "/history":
            self.show_history()
        
        elif cmd == "/status":
            self.show_status()
        
        elif cmd.startswith("/set"):
            await self.handle_set_command(cmd)
        
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("Type /help for available commands.")
    
    def show_help(self):
        """Show help information."""
        help_text = """
# Available Commands

- **/quit** - Exit interactive mode
- **/help** - Show this help message
- **/clear** - Clear conversation history
- **/history** - Show conversation history
- **/status** - Show current session status
- **/set KEY=VALUE** - Set a preference

# Getting Started

Simply describe your data analysis problem, for example:
- "I have test scores from two classes and want to know if there's a significant difference"
- "I need to predict sales based on historical data"
- "I want to understand the distribution of my data"
"""
        
        console.print(Panel(Markdown(help_text), title="Help", border_style="cyan"))
    
    def show_history(self):
        """Show conversation history."""
        if not self.state.conversation_history:
            console.print("[yellow]No conversation history.[/yellow]")
            return
        
        console.print("\n[bold cyan]Conversation History:[/bold cyan]\n")
        
        for i, msg in enumerate(self.state.conversation_history, 1):
            role = msg["role"]
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            
            if role == "user":
                console.print(f"[cyan]{i}. You:[/cyan] {content}")
            else:
                console.print(f"[green]{i}. Assistant:[/green] {content}")
    
    def show_status(self):
        """Show current session status."""
        console.print("\n[bold cyan]Session Status:[/bold cyan]\n")
        
        status_items = [
            ("Current Problem", self.state.current_problem or "None"),
            ("Recommended Skills", str(len(self.state.recommended_skills))),
            ("Generated Code", "Yes" if self.state.generated_code else "No"),
            ("Conversation Turns", str(len(self.state.conversation_history))),
        ]
        
        table = Table(show_header=False)
        table.add_column("Item", style="cyan")
        table.add_column("Value")
        
        for item, value in status_items:
            table.add_row(item, value)
        
        console.print(table)
    
    async def handle_set_command(self, command: str):
        """Handle /set command.
        
        Args:
            command: Command string
        """
        parts = command.split(None, 1)
        if len(parts) < 2:
            console.print("[yellow]Usage: /set KEY=VALUE[/yellow]")
            return
        
        kv = parts[1]
        if "=" not in kv:
            console.print("[yellow]Usage: /set KEY=VALUE[/yellow]")
            return
        
        key, value = kv.split("=", 1)
        self.state.user_preferences[key] = value
        console.print(f"[green]Set {key} = {value}[/green]")
    
    async def handle_query(self, query: str):
        """Handle user query.
        
        Args:
            query: User's question/problem description
        """
        # Store current problem
        self.state.current_problem = query
        
        console.print("\n[bold yellow]Analyzing your problem...[/bold yellow]")
        
        # This will be integrated with the full analysis pipeline
        # For now, show a placeholder response
        response = self._generate_placeholder_response(query)
        
        console.print(Panel(
            response,
            title="Analysis Result",
            border_style="green"
        ))
        
        # Add to history
        self.state.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Offer follow-up actions
        await self.offer_followup()
    
    def _generate_placeholder_response(self, query: str) -> str:
        """Generate a placeholder response.
        
        Args:
            query: User query
            
        Returns:
            Response text
        """
        return f"""
Based on your problem: "{query[:100]}{'...' if len(query) > 100 else ''}"

I've identified the following:

**Problem Type**: Statistical Analysis
**Data Types**: Numerical (inferred)
**Suggested Approach**: Comparative analysis

**Recommended Skills**:
1. Two-sample t-test (for comparing means)
2. Descriptive statistics (for understanding distributions)
3. Visualization (for displaying results)

*Full recommendation coming soon with complete integration!*
"""
    
    async def offer_followup(self):
        """Offer follow-up actions to the user."""
        console.print("\n[bold cyan]What would you like to do next?[/bold cyan]")
        console.print("  [1] Generate code for the recommended solution")
        console.print("  [2] See alternative approaches")
        console.print("  [3] Refine your problem description")
        console.print("  [4] Ask a follow-up question")
        console.print("  [5] Continue with new problem")
        
        choice = Prompt.ask(
            "\n[cyan]Select an option[/cyan]",
            choices=["1", "2", "3", "4", "5"],
            default="5"
        )
        
        if choice == "1":
            console.print("[yellow]Code generation coming soon![/yellow]")
        elif choice == "2":
            console.print("[yellow]Alternative suggestions coming soon![/yellow]")
        elif choice == "3":
            new_desc = Prompt.ask("\n[cyan]Refined problem description[/cyan]")
            await self.handle_query(new_desc)
        elif choice == "4":
            followup = Prompt.ask("\n[cyan]Your follow-up question[/cyan]")
            await self.handle_query(f"{self.state.current_problem}\n\n{followup}")
        elif choice == "5":
            console.print("[cyan]Ready for your next problem![/cyan]")
            self.state.current_problem = None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the current session.
        
        Returns:
            Session summary dictionary
        """
        return {
            "total_turns": len(self.state.conversation_history),
            "current_problem": self.state.current_problem,
            "skills_recommended": len(self.state.recommended_skills),
            "code_generated": self.state.generated_code is not None,
            "preferences": self.state.user_preferences,
        }