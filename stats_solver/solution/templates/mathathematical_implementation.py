"""Template for mathematical implementations."""

from typing import Dict, Any
from .base import BaseTemplate


class MathematicalImplementationTemplate(BaseTemplate):
    """Template for mathematical algorithm implementations."""

    TEMPLATE = '''def {function_name}({params}):
    """
    {docstring}

    Parameters
    ----------
    {param_docs}

    Returns
    -------
    {return_type}
        {return_description}

    Examples
    --------
    >>> {example_call}
    >>> result = {function_name}({example_args})
    >>> print(result)
    """
    import numpy as np

    # Validate inputs
    {validation}

    # Perform calculation
    {implementation}

    return {return_value}


if __name__ == "__main__":
    # Example usage
    {example_usage}
'''

    def render(self, **kwargs: Any) -> str:
        """Render the mathematical implementation template.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered template
        """
        variables = {
            "function_name": kwargs.get("skill_id", "math_function").replace("-", "_"),
            "docstring": kwargs.get("description", "Perform mathematical calculation"),
            "params": self._get_params(kwargs),
            "param_docs": self._get_param_docs(kwargs),
            "return_type": kwargs.get("output_requirements", "float"),
            "return_description": kwargs.get("output_requirements", "Calculation result"),
            "example_call": kwargs.get("example_call", "# Example"),
            "example_args": kwargs.get("example_args", "data"),
            "validation": self._get_validation(kwargs),
            "implementation": self._get_implementation(kwargs),
            "return_value": self._get_return_value(kwargs),
            "example_usage": kwargs.get("example_usage", "result = math_function(1, 2, 3)"),
        }

        return self.TEMPLATE.format(**variables)

    def _get_params(self, kwargs: Dict[str, Any]) -> str:
        """Get function parameters.

        Args:
            kwargs: Template variables

        Returns:
            Parameter string
        """
        return "data, *args, **kwargs"

    def _get_param_docs(self, kwargs: Dict[str, Any]) -> str:
        """Get parameter documentation.

        Args:
            kwargs: Template variables

        Returns:
            Parameter documentation
        """
        return """data : array-like
        Input data for calculation
    *args : additional positional arguments
        Additional arguments
    **kwargs : additional keyword arguments
        Additional keyword arguments"""

    def _get_validation(self, kwargs: Dict[str, Any]) -> str:
        """Get input validation code.

        Args:
            kwargs: Template variables

        Returns:
            Validation code
        """
        return """data = np.asarray(data)
    if data.size == 0:
        raise ValueError("Input data cannot be empty")"""

    def _get_implementation(self, kwargs: Dict[str, Any]) -> str:
        """Get implementation code.

        Args:
            kwargs: Template variables

        Returns:
            Implementation code
        """
        return """result = perform_calculation(data)  # Implement your algorithm here"""

    def _get_return_value(self, kwargs: Dict[str, Any]) -> str:
        """Get return value expression.

        Args:
            kwargs: Template variables

        Returns:
            Return value expression
        """
        return "result"

    def get_name(self) -> str:
        """Get template name.

        Returns:
            Template name
        """
        return "Mathematical Implementation"
