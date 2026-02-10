"""Display utilities for CLI output."""

import logging
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from rich.syntax import Syntax

from ..recommendation.scorer import Recommendation
from ..recommendation.matcher import MatchResult
from ..recommendation.chain_builder import SkillChain
from ..recommendation.alternatives import AlternativeSet

logger = logging.getLogger(__name__)
console = Console()


class RecommendationDisplay:
    """Display utilities for recommendation results."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize display.

        Args:
            console: Console instance (uses default if None)
        """
        self.console = console or Console()

    def show_recommendations(
        self, recommendations: List[Recommendation], show_details: bool = False
    ):
        """Display recommendations.

        Args:
            recommendations: List of recommendations
            show_details: Whether to show detailed information
        """
        if not recommendations:
            self.console.print("[yellow]No recommendations found.[/yellow]")
            return

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="cyan", width=6)
        table.add_column("Skill", style="green")
        table.add_column("Score", style="yellow")
        table.add_column("Match", style="blue")
        table.add_column("Confidence", style="white")

        for rec in recommendations:
            table.add_row(
                str(rec.ranking_position),
                rec.skill.name,
                f"{rec.final_score:.2f}",
                f"{rec.match_score:.2f}",
                f"{rec.confidence:.2f}",
            )

        self.console.print("\n[bold cyan]Recommendations[/bold cyan]\n")
        self.console.print(table)

        if show_details:
            self.show_recommendation_details(recommendations[0])

    def show_recommendation_details(self, recommendation: Recommendation):
        """Show detailed information about a recommendation.

        Args:
            recommendation: Recommendation to display
        """
        panel_content = f"""
[bold green]Skill:[/bold green] {recommendation.skill.name}
[bold cyan]ID:[/bold cyan] {recommendation.skill.id}
[bold cyan]Category:[/bold cyan] {recommendation.skill.category.value}

[bold]Scores:[/bold]
  Final Score: {recommendation.final_score:.2f}
  Match Score: {recommendation.match_score:.2f}
  Confidence: {recommendation.confidence:.2f}

[bold]Description:[/bold]
{recommendation.skill.description}
"""

        if recommendation.skill.long_description:
            panel_content += (
                f"\n[bold]Extended Description:[/bold]\n{recommendation.skill.long_description}\n"
            )

        if recommendation.match_reasons:
            panel_content += "\n[bold]Match Reasons:[/bold]\n"
            for reason in recommendation.match_reasons:
                panel_content += f"  • {reason}\n"

        if recommendation.mismatches:
            panel_content += "\n[bold red]Potential Issues:[/bold red]\n"
            for mismatch in recommendation.mismatches:
                panel_content += f"  • {mismatch}\n"

        if recommendation.skill.tags:
            panel_content += f"\n[bold]Tags:[/bold] {', '.join(recommendation.skill.tags)}\n"

        if recommendation.skill.assumptions:
            panel_content += "\n[bold]Assumptions:[/bold]\n"
            for assumption in recommendation.skill.assumptions:
                panel_content += f"  • {assumption}\n"

        self.console.print(
            Panel(panel_content, title="Recommendation Details", border_style="cyan")
        )

    def show_match_results(self, match_results: List[MatchResult]):
        """Show match results.

        Args:
            match_results: List of match results
        """
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Skill", style="green")
        table.add_column("Score", style="yellow")
        table.add_column("Confidence", style="white")
        table.add_column("Matches", style="blue")

        for result in match_results:
            table.add_row(
                result.skill.name,
                f"{result.score:.2f}",
                f"{result.confidence:.2f}",
                str(len(result.match_reasons)),
            )

        self.console.print("\n[bold cyan]Match Results[/bold cyan]\n")
        self.console.print(table)

    def show_skill_chain(self, chain: SkillChain):
        """Display a skill chain.

        Args:
            chain: Skill chain to display
        """
        tree = Tree(f"[bold cyan]{chain.name}[/bold cyan]")

        tree.add(f"[dim]Duration: {chain.estimated_duration}[/dim]")
        tree.add(f"[dim]Steps: {chain.total_steps}[/dim]")
        tree.add(f"[dim]Confidence: {chain.confidence:.2f}[/dim]")

        steps_branch = tree.add("[bold]Analysis Steps[/bold]")

        for step in chain.steps:
            step_text = f"[{step.step_type.value}]{step.order}. {step.skill.name}"
            if step.depends_on:
                step_text += f" [dim](depends on: {', '.join(step.depends_on)})[/dim]"
            steps_branch.add(step_text)

        self.console.print("\n[bold cyan]Analysis Workflow[/bold cyan]\n")
        self.console.print(tree)

    def show_alternatives(self, alternative_set: AlternativeSet):
        """Display alternative solutions.

        Args:
            alternative_set: Set of alternatives
        """
        # Primary recommendation
        self.console.print(
            f"\n[bold cyan]Primary Recommendation:[/bold cyan] {alternative_set.primary_recommendation.name}"
        )

        # Alternatives
        if alternative_set.alternatives:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Alternative", style="green")
            table.add_column("Type", style="yellow")
            table.add_column("Similarity", style="blue")
            table.add_column("When to Use", style="white")

            for alt in alternative_set.alternatives:
                when_to_use = ", ".join(alt.use_when[:2]) if alt.use_when else "N/A"
                table.add_row(
                    alt.skill.name,
                    alt.alternative_type.value,
                    f"{alt.similarity_score:.2f}",
                    when_to_use,
                )

            self.console.print("\n[bold cyan]Alternative Approaches[/bold cyan]\n")
            self.console.print(table)

        # Reasoning
        if alternative_set.reasoning:
            self.console.print(f"\n[dim]{alternative_set.reasoning}[/dim]\n")

    def show_code(self, code: str, language: str = "python"):
        """Display code with syntax highlighting.

        Args:
            code: Code to display
            language: Programming language
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title="Generated Code", border_style="cyan"))

    def show_comparison(self, recommendations: List[Recommendation]):
        """Show comparison between recommendations.

        Args:
            recommendations: Recommendations to compare
        """
        if len(recommendations) < 2:
            self.console.print("[yellow]Need at least 2 recommendations to compare.[/yellow]")
            return

        # Create comparison panels
        panels = []

        for rec in recommendations[:3]:  # Limit to 3 for display
            content = f"""
