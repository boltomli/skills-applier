"""Code output and file saving utilities."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class CodeOutputHandler:
    """Handler for code output and file saving."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize output handler.
        
        Args:
            output_dir: Default output directory
        """
        self.output_dir = output_dir or Path.cwd()
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_code(
        self,
        code: str,
        filename: str,
        subdirectory: Optional[str] = None
    ) -> Path:
        """Save code to a file.
        
        Args:
            code: Code content
            filename: Name of the file
            subdirectory: Optional subdirectory within output_dir
            
        Returns:
            Path to saved file
        """
        # Determine full path
        if subdirectory:
            full_dir = self.output_dir / subdirectory
        else:
            full_dir = self.output_dir
        
        full_dir.mkdir(parents=True, exist_ok=True)
        file_path = full_dir / filename
        
        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        logger.info(f"Saved code to {file_path}")
        return file_path
    
    def save_requirements(
        self,
        dependencies: list[str],
        filename: str = "requirements.txt"
    ) -> Path:
        """Save requirements to a file.
        
        Args:
            dependencies: List of dependencies
            filename: Name of the requirements file
            
        Returns:
            Path to saved file
        """
        from ..solution.dependencies import DependencyGenerator
        
        generator = DependencyGenerator()
        requirements_content = generator.generate_requirements_txt(dependencies)
        
        return self.save_code(requirements_content, filename)
    
    def save_markdown_report(
        self,
        title: str,
        sections: Dict[str, str],
        filename: str = "report.md"
    ) -> Path:
        """Save a markdown report.
        
        Args:
            title: Report title
            sections: Dictionary of section headers to content
            filename: Name of the report file
            
        Returns:
            Path to saved file
        """
        lines = [f"# {title}\n"]
        
        for header, content in sections.items():
            lines.append(f"## {header}\n")
            lines.append(content)
            lines.append("\n")
        
        report_content = "\n".join(lines)
        return self.save_code(report_content, filename)
    
    def save_json(
        self,
        data: Dict[str, Any],
        filename: str
    ) -> Path:
        """Save data as JSON.
        
        Args:
            data: Data to save
            filename: Name of the JSON file
            
        Returns:
            Path to saved file
        """
        import json
        
        json_content = json.dumps(data, indent=2, ensure_ascii=False)
        return self.save_code(json_content, filename)
    
    def create_script_bundle(
        self,
        code: str,
        dependencies: list[str],
        script_name: str,
        include_readme: bool = True
    ) -> Path:
        """Create a complete script bundle.
        
        Args:
            code: Python code
            dependencies: List of dependencies
            script_name: Name of the script
            include_readme: Whether to include README
            
        Returns:
            Path to bundle directory
        """
        # Create bundle directory
        bundle_dir = self.output_dir / script_name
        bundle_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main script
        script_path = bundle_dir / f"{script_name}.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Save requirements
        self.save_code(
            self._generate_requirements(dependencies),
            "requirements.txt",
            subdirectory=script_name
        )
        
        # Save README if requested
        if include_readme:
            readme_content = self._generate_readme(script_name, dependencies)
            self.save_code(
                readme_content,
                "README.md",
                subdirectory=script_name
            )
        
        console.print(f"[green]Created script bundle:[/green] {bundle_dir}")
        return bundle_dir
    
    def _generate_requirements(self, dependencies: list[str]) -> str:
        """Generate requirements.txt content.
        
        Args:
            dependencies: List of dependencies
            
        Returns:
            Requirements content
        """
        from ..solution.dependencies import DependencyGenerator
        
        generator = DependencyGenerator()
        return generator.generate_requirements_txt(dependencies)
    
    def _generate_readme(self, script_name: str, dependencies: list[str]) -> str:
        """Generate README content.
        
        Args:
            script_name: Name of the script
            dependencies: List of dependencies
            
        Returns:
            README content
        """
        return f"""# {script_name}

This script was generated by Stats Solver.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script:

```bash
python {script_name}.py
```

## Dependencies

{', '.join(dependencies) if dependencies else 'None'}

## Generated by Stats Solver

This script was automatically generated based on a statistical analysis recommendation.
"""
    
    def display_code(self, code: str, language: str = "python"):
        """Display code in console.
        
        Args:
            code: Code to display
            language: Programming language
        """
        from rich.syntax import Syntax
        from rich.panel import Panel
        
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Generated Code", border_style="cyan"))
    
    def confirm_overwrite(self, file_path: Path) -> bool:
        """Confirm file overwrite.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if user confirms overwrite
        """
        from rich.prompt import Confirm
        
        return Confirm.ask(
            f"[yellow]File {file_path} already exists. Overwrite?[/yellow]",
            default=False
        )
    
    def save_with_confirmation(
        self,
        code: str,
        filename: str,
        subdirectory: Optional[str] = None,
        overwrite: bool = False
    ) -> Optional[Path]:
        """Save code with overwrite confirmation.
        
        Args:
            code: Code content
            filename: Name of the file
            subdirectory: Optional subdirectory
            overwrite: Whether to overwrite without confirmation
            
        Returns:
            Path to saved file or None if cancelled
        """
        # Determine full path
        if subdirectory:
            full_dir = self.output_dir / subdirectory
        else:
            full_dir = self.output_dir
        
        full_dir.mkdir(parents=True, exist_ok=True)
        file_path = full_dir / filename
        
        # Check if file exists
        if file_path.exists() and not overwrite:
            if not self.confirm_overwrite(file_path):
                console.print("[yellow]Save cancelled.[/yellow]")
                return None
        
        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        console.print(f"[green]✓[/green] Saved to [cyan]{file_path}[/cyan]")
        return file_path
    
    def set_output_dir(self, output_dir: Path):
        """Set the output directory.
        
        Args:
            output_dir: New output directory
        """
        self.output_dir = output_dir
        self.ensure_output_dir()
        console.print(f"[cyan]Output directory set to:[/cyan] {output_dir}")
    
    def get_output_dir(self) -> Path:
        """Get the current output directory.
        
        Returns:
            Current output directory
        """
        return self.output_dir