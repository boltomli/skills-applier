"""Template for visualization tasks."""

from typing import Any
from .base import BaseTemplate


class VisualizationTemplate(BaseTemplate):
    """Template for visualization implementations."""

    TEMPLATE = '''def {function_name}({params}):
    """
    {docstring}

    Parameters
    ----------
    {param_docs}

    Returns
    -------
    matplotlib.figure.Figure
        The generated figure object

    Examples
    --------
    >>> {example_call}
    >>> fig = {function_name}({example_args})
    >>> plt.show()
    """
    import matplotlib.pyplot as plt
    import numpy as np

    # Prepare data
    {data_preparation}

    # Create figure
    fig, ax = plt.subplots(figsize={figure_size})

    # Create plot
    {plot_code}

    # Customize plot
    {customization}

    return fig


if __name__ == "__main__":
    # Example usage
    {example_usage}
'''

    def render(self, **kwargs: Any) -> str:
        """Render the visualization template.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered template
        """
        variables = {
            "function_name": kwargs.get("skill_id", "create_plot").replace("-", "_"),
            "docstring": kwargs.get("description", "Create visualization"),
            "params": self._get_params(kwargs),
            "param_docs": self._get_param_docs(kwargs),
            "example_call": kwargs.get("example_call", "# Example"),
            "example_args": kwargs.get("example_args", "data"),
            "data_preparation": self._get_data_preparation(kwargs),
            "figure_size": kwargs.get("figure_size", "(10, 6)"),
            "plot_code": self._get_plot_code(kwargs),
            "customization": self._get_customization(kwargs),
            "example_usage": kwargs.get("example_usage", "fig = create_plot(data)\nplt.show()"),
        }

        return self.TEMPLATE.format(**variables)

    def _get_params(self, kwargs: dict[str, Any]) -> str:
        """Get function parameters.

        Args:
            kwargs: Template variables

        Returns:
            Parameter string
        """
        return "data, title=None, xlabel=None, ylabel=None, **kwargs"

    def _get_param_docs(self, kwargs: dict[str, Any]) -> str:
        """Get parameter documentation.

        Args:
            kwargs: Template variables

        Returns:
            Parameter documentation
        """
        return """data : array-like
        Data to visualize
    title : str, optional
        Plot title
    xlabel : str, optional
        X-axis label
    ylabel : str, optional
        Y-axis label
    **kwargs : additional keyword arguments
        Additional keyword arguments for plotting"""

    def _get_data_preparation(self, kwargs: dict[str, Any]) -> str:
        """Get data preparation code.

        Args:
            kwargs: Template variables

        Returns:
            Data preparation code
        """
        return """data = np.asarray(data)
    if data.ndim == 1:
        x = np.arange(len(data))
        y = data
    else:
        x, y = data.T"""

    def _get_plot_code(self, kwargs: dict[str, Any]) -> str:
        """Get plot creation code.

        Args:
            kwargs: Template variables

        Returns:
            Plot code
        """
        return """ax.plot(x, y, **kwargs)
    ax.grid(True, alpha=0.3)"""

    def _get_customization(self, kwargs: dict[str, Any]) -> str:
        """Get plot customization code.

        Args:
            kwargs: Template variables

        Returns:
            Customization code
        """
        return """if title:
        ax.set_title(title)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    plt.tight_layout()"""

    def get_name(self) -> str:
        """Get template name.

        Returns:
            Template name
        """
        return "Visualization"
