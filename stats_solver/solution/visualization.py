"""Visualization code generator."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..skills.metadata_schema import SkillMetadata, DataType
from ..problem.output_format import OutputFormat
from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class PlotType(str, Enum):
    """Types of plots."""
    
    HISTOGRAM = "histogram"
    SCATTER = "scatter"
    LINE = "line"
    BAR = "bar"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    PIE = "pie"


@dataclass
class VisualizationSpec:
    """Specification for a visualization."""
    
    plot_type: PlotType
    data_param: str
    x_param: Optional[str] = None
    y_param: Optional[str] = None
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    figsize: tuple = (10, 6)
    color: Optional[str] = None
    grid: bool = True
    legend: bool = False


@dataclass
class GeneratedVisualization:
    """Generated visualization code."""
    
    code: str
    description: str
    plot_type: PlotType
    libraries: List[str]
    metadata: Dict[str, Any]


class VisualizationGenerator:
    """Generator for visualization code."""
    
    # Plot type mapping
    PLOT_TYPE_MAPPING = {
        OutputFormat.HISTOGRAM: PlotType.HISTOGRAM,
        OutputFormat.SCATTER_PLOT: PlotType.SCATTER,
        OutputFormat.LINE_PLOT: PlotType.LINE,
        OutputFormat.BAR_CHART: PlotType.BAR,
        OutputFormat.HEATMAP: PlotType.HEATMAP,
    }
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        """Initialize visualization generator.
        
        Args:
            llm_provider: LLM provider for enhanced generation
        """
        self.llm_provider = llm_provider
    
    async def generate(
        self,
        skill: SkillMetadata,
        output_format: OutputFormat,
        data_description: Optional[str] = None,
        use_llm: bool = False
    ) -> GeneratedVisualization:
        """Generate visualization code.
        
        Args:
            skill: Skill metadata
            output_format: Desired output format
            data_description: Optional data description
            use_llm: Whether to use LLM for generation
            
        Returns:
            Generated visualization code
        """
        if use_llm and self.llm_provider:
            return await self._generate_with_llm(skill, output_format, data_description)
        else:
            return self._generate_with_template(skill, output_format, data_description)
    
    def _generate_with_template(
        self,
        skill: SkillMetadata,
        output_format: OutputFormat,
        data_description: Optional[str] = None
    ) -> GeneratedVisualization:
        """Generate visualization using templates.
        
        Args:
            skill: Skill metadata
            output_format: Desired output format
            data_description: Optional data description
            
        Returns:
            Generated visualization code
        """
        plot_type = self._determine_plot_type(output_format, skill)
        spec = self._create_spec(plot_type, skill, data_description)
        code = self._generate_code_from_spec(spec)
        
        return GeneratedVisualization(
            code=code,
            description=f"Generate {plot_type.value} visualization",
            plot_type=plot_type,
            libraries=["matplotlib"],
            metadata={"method": "template"},
        )
    
    async def _generate_with_llm(
        self,
        skill: SkillMetadata,
        output_format: OutputFormat,
        data_description: Optional[str] = None
    ) -> GeneratedVisualization:
        """Generate visualization using LLM.
        
        Args:
            skill: Skill metadata
            output_format: Desired output format
            data_description: Optional data description
            
        Returns:
            Generated visualization code
        """
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured")
        
        prompt = self._build_generation_prompt(skill, output_format, data_description)
        
        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in data visualization using Python. Generate clean, well-documented visualization code.",
            )
            
            return GeneratedVisualization(
                code=result.get("code", ""),
                description=result.get("description", ""),
                plot_type=PlotType(result.get("plot_type", "histogram")),
                libraries=result.get("libraries", ["matplotlib"]),
                metadata={"method": "llm"},
            )
        except Exception as e:
            logger.error(f"LLM visualization generation failed: {e}")
            return self._generate_with_template(skill, output_format, data_description)
    
    def _determine_plot_type(
        self,
        output_format: OutputFormat,
        skill: SkillMetadata
    ) -> PlotType:
        """Determine appropriate plot type.
        
        Args:
            output_format: Desired output format
            skill: Skill metadata
            
        Returns:
            Plot type
        """
        # Check explicit mapping
        if output_format in self.PLOT_TYPE_MAPPING:
            return self.PLOT_TYPE_MAPPING[output_format]
        
        # Infer from skill
        skill_text = f"{skill.id} {skill.description} {' '.join(skill.tags)}".lower()
        
        if any(kw in skill_text for kw in ["histogram", "distribution", "freq"]):
            return PlotType.HISTOGRAM
        elif any(kw in skill_text for kw in ["scatter", "point"]):
            return PlotType.SCATTER
        elif any(kw in skill_text for kw in ["line", "trend", "time"]):
            return PlotType.LINE
        elif any(kw in skill_text for kw in ["bar", "column"]):
            return PlotType.BAR
        elif any(kw in skill_text for kw in ["box", "boxplot"]):
            return PlotType.BOX
        elif any(kw in skill_text for kw in ["heatmap", "correlation"]):
            return PlotType.HEATMAP
        else:
            return PlotType.HISTOGRAM
    
    def _create_spec(
        self,
        plot_type: PlotType,
        skill: SkillMetadata,
        data_description: Optional[str] = None
    ) -> VisualizationSpec:
        """Create visualization specification.
        
        Args:
            plot_type: Type of plot
            skill: Skill metadata
            data_description: Optional data description
            
        Returns:
            Visualization specification
        """
        return VisualizationSpec(
            plot_type=plot_type,
            data_param="data",
            title=skill.name,
            xlabel=data_description or "X",
            ylabel="Value" if plot_type != PlotType.HISTOGRAM else "Frequency",
        )
    
    def _generate_code_from_spec(self, spec: VisualizationSpec) -> str:
        """Generate code from specification.
        
        Args:
            spec: Visualization specification
            
        Returns:
            Generated code
        """
        lines = [
            "import matplotlib.pyplot as plt",
            "import numpy as np",
            "",
            f"def create_{spec.plot_type.value}(data):",
            '    """',
            f"    Create a {spec.plot_type.value} plot.",
            '    """',
            "",
            "    # Create figure",
            f"    fig, ax = plt.subplots(figsize={spec.figsize})",
            "",
        ]
        
        # Add plot-specific code
        if spec.plot_type == PlotType.HISTOGRAM:
            lines.extend([
                "    # Create histogram",
                "    ax.hist(data, bins=30, edgecolor='black', alpha=0.7)",
            ])
        elif spec.plot_type == PlotType.SCATTER:
            lines.extend([
                "    # Create scatter plot",
                "    x = np.arange(len(data))",
                "    ax.scatter(x, data, alpha=0.6)",
            ])
        elif spec.plot_type == PlotType.LINE:
            lines.extend([
                "    # Create line plot",
                "    x = np.arange(len(data))",
                "    ax.plot(x, data, linewidth=2)",
            ])
        elif spec.plot_type == PlotType.BAR:
            lines.extend([
                "    # Create bar plot",
                "    x = np.arange(len(data))",
                "    ax.bar(x, data, alpha=0.7)",
            ])
        elif spec.plot_type == PlotType.BOX:
            lines.extend([
                "    # Create box plot",
                "    ax.boxplot([data])",
            ])
        elif spec.plot_type == PlotType.HEATMAP:
            lines.extend([
                "    # Create heatmap",
                "    data_matrix = np.array(data).reshape(-1, 1)",
                "    ax.imshow(data_matrix, cmap='viridis', aspect='auto')",
                "    plt.colorbar(ax.collections[0], ax=ax)",
            ])
        else:
            lines.extend([
                "    # Default plot",
                "    ax.plot(data)",
            ])
        
        # Add customization
        lines.extend([
            "",
            "    # Customize plot",
            f"    ax.set_title('{spec.title}')",
            f"    ax.set_xlabel('{spec.xlabel}')",
            f"    ax.set_ylabel('{spec.ylabel}')",
        ])
        
        if spec.grid:
            lines.append("    ax.grid(True, alpha=0.3)")
        
        lines.extend([
            "",
            "    plt.tight_layout()",
            "    return fig",
            "",
            "",
            "if __name__ == '__main__':",
            "    # Example usage",
            "    example_data = np.random.randn(100)",
            f"    fig = create_{spec.plot_type.value}(example_data)",
            "    plt.show()",
        ])
        
        return "\n".join(lines)
    
    def _build_generation_prompt(
        self,
        skill: SkillMetadata,
        output_format: OutputFormat,
        data_description: Optional[str] = None
    ) -> str:
        """Build visualization generation prompt.
        
        Args:
            skill: Skill metadata
            output_format: Desired output format
            data_description: Optional data description
            
        Returns:
            Prompt string
        """
        return f"""Generate Python visualization code for the following:

**Skill**: {skill.name}
**Description**: {skill.description}
**Output Format**: {output_format.value}
**Data Description**: {data_description or 'Numerical data'}

Return a JSON object with:
- code: Complete Python code including imports, function definition, and example usage
- description: Description of the visualization
- plot_type: Type of plot (histogram, scatter, line, bar, box, violin, heatmap, pie)
- libraries: List of required libraries

Requirements:
1. Use matplotlib for the visualization
2. Include proper axis labels and title
3. Add grid when appropriate
4. Include example usage in if __name__ == "__main__" block
5. Return the figure object from the function"""
    
    def generate_multi_plot(
        self,
        specs: List[VisualizationSpec]
    ) -> str:
        """Generate code for multiple subplots.
        
        Args:
            specs: List of visualization specifications
            
        Returns:
            Generated multi-plot code
        """
        n_plots = len(specs)
        cols = min(n_plots, 3)
        rows = (n_plots + cols - 1) // cols
        
        lines = [
            "import matplotlib.pyplot as plt",
            "import numpy as np",
            "",
            "def create_multi_plot(*datasets):",
            '    """',
            f"    Create a {n_plots}-panel plot.",
            '    """',
            "",
            f"    fig, axes = plt.subplots({rows}, {cols}, figsize={(cols * 6, rows * 4)})",
            "",
        ]
        
        # Flatten axes if needed
        if rows > 1 or cols > 1:
            lines.append("    axes = axes.flatten()")
        else:
            lines.append("    axes = [axes]")
        
        lines.append("")
        
        # Add plots
        for i, spec in enumerate(specs):
            lines.append(f"    # Plot {i + 1}: {spec.title}")
            lines.append(f"    ax = axes[{i}]")
            
            if spec.plot_type == PlotType.HISTOGRAM:
                lines.append(f"    ax.hist(datasets[{i}], bins=30, edgecolor='black', alpha=0.7)")
            elif spec.plot_type == PlotType.SCATTER:
                lines.append(f"    x = np.arange(len(datasets[{i}]))")
                lines.append(f"    ax.scatter(x, datasets[{i}], alpha=0.6)")
            elif spec.plot_type == PlotType.LINE:
                lines.append(f"    x = np.arange(len(datasets[{i}]))")
                lines.append(f"    ax.plot(x, datasets[{i}], linewidth=2)")
            else:
                lines.append(f"    ax.plot(datasets[{i}])")
            
            lines.append(f"    ax.set_title('{spec.title}')")
            lines.append("")
        
        # Hide unused axes
        if n_plots < rows * cols:
            lines.append(f"    for i in range({n_plots}, len(axes)):")
            lines.append("        axes[i].set_visible(False)")
            lines.append("")
        
        lines.extend([
            "    plt.tight_layout()",
            "    return fig",
            "",
            "",
            "if __name__ == '__main__':",
            "    # Example usage",
        ])
        
        for i in range(n_plots):
            lines.append(f"    data{i+1} = np.random.randn(100)")
        
        lines.append(f"    fig = create_multi_plot({', '.join([f'data{i+1}' for i in range(n_plots)])})")
        lines.append("    plt.show()")
        
        return "\n".join(lines)
