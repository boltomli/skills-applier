"""Template for statistical methods."""

from typing import Dict, Any
from .base import BaseTemplate


class StatisticalMethodTemplate(BaseTemplate):
    """Template for statistical method implementations."""
    
    TEMPLATE = '''def {function_name}({data_param}):
    """
    {docstring}
    
    Parameters
    ----------
    {data_param} : array-like
        {data_description}
    
    Returns
    -------
    {return_type}
        {return_description}
    
    Examples
    --------
    >>> {data_example}
    >>> result = {function_name}({data_param})
    >>> print(result)
    """
    import numpy as np
    from scipy import stats
    
    # Validate input
    {data_param} = np.asarray({data_param})
    
    # Perform statistical analysis
    {implementation}
    
    return {return_value}


if __name__ == "__main__":
    # Example usage
    example_data = {example_data}
    result = {function_name}(example_data)
    print(f"Result: {{result}}")
'''
    
    def render(self, **kwargs: Any) -> str:
        """Render the statistical method template.
        
        Args:
            **kwargs: Template variables
            
        Returns:
            Rendered template
        """
        variables = {
            "function_name": kwargs.get("skill_id", "statistical_method").replace("-", "_"),
            "docstring": kwargs.get("description", "Perform statistical analysis"),
            "data_param": kwargs.get("data_description", "data").split()[0].lower(),
            "data_description": kwargs.get("data_description", "Input data"),
            "return_type": kwargs.get("output_requirements", "float"),
            "return_description": kwargs.get("output_requirements", "Statistical result"),
            "data_example": kwargs.get("data_example", "np.array([1, 2, 3, 4, 5])"),
            "implementation": self._get_implementation(kwargs),
            "return_value": self._get_return_value(kwargs),
            "example_data": kwargs.get("data_example", "[1, 2, 3, 4, 5]"),
        }
        
        return self.TEMPLATE.format(**variables)
    
    def _get_implementation(self, kwargs: Dict[str, Any]) -> str:
        """Get implementation code based on dependencies.
        
        Args:
            kwargs: Template variables
            
        Returns:
            Implementation code
        """
        dependencies = kwargs.get("dependencies", [])
        
        if "scipy" in dependencies:
            return "result = stats.ttest_1samp(data, 0)  # Example: one-sample t-test"
        elif "numpy" in dependencies:
            return "result = np.mean(data)  # Example: mean calculation"
        else:
            return "result = analyze_data(data)  # Implement your analysis here"
    
    def _get_return_value(self, kwargs: Dict[str, Any]) -> str:
        """Get return value expression.
        
        Args:
            kwargs: Template variables
            
        Returns:
            Return value expression
        """
        output = kwargs.get("output_requirements", "result")
        
        if output == "number":
            return "result.statistic if hasattr(result, 'statistic') else result"
        elif output == "boolean":
            return "result.pvalue < 0.05 if hasattr(result, 'pvalue') else bool(result)"
        else:
            return "result"
    
    def get_name(self) -> str:
        """Get template name.
        
        Returns:
            Template name
        """
        return "Statistical Method"