"""Solution generation module."""

__all__ = [
    "CodeGenerator",
    "DocstringGenerator",
    "DependencyGenerator",
    "SampleDataGenerator",
    "VisualizationGenerator",
    "CodeValidator",
]


# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == "CodeGenerator":
        from .code_generator import CodeGenerator

        return CodeGenerator
    elif name == "DocstringGenerator":
        from .docstring import DocstringGenerator

        return DocstringGenerator
    elif name == "DependencyGenerator":
        from .dependencies import DependencyGenerator

        return DependencyGenerator
    elif name == "SampleDataGenerator":
        from .sample_data import SampleDataGenerator

        return SampleDataGenerator
    elif name == "VisualizationGenerator":
        from .visualization import VisualizationGenerator

        return VisualizationGenerator
    elif name == "CodeValidator":
        from .validator import CodeValidator

        return CodeValidator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
