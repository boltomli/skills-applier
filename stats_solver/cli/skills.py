"""Skills browsing and management commands."""

import logging
from typing import List, Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from ..skills.metadata_schema import SkillMetadata, SkillCategory
from ..skills.index import SkillIndex

logger = logging.getLogger(__name__)
console = Console()


class SkillsBrowser:
    """Browser for viewing and managing skills."""

    def __init__(self, skill_index: Optional[SkillIndex] = None):
        """Initialize skills browser.

        Args:
            skill_index: Skill index to browse
        """
        self.skill_index = skill_index or SkillIndex()
        self.index_loaded = False

    async def load_index(self, force_reload: bool = False) -> bool:
        """Load the skill index.

        Args:
            force_reload: Force reload even if already loaded

        Returns:
            True if successful
        """
        if self.index_loaded and not force_reload:
            return True

        try:
            await self.skill_index.load()
            self.index_loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load skill index: {e}")
            return False

    def list_all(
        self, category: Optional[SkillCategory] = None, tag: Optional[str] = None, limit: int = 50
    ) -> List[SkillMetadata]:
        """List skills with optional filtering.

        Args:
            category: Filter by category
            tag: Filter by tag
            limit: Maximum number of results

        Returns:
            List of skills
        """
        skills = self.skill_index.get_all_skills()

        # Filter by category
        if category:
            skills = [s for s in skills if s.category == category]

        # Filter by tag
        if tag:
            skills = [s for s in skills if tag in s.tags]

        # Limit results
        return skills[:limit]

    def search(self, query: str, limit: int = 50) -> List[SkillMetadata]:
        """Search skills by query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching skills
        """
        return self.skill_index.search(query)[:limit]

    def display_skills(self, skills: List[SkillMetadata], show_details: bool = False):
        """Display skills in a table.

        Args:
            skills: Skills to display
            show_details: Whether to show detailed information
        """
        if not skills:
            console.print("[yellow]No skills found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=20)
        table.add_column("Name", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Tags", style="blue")

        for skill in skills:
            tags_str = ", ".join(skill.tags[:3]) if skill.tags else ""
            if len(skill.tags) > 3:
                tags_str += "..."

            table.add_row(
                skill.id,
                skill.name,
                skill.category.value,
                tags_str,
            )

        console.print("\n[bold cyan]Skills[/bold cyan]\n")
        console.print(table)

        if show_details and skills:
            self.display_skill_details(skills[0])

    def display_skill_details(self, skill: SkillMetadata):
        """Display detailed information about a skill.

        Args:
            skill: Skill to display
        """
        panel_content = f"""
[bold green]Name:[/bold green] {skill.name}
[bold cyan]ID:[/bold cyan] {skill.id}
[bold cyan]Category:[/bold cyan] {skill.category.value}
[bold cyan]Path:[/bold cyan] {skill.path}

[bold]Description:[/bold]
{skill.description}
"""

        if skill.long_description:
            panel_content += f"\n[bold]Extended Description:[/bold]\n{skill.long_description}\n"

        if skill.tags:
            panel_content += f"\n[bold]Tags:[/bold] {', '.join(skill.tags)}\n"

        if skill.input_data_types:
            panel_content += f"\n[bold]Input Data Types:[/bold] {', '.join(dt.value for dt in skill.input_data_types)}\n"

        if skill.output_format:
            panel_content += f"\n[bold]Output Format:[/bold] {skill.output_format}\n"

        if skill.statistical_concept:
            panel_content += f"\n[bold]Statistical Concept:[/bold] {skill.statistical_concept}\n"

        if skill.assumptions:
            panel_content += "\n[bold]Assumptions:[/bold]\n"
            for assumption in skill.assumptions:
                panel_content += f"  • {assumption}\n"

        if skill.dependencies:
            panel_content += f"\n[bold]Dependencies:[/bold] {', '.join(skill.dependencies)}\n"

        if skill.use_cases:
            panel_content += "\n[bold]Use Cases:[/bold]\n"
            for use_case in skill.use_cases:
                panel_content += f"  • {use_case}\n"

        panel_content += f"\n[dim]Confidence: {skill.confidence:.2f}[/dim]"
        panel_content += f"\n[dim]Source: {skill.source}[/dim]"

        console.print(Panel(panel_content, title="Skill Details", border_style="cyan"))

    def display_categories(self):
        """Display skill categories with counts."""
        stats = self.skill_index.get_statistics()
        categories = stats.get("categories", {})

        tree = Tree("[bold cyan]Skill Categories[/bold cyan]")

        for category, count in categories.items():
            tree.add(f"[green]{category}[/green]: {count} skills")

        console.print("\n")
        console.print(tree)

    def display_tags(self, limit: int = 20):
        """Display most common tags.

        Args:
            limit: Maximum number of tags to display
        """
        tags = self.skill_index.get_top_tags(limit)

        if not tags:
            console.print("[yellow]No tags found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tag", style="cyan")
        table.add_column("Count", style="yellow")

        for tag, count in tags:
            table.add_row(tag, str(count))

        console.print("\n[bold cyan]Top Tags[/bold cyan]\n")
        console.print(table)

    def display_dependencies(self):
        """Display dependency summary."""
        deps = self.skill_index.get_dependencies_summary()

        if not deps:
            console.print("[yellow]No dependencies found.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Dependency", style="cyan")
        table.add_column("Skills Using", style="yellow")

        for dep, count in list(deps.items())[:20]:
            table.add_row(dep, str(count))

        console.print("\n[bold cyan]Common Dependencies[/bold cyan]\n")
        console.print(table)

    def display_statistics(self):
        """Display skill index statistics."""
        stats = self.skill_index.get_statistics()

        panel_content = f"""
[bold green]Total Skills:[/bold green] {stats['total_skills']}
[bold cyan]Last Updated:[/bold cyan] {stats.get('last_updated', 'Never')}

[bold]Categories:[/bold]
"""

        for category, count in stats.get("categories", {}).items():
            panel_content += f"  • {category}: {count}\n"

        console.print(Panel(panel_content, title="Skill Statistics", border_style="cyan"))

    def get_skill_by_id(self, skill_id: str) -> Optional[SkillMetadata]:
        """Get a skill by ID.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill metadata or None
        """
        return self.skill_index.get_skill(skill_id)

    def get_skills_by_category(self, category: SkillCategory) -> List[SkillMetadata]:
        """Get all skills in a category.

        Args:
            category: Skill category

        Returns:
            List of skills
        """
        return self.skill_index.get_by_category(category)

    def get_skills_by_tag(self, tag: str) -> List[SkillMetadata]:
        """Get all skills with a tag.

        Args:
            tag: Tag to search for

        Returns:
            List of skills
        """
        return self.skill_index.get_by_tag(tag)

    def export_skills(
        self, output_file: Path, skills: Optional[List[SkillMetadata]] = None
    ) -> bool:
        """Export skills to a file.

        Args:
            output_file: Output file path
            skills: Skills to export (exports all if None)

        Returns:
            True if successful
        """
        import json

        if skills is None:
            skills = self.skill_index.get_all_skills()

        try:
            data = {
                "skills": [skill.model_dump() for skill in skills],
                "total": len(skills),
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            console.print(
                f"[green]✓[/green] Exported {len(skills)} skills to [cyan]{output_file}[/cyan]"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to export skills: {e}")
            return False
