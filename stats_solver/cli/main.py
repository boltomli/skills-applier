"""Main CLI entry point for stats_solver."""

import logging

import typer
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Confirm

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
    problem: str = typer.Argument(None, help="Problem description to solve"),
    method: str = typer.Option(
        "auto", "--method", "-m", help="Method to use (auto, template, llm)"
    ),
    output: str = typer.Option("file", "--output", "-o", help="Output format (file, stdout)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Generate complete solution code for a problem."""
    import asyncio
    from pathlib import Path

    from ..problem.extractor import ProblemExtractor
    from ..problem.classifier import ProblemClassifier
    from ..problem.data_types import DataTypeDetector
    from ..recommendation.matcher import SkillMatcher
    from ..recommendation.scorer import RecommendationScorer
    from ..skills.index import SkillIndex
    from ..solution.code_generator import CodeGenerator, GenerationContext
    from ..llm.manager import LLMManager

    if problem is None:
        console.print("[bold cyan]Describe your data problem:[/bold cyan] ", end="")
        problem = input()

    console.print(f"[bold cyan]Solving problem:[/bold cyan] {problem}")

    async def _solve():
        global llm_manager

        # Initialize LLM manager if not already done
        if llm_manager is None:
            try:
                llm_manager = LLMManager.from_env()
                await llm_manager.initialize()
            except Exception as e:
                console.print(f"[yellow]![/yellow] LLM not available: {e}")
                console.print("[dim]Continuing with rule-based analysis...[/dim]")

        # Determine if we should use LLM
        use_llm = method == "llm" or (method == "auto" and llm_manager is not None)

        # Step 1: Extract problem features
        console.print("\n[cyan]Step 1: Analyzing problem...[/cyan]")
        extractor = ProblemExtractor(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        problem_features = await extractor.extract(problem)

        console.print(f"[dim]Problem Type:[/dim] {problem_features.problem_type}")
        console.print(
            f"[dim]Data Types:[/dim] {', '.join(dt.value for dt in problem_features.data_types)}"
        )
        console.print(f"[dim]Primary Goal:[/dim] {problem_features.primary_goal}")

        # Step 2: Detect data types
        console.print("\n[cyan]Step 2: Detecting data types...[/cyan]")
        data_type_detector = DataTypeDetector(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        data_type_result = await data_type_detector.detect(problem)

        # Step 3: Classify problem type
        console.print("\n[cyan]Step 3: Classifying problem...[/cyan]")
        classifier = ProblemClassifier(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        classification = await classifier.classify(problem, data_type_result)

        console.print(f"[dim]Classification:[/dim] {classification.primary_type.value}")
        console.print(f"[dim]Confidence:[/dim] {classification.confidence:.2f}")

        # Step 4: Load skills
        console.print("\n[cyan]Step 4: Loading skills...[/cyan]")
        skill_index = SkillIndex()
        await skill_index.load()

        skills = skill_index.get_all_skills()
        console.print(f"[dim]Loaded {len(skills)} skills[/dim]")

        # Step 5: Match skills
        console.print("\n[cyan]Step 5: Finding best solution...[/cyan]")
        matcher = SkillMatcher(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        match_results = await matcher.match(
            skills,
            problem_features,
            classification.primary_type,
            data_type_result,
            None,
            top_k=10,
        )

        # Step 6: Score and rank recommendations
        scorer = RecommendationScorer()
        recommendations = scorer.score_recommendations(match_results, max_recommendations=3)

        if not recommendations:
            console.print("[yellow]No suitable solutions found.[/yellow]")
            return

        # Show top recommendation
        top_rec = recommendations[0]
        console.print(f"\n[bold green]Best Solution:[/bold green] {top_rec.skill.name}")
        console.print(f"[dim]{top_rec.skill.description}[/dim]")
        console.print(f"[dim]Confidence: {top_rec.confidence:.2f}[/dim]")

        # Ask for confirmation
        if not yes and not Confirm.ask("\nGenerate code for this solution?", default=True):
            console.print("[yellow]Solution generation cancelled.[/yellow]")
            return

        # Step 7: Get related programming skills for reference
        from ..skills.metadata_schema import SkillTypeGroup

        related_programming_skills = [
            skill
            for skill in skills
            if skill.type_group == SkillTypeGroup.PROGRAMMING and skill.id != top_rec.skill.id
        ]

        # Show number of related skills
        console.print(
            f"[dim]Using {len(related_programming_skills)} related programming skills for reference[/dim]"
        )

        # Step 8: Generate code
        console.print("\n[cyan]Step 7: Generating code...[/cyan]")

        code_generator = CodeGenerator(llm_provider=llm_manager.provider if llm_manager else None)

        context = GenerationContext(
            skill=top_rec.skill,
            problem_description=problem,
            data_description="Your data",
            output_requirements="Result",
            related_skills=related_programming_skills[:5],  # Limit to 5 for reference
        )

        try:
            generated = await code_generator.generate(context, use_llm=use_llm)
            full_code = code_generator.format_code(generated)

            # Output code
            if output == "file":
                # Write to file
                filename = f"{top_rec.skill.id.replace('-', '_')}_solution.py"
                output_path = Path(filename)
                output_path.write_text(full_code, encoding="utf-8")
                console.print(f"[green]✓[/green] Code written to: {filename}")
            else:
                # Print to console
                console.print("\n[bold green]Generated Solution:[/bold green]\n")
                console.print(Syntax(full_code, "python", theme="monokai", line_numbers=True))

            console.print(f"\n[dim]Method: {generated.metadata.get('method', 'unknown')}[/dim]")

        except Exception as e:
            console.print(f"[red]Error generating code: {e}[/red]")
            logger.error(f"Code generation failed: {e}")

    asyncio.run(_solve())


@app.command()
def recommend(
    problem: str = typer.Argument(None, help="Problem description to analyze"),
    method: str = typer.Option(
        "auto", "--method", "-m", help="Method to use (auto, template, llm)"
    ),
    output: str = typer.Option("markdown", "--output", "-o", help="Output format (markdown, json)"),
    top_k: int = typer.Option(5, "--top", "-k", help="Number of recommendations to show"),
):
    """Get skill recommendations for a problem."""
    import asyncio
    from ..problem.extractor import ProblemExtractor
    from ..problem.classifier import ProblemClassifier
    from ..problem.data_types import DataTypeDetector
    from ..recommendation.matcher import SkillMatcher
    from ..recommendation.scorer import RecommendationScorer
    from ..skills.index import SkillIndex
    from ..llm.manager import LLMManager

    if problem is None:
        console.print("[bold cyan]Describe your data problem:[/bold cyan] ", end="")
        problem = input()

    console.print(f"[bold cyan]Analyzing problem:[/bold cyan] {problem}")

    async def _recommend():
        global llm_manager

        # Initialize LLM manager if not already done
        if llm_manager is None:
            try:
                llm_manager = LLMManager.from_env()
                await llm_manager.initialize()
            except Exception as e:
                console.print(f"[yellow]![/yellow] LLM not available: {e}")
                console.print("[dim]Continuing with rule-based analysis...[/dim]")

        # Determine if we should use LLM
        use_llm = method == "llm" or (method == "auto" and llm_manager is not None)

        # Step 1: Extract problem features
        console.print("\n[cyan]Extracting problem features...[/cyan]")
        extractor = ProblemExtractor(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        problem_features = await extractor.extract(problem)

        # Display problem summary
        console.print(f"[dim]Problem Type:[/dim] {problem_features.problem_type}")
        console.print(
            f"[dim]Data Types:[/dim] {', '.join(dt.value for dt in problem_features.data_types)}"
        )
        console.print(f"[dim]Primary Goal:[/dim] {problem_features.primary_goal}")

        # Step 2: Detect data types
        console.print("\n[cyan]Detecting data types...[/cyan]")
        data_type_detector = DataTypeDetector(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        data_type_result = await data_type_detector.detect(problem)

        # Step 3: Classify problem type
        console.print("\n[cyan]Classifying problem...[/cyan]")
        classifier = ProblemClassifier(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        classification = await classifier.classify(problem, data_type_result)

        console.print(f"[dim]Classification:[/dim] {classification.primary_type.value}")
        console.print(f"[dim]Confidence:[/dim] {classification.confidence:.2f}")

        # Step 4: Load skills
        console.print("\n[cyan]Loading skills...[/cyan]")
        skill_index = SkillIndex()
        await skill_index.load()

        skills = skill_index.get_all_skills()
        console.print(f"[dim]Loaded {len(skills)} skills[/dim]")

        # Step 5: Match skills
        console.print("\n[cyan]Matching skills to problem...[/cyan]")
        matcher = SkillMatcher(
            use_llm=use_llm, llm_provider=llm_manager.provider if llm_manager else None
        )
        match_results = await matcher.match(
            skills,
            problem_features,
            classification.primary_type,
            data_type_result,
            None,  # No specific output format
            top_k=top_k * 2,  # Get more candidates for better filtering
        )

        # Step 6: Score and rank recommendations
        console.print("\n[cyan]Scoring recommendations...[/cyan]")
        scorer = RecommendationScorer()
        recommendations = scorer.score_recommendations(match_results, max_recommendations=top_k)

        # Display recommendations
        console.print("\n[bold green]Recommended Skills:[/bold green]\n")

        if not recommendations:
            console.print(
                "[yellow]No matching skills found. Try a different problem description.[/yellow]"
            )
            return

        if output == "json":
            import json

            recs_json = [
                {
                    "rank": rec.ranking_position,
                    "name": rec.skill.name,
                    "id": rec.skill.id,
                    "score": rec.final_score,
                    "confidence": rec.confidence,
                    "match_reasons": rec.match_reasons,
                    "description": rec.skill.description,
                }
                for rec in recommendations
            ]
            console.print(json.dumps(recs_json, indent=2))
        else:  # markdown
            # Display in table format
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Skill", style="green", width=30)
            table.add_column("Category", width=20)
            table.add_column("Score", width=8)
            table.add_column("Reason", width=40)

            for rec in recommendations:
                reason = rec.match_reasons[0] if rec.match_reasons else "Good match"
                reason = reason[:37] + "..." if len(reason) > 37 else reason
                table.add_row(
                    str(rec.ranking_position),
                    rec.skill.name,
                    rec.skill.category.value,
                    f"{rec.final_score:.2f}",
                    reason,
                )

            console.print(table)

            # Show top recommendation details
            if recommendations:
                top_rec = recommendations[0]
                console.print(f"\n[bold cyan]Top Recommendation: {top_rec.skill.name}[/bold cyan]")
                console.print(f"[dim]{top_rec.skill.description}[/dim]")
                console.print(f"\n[dim]Match Score: {top_rec.match_score:.2f}[/dim]")
                console.print(f"[dim]Confidence: {top_rec.confidence:.2f}[/dim]")

                if top_rec.match_reasons:
                    console.print("\n[bold]Why this skill?[/bold]")
                    for reason in top_rec.match_reasons[:3]:
                        console.print(f"  • {reason}")

                if top_rec.skill.tags:
                    console.print(f"\n[dim]Tags: {', '.join(top_rec.skill.tags)}[/dim]")

        console.print(f"\n[dim]Found {len(recommendations)} matching skills[/dim]")

    asyncio.run(_recommend())


@app.command()
def generate(
    skill_id: str = typer.Argument(..., help="Skill ID to generate code for"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    method: str = typer.Option(
        "auto", "--method", "-m", help="Method to use (auto, template, llm)"
    ),
):
    """Generate Python code for a skill."""
    import asyncio
    from pathlib import Path

    from ..skills.index import SkillIndex
    from ..solution.code_generator import CodeGenerator, GenerationContext
    from ..llm.manager import LLMManager

    console.print(f"[bold cyan]Generating code for:[/bold cyan] {skill_id}")

    async def _generate():
        global llm_manager

        # Initialize LLM manager if not already done
        if llm_manager is None:
            try:
                llm_manager = LLMManager.from_env()
                await llm_manager.initialize()
            except Exception as e:
                console.print(f"[yellow]![/yellow] LLM not available: {e}")
                console.print("[dim]Continuing with template-based generation...[/dim]")

        # Determine if we should use LLM
        use_llm = method == "llm" or (method == "auto" and llm_manager is not None)

        # Load skill index
        console.print("\n[cyan]Loading skill...[/cyan]")
        skill_index = SkillIndex()
        await skill_index.load()

        skill = skill_index.get_skill(skill_id)

        if not skill:
            console.print(f"[red]Skill '{skill_id}' not found[/red]")
            console.print("[dim]Use 'skills-applier skills list' to see available skills[/dim]")
            return

        console.print(f"[dim]Found:[/dim] {skill.name}")
        console.print(f"[dim]Description:[/dim] {skill.description}")

        # Generate code
        console.print("\n[cyan]Generating code...[/cyan]")

        code_generator = CodeGenerator(llm_provider=llm_manager.provider if llm_manager else None)

        context = GenerationContext(
            skill=skill,
            problem_description=skill.description,
            data_description="Your data",
            output_requirements="Result",
        )

        try:
            generated = await code_generator.generate(context, use_llm=use_llm)

            # Format the code
            full_code = code_generator.format_code(generated)

            # Output code
            if output:
                # Write to file
                output_path = Path(output)
                output_path.write_text(full_code, encoding="utf-8")
                console.print(f"[green]✓[/green] Code written to: {output}")
            else:
                # Print to console
                console.print("\n[bold green]Generated Code:[/bold green]\n")
                console.print(Syntax(full_code, "python", theme="monokai", line_numbers=True))

            # Print metadata
            console.print(f"\n[dim]Method: {generated.metadata.get('method', 'unknown')}[/dim]")
            console.print(
                f"[dim]Imports: {', '.join(generated.imports) if generated.imports else 'None'}[/dim]"
            )

        except Exception as e:
            console.print(f"[red]Error generating code: {e}[/red]")
            logger.error(f"Code generation failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(_generate())


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
def init(
    mode: str = typer.Option(
        "merge",
        "--mode",
        "-m",
        help="Init mode: merge (merge new skills), overwrite (replace all), skip (skip existing)",
    ),
    batch_size: int = typer.Option(
        50,
        "--batch-size",
        "-b",
        help="Batch size for processing skills (saves progress after each batch)",
    ),
):
    """Initialize the system (scan skills, connect to LLM)."""
    import asyncio
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
    )

    console.print("[bold cyan]Initializing Skills Applier...[/bold cyan]\n")
    console.print(f"[dim]Mode: {mode}[/dim]")
    console.print(f"[dim]Batch size: {batch_size}[/dim]")

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

        # Scan skills
        console.print("\n[cyan]Scanning skills...[/cyan]")
        from ..skills.scanner import SkillScanner
        from ..skills.index import SkillIndex
        from ..skills.classifier import SkillClassifier
        from ..cli.config import ConfigManager
        from pathlib import Path

        # Load configuration
        config_manager = ConfigManager()
        skill_base_paths = config_manager.config.skill_base_paths

        # Check if configured paths exist, otherwise use default
        valid_paths = []
        for path_str in skill_base_paths:
            path = Path(path_str)
            if path.exists():
                valid_paths.append(str(path))
            else:
                console.print(f"[dim]Path not found: {path_str}[/dim]")

        # Determine if we should ignore example metadata
        use_configured_paths = bool(valid_paths)

        # Default to data/skills_metadata if no valid paths configured
        if not valid_paths:
            default_metadata_path = Path("data/skills_metadata")
            if default_metadata_path.exists():
                valid_paths = [str(default_metadata_path)]
                console.print(f"[dim]Using default skills path: {default_metadata_path}[/dim]")
            else:
                console.print(
                    "[yellow]![/yellow] No valid skill paths configured and no default path found"
                )
                console.print("[dim]Configure SKILL_BASE_PATH in .env or config/default.yaml[/dim]")
                console.print("\n[green]Initialization complete! (No skills scanned)[/green]")
                return

        # Initialize scanner with ignore_example if using configured paths
        scanner = SkillScanner(valid_paths, ignore_example=use_configured_paths)
        scanned_skills = scanner.scan_all()

        if not scanned_skills:
            console.print("[yellow]![/yellow] No skills found in configured paths")
            console.print("[cyan]Falling back to default skills metadata...[/cyan]")

            # Try default path without ignore_example
            default_metadata_path = Path("data/skills_metadata")
            if default_metadata_path.exists():
                scanner = SkillScanner([str(default_metadata_path)], ignore_example=False)
                scanned_skills = scanner.scan_all()

        if not scanned_skills:
            console.print("[yellow]![/yellow] No skills found")
            console.print("\n[green]Initialization complete! (No skills found)[/green]")
            return

        console.print(f"[green]✓[/green] Found {len(scanned_skills)} skills")

        # Initialize index
        index = SkillIndex()
        await index.load()

        # Handle overwrite mode
        if mode == "overwrite":
            console.print("[yellow]![/yellow] Overwrite mode: clearing existing index...")
            index.clear()

        # Get existing skill IDs for skip mode (and merge mode optimization)
        existing_skill_ids = set()
        if mode == "skip" or mode == "merge":
            existing_skill_ids = {s.id for s in index.get_all_skills()}
            console.print(f"[dim]Found {len(existing_skill_ids)} existing skills[/dim]")

        # Filter out existing skills to avoid re-classification
        skills_to_classify = scanned_skills
        if mode == "skip":
            skills_to_classify = [s for s in scanned_skills if s.id not in existing_skill_ids]
            skipped_count = len(scanned_skills) - len(skills_to_classify)
            if skipped_count > 0:
                console.print(
                    f"[dim]Skipping {skipped_count} existing skills (no need to re-classify)[/dim]"
                )

        # Classify skills with progress bar
        use_llm_classification = config_manager.config.enable_llm_classification
        classifier = SkillClassifier(
            use_llm=use_llm_classification and llm_manager is not None,
            llm_provider=llm_manager.provider if llm_manager else None,
        )

        # Classify and add to index with progress tracking (merged batch processing)
        # This ensures each batch is saved to index as soon as it's classified
        classified_skills = []
        if skills_to_classify:
            if use_llm_classification and llm_manager:
                console.print(
                    f"[cyan]Classifying and indexing {len(skills_to_classify)} new skills with LLM...[/cyan]"
                )
            else:
                console.print(
                    f"[cyan]Classifying and indexing {len(skills_to_classify)} new skills with rules...[/cyan]"
                )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Classifying and indexing skills...", total=len(skills_to_classify)
                )

                # Process skills in batches: classify -> save to index
                stats = {"added": 0, "updated": 0, "skipped": 0, "total": 0}
                for i in range(0, len(skills_to_classify), batch_size):
                    batch = skills_to_classify[i : i + batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (len(skills_to_classify) + batch_size - 1) // batch_size

                    # Classify the current batch
                    classified_batch = await classifier.batch_classify(batch)
                    classified_skills.extend(classified_batch)

                    # Add classified batch to index immediately
                    for j, skill in enumerate(classified_batch):
                        # Find existing skill
                        existing_idx = next(
                            (k for k, s in enumerate(index._metadata.skills) if s.id == skill.id),
                            None,
                        )

                        # Apply mode logic
                        if mode == "skip" and existing_idx is not None:
                            stats["skipped"] += 1
                        elif existing_idx is not None:
                            index._metadata.skills[existing_idx] = skill
                            stats["updated"] += 1
                        else:
                            index.add_skill(skill)
                            stats["added"] += 1

                        stats["total"] += 1

                        # Update progress
                        global_index = i + j + 1
                        progress.update(task, completed=global_index)

                    # Save progress after each batch
                    await index.save()
                    console.print(
                        f"[dim]Batch {batch_num}/{total_batches} saved ({len(batch)} skills)[/dim]"
                    )

            # For skip mode, append existing skills to classified list
            if mode == "skip":
                existing_skills = [s for s in scanned_skills if s.id in existing_skill_ids]
                classified_skills.extend(existing_skills)
        else:
            # No new skills to classify
            console.print("[green]✓[/green] No new skills to classify")
            classified_skills = scanned_skills
            stats = {"added": 0, "updated": 0, "skipped": 0, "total": len(scanned_skills)}

        # Display statistics
        final_stats = index.get_statistics()
        console.print(f"\n[green]✓[/green] Indexed {final_stats['total_skills']} skills")
        if stats.get("added", 0) > 0:
            console.print(f"[green]Added: {stats['added']}[/green]")
        if stats.get("updated", 0) > 0:
            console.print(f"[yellow]Updated: {stats['updated']}[/yellow]")
        if stats.get("skipped", 0) > 0:
            console.print(f"[dim]Skipped: {stats['skipped']}[/dim]")

        # Display statistics
        stats = index.get_statistics()
        console.print(f"[green]✓[/green] Indexed {stats['total_skills']} skills")

        if stats["categories"]:
            console.print("\n[bold cyan]Skills by Category:[/bold cyan]")
            for category, count in stats["categories"].items():
                console.print(f"  • {category}: {count}")

        console.print("\n[green]Initialization complete![/green]")

    # Run async initialization
    asyncio.run(_init())


@app.command()
def skills(
    action: str = typer.Argument("list", help="Action: list, search, show, check"),
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    data_type: str | None = typer.Option(None, "--data-type", "-d", help="Filter by data type"),
    skill_id: str | None = typer.Option(None, "--id", help="Skill ID (for show action)"),
    output: str = typer.Option("table", "--output", "-o", help="Output format (table, json)"),
):
    """Manage and browse skills."""
    import asyncio
    from ..skills.index import SkillIndex
    from ..skills.metadata_schema import SkillCategory, DataType

    async def _run_skills():
        index = SkillIndex()
        await index.load()

        if action == "list":
            console.print("[bold cyan]Available Skills[/bold cyan]\n")

            # Filter skills
            skills_list = index.get_all_skills()

            if category:
                try:
                    cat_enum = SkillCategory(category)
                    skills_list = index.get_by_category(cat_enum)
                    console.print(f"[dim]Category: {category}[/dim]\n")
                except ValueError:
                    console.print(f"[red]Invalid category: {category}[/red]")
                    console.print(
                        f"[dim]Valid categories: {[c.value for c in SkillCategory]}[/dim]"
                    )
                    return

            if tag:
                skills_list = [s for s in skills_list if tag in s.tags]
                console.print(f"[dim]Tag: {tag}[/dim]\n")

            if data_type:
                try:
                    dt_enum = DataType(data_type)
                    skills_list = index.filter_by_data_type(dt_enum)
                    console.print(f"[dim]Data Type: {data_type}[/dim]\n")
                except ValueError:
                    console.print(f"[red]Invalid data type: {data_type}[/red]")
                    console.print(f"[dim]Valid data types: {[dt.value for dt in DataType]}[/dim]")
                    return

            if not skills_list:
                console.print("[yellow]No skills found[/yellow]")
                return

            # Display skills
            if output == "json":
                import json

                skills_json = [
                    {
                        "id": skill.id,
                        "name": skill.name,
                        "category": skill.category.value,
                        "tags": skill.tags,
                        "description": skill.description,
                    }
                    for skill in skills_list
                ]
                console.print(json.dumps(skills_json, indent=2))
            else:
                # Display skills in a table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Category", width=25)
                table.add_column("Tags")

                for skill in skills_list:
                    tags_str = ", ".join(skill.tags)
                    table.add_row(skill.id, skill.name, skill.category.value, tags_str)

                console.print(table)
                console.print(f"\n[dim]Total: {len(skills_list)} skills[/dim]")

        elif action == "search":
            if not skill_id and not tag and not data_type:
                console.print("[red]Error: Search requires a query term[/red]")
                console.print("Use: skills-applier skills search --tag <tag> or --data-type <type>")
                return

            console.print("[bold cyan]Search Skills[/bold cyan]\n")

            skills_list = []

            if skill_id:
                skills_list = index.search(skill_id)
                console.print(f"[dim]Query: {skill_id}[/dim]\n")

            if tag:
                skills_list = index.get_by_tag(tag)
                console.print(f"[dim]Tag: {tag}[/dim]\n")

            if data_type:
                try:
                    dt_enum = DataType(data_type)
                    skills_list = index.filter_by_data_type(dt_enum)
                    console.print(f"[dim]Data Type: {data_type}[/dim]\n")
                except ValueError:
                    console.print(f"[red]Invalid data type: {data_type}[/red]")
                    return

            if not skills_list:
                console.print("[yellow]No matching skills found[/yellow]")
                return

            # Display results
            if output == "json":
                import json

                skills_json = [
                    {
                        "id": skill.id,
                        "name": skill.name,
                        "category": skill.category.value,
                        "description": skill.description,
                    }
                    for skill in skills_list
                ]
                console.print(json.dumps(skills_json, indent=2))
            else:
                # Display results
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Category", width=25)
                table.add_column("Description")

                for skill in skills_list[:10]:  # Limit to 10 results
                    table.add_row(skill.id, skill.name, skill.category.value, skill.description)

                console.print(table)
                console.print(f"\n[dim]Found {len(skills_list)} skills (showing first 10)[/dim]")

        elif action == "show":
            if not skill_id:
                console.print("[red]Error: Show action requires --id <skill_id>[/red]")
                console.print("Use: skills-applier skills show --id <skill_id>")
                return

            console.print(f"[bold cyan]Skill Details: {skill_id}[/bold cyan]\n")

            skill = index.get_skill(skill_id)

            if not skill:
                console.print(f"[red]Skill '{skill_id}' not found[/red]")
                return

            # Display skill details
            table = Table(show_header=False, box=None)
            table.add_column("Field", style="cyan", width=20)
            table.add_column("Value")

            table.add_row("ID", skill.id)
            table.add_row("Name", skill.name)
            table.add_row("Category", skill.category.value)
            table.add_row("Description", skill.description)
            table.add_row("Path", skill.path)

            if skill.tags:
                table.add_row("Tags", ", ".join(skill.tags))

            if skill.input_data_types:
                table.add_row(
                    "Input Data Types", ", ".join([dt.value for dt in skill.input_data_types])
                )

            if skill.output_format:
                table.add_row("Output Format", skill.output_format)

            if skill.dependencies:
                table.add_row("Dependencies", ", ".join(skill.dependencies))

            if skill.prerequisites:
                table.add_row("Prerequisites", ", ".join(skill.prerequisites))

            if skill.statistical_concept:
                table.add_row("Statistical Concept", skill.statistical_concept)

            if skill.assumptions:
                table.add_row(
                    "Assumptions", "\n" + "\n".join(f"  • {a}" for a in skill.assumptions)
                )

            if skill.use_cases:
                table.add_row("Use Cases", "\n" + "\n".join(f"  • {u}" for u in skill.use_cases))

            table.add_row("Source", skill.source)
            table.add_row("Confidence", f"{skill.confidence:.2f}")

            if skill.last_updated:
                table.add_row("Last Updated", skill.last_updated)

            console.print(table)

        elif action == "check":
            """Check skills for issues and optionally fix them."""
            console.print("[bold cyan]Checking skills for issues...[/bold cyan]\n")

            all_skills = index.get_all_skills()
            issues_found = []

            for skill in all_skills:
                skill_issues = []

                # Check 1: Missing or empty description
                if not skill.description or skill.description.strip() == "":
                    skill_issues.append("Missing description")

                # Check 2: Missing tags
                if not skill.tags:
                    skill_issues.append("Missing tags")

                # Check 3: Missing data types
                if not skill.input_data_types:
                    skill_issues.append("Missing input data types")

                # Check 4: Invalid path
                from pathlib import Path

                if not Path(skill.path).exists():
                    skill_issues.append("Path does not exist")

                # Check 5: Low confidence score
                if skill.confidence < 0.5:
                    skill_issues.append(f"Low confidence ({skill.confidence:.2f})")

                # Check 6: Missing type_group
                if not skill.type_group:
                    skill_issues.append("Missing type_group")

                if skill_issues:
                    issues_found.append({"skill": skill, "issues": skill_issues})

            # Display results
            if not issues_found:
                console.print(
                    f"[green]✓[/green] No issues found in [green]{len(all_skills)}[/green] skills"
                )
            else:
                console.print(
                    f"[yellow]![/yellow] Found issues in [yellow]{len(issues_found)}[/yellow] skills:\n"
                )

                # Display issues in a table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("ID", style="cyan", width=30)
                table.add_column("Name", style="green", width=30)
                table.add_column("Issues", style="yellow")

                for item in issues_found:
                    issues_str = ", ".join(item["issues"])
                    table.add_row(item["skill"].id, item["skill"].name, issues_str)

                console.print(table)
                console.print(f"\n[dim]Checked {len(all_skills)} skills total[/dim]")

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Use: skills-applier skills [list|search|show|check] [options]")

    asyncio.run(_run_skills())


@app.command()
def config(
    action: str = typer.Argument("list", help="Action: list, get, set, validate"),
    key: str | None = typer.Argument(None, help="Configuration key"),
    value: str | None = typer.Argument(None, help="Configuration value"),
):
    """Manage configuration."""
    from ..cli.config import ConfigManager

    config_manager = ConfigManager()

    if action == "list" or (action == "get" and key is None):
        # List configuration
        console.print("[bold cyan]Current Configuration[/bold cyan]\n")
        config_manager.display_config()

    elif action == "get" and key:
        # Get specific configuration value
        config_value = config_manager.get(key)

        if config_value is not None:
            console.print(f"[bold cyan]{key}:[/bold cyan] {config_value}")
        else:
            console.print(f"[red]Configuration key not found: {key}[/red]")
            console.print("[dim]Use 'skills-applier config list' to see all available keys[/dim]")

    elif action == "set" and key and value:
        # Set configuration value
        # Handle boolean values
        if value.lower() in ("true", "false"):
            value_bool = value.lower() == "true"
            success = config_manager.set(key, value_bool)
        # Handle integer values
        elif value.isdigit():
            success = config_manager.set(key, int(value))
        else:
            success = config_manager.set(key, value)

        if success:
            console.print(f"[green]✓[/green] Set {key} = {value}")
            # Save to file
            if config_manager.save_config():
                console.print("[green]✓[/green] Configuration saved")
            else:
                console.print("[yellow]![/yellow] Failed to save configuration to file")
        else:
            console.print(f"[red]✗[/red] Failed to set configuration: {key}")

    elif action == "validate":
        # Validate configuration
        console.print("[bold cyan]Validating configuration...[/bold cyan]\n")

        validation = config_manager.validate_config()

        if validation["valid"]:
            console.print("[green]✓[/green] Configuration is valid")
        else:
            console.print("[red]✗[/red] Configuration has errors")
            for issue in validation["issues"]:
                console.print(f"  [red]•[/red] {issue}")

        if validation["warnings"]:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in validation["warnings"]:
                console.print(f"  [yellow]•[/yellow] {warning}")

        if validation["valid"] and not validation["warnings"]:
            console.print("\n[green]No issues found![/green]")

    else:
        console.print(f"[red]Unknown or incomplete action: {action}[/red]")
        console.print("Use: skills-applier config [list|get|set|validate] [key] [value]")


if __name__ == "__main__":
    app()