[bold green]{rec.skill.name}[/bold green]

Score: {rec.final_score:.2f}
Match: {rec.match_score:.2f}
Confidence: {rec.confidence:.2f}

{rec.skill.description}
"""
            panel = Panel(content, border_style="cyan")
            panels.append(panel)

        columns = Columns(panels)
        self.console.print("\n[bold cyan]Comparison[/bold cyan]\n")
        self.console.print(columns)

    def show_problem_analysis(
        self, problem_summary: str, problem_type: str, data_types: List[str], constraints: List[str]
    ):
        """Display problem analysis results.

        Args:
            problem_summary: Problem summary
            problem_type: Problem type
            data_types: Data types involved
            constraints: Constraints identified
        """
        panel_content = f"""
[bold green]Problem Summary:[/bold green]
{problem_summary}

[bold cyan]Problem Type:[/bold cyan] {problem_type}

[bold cyan]Data Types:[/bold cyan] {', '.join(data_types)}
"""

        if constraints:
            panel_content += "\n[bold yellow]Constraints:[/bold yellow]\n"
            for constraint in constraints:
                panel_content += f"  • {constraint}\n"

        self.console.print(Panel(panel_content, title="Problem Analysis", border_style="cyan"))

    def show_progress(self, current: int, total: int, message: str):
        """Show progress indicator.

        Args:
            current: Current step
            total: Total steps
            message: Progress message
        """
        percent = (current / total) * 100
        bar_width = 40
        filled = int(bar_width * current / total)
        bar = "█" * filled + "░" * (bar_width - filled)

        self.console.print(
            f"\r[cyan]{message}[/cyan] [{bar}] {current}/{total} ({percent:.1f}%)", end=""
        )
        self.console.print()

    def show_error(self, message: str, details: Optional[str] = None):
        """Display error message.

        Args:
            message: Error message
            details: Optional error details
        """
        panel_content = f"[bold red]Error:[/bold red] {message}"

        if details:
            panel_content += f"\n\n[dim]{details}[/dim]"

        self.console.print(Panel(panel_content, title="Error", border_style="red"))

    def show_success(self, message: str):
        """Display success message.

        Args:
            message: Success message
        """
        self.console.print(f"[green]✓[/green] {message}")

    def show_warning(self, message: str):
        """Display warning message.

        Args:
            message: Warning message
        """
        self.console.print(f"[yellow]⚠[/yellow] {message}")
