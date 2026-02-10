"""Template for data analysis tasks."""

from typing import Dict, Any
from .base import BaseTemplate


class DataAnalysisTemplate(BaseTemplate):
    """Template for data analysis implementations."""
    
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
    import pandas as pd
    import numpy as np
    
    # Load and validate data
    {data_loading}
    
    # Perform analysis
    {implementation}
    
    return {return_value}


if __name__ == "__main__":
    # Example usage
    {example_usage}
'''
    
    def render(self, **kwargs: Any) -> str:
        """Render the data analysis template.
        
        Args:
            **kwargs: Template variables
            
        Returns:
            Rendered template
        """
        variables = {
            "function_name": kwargs.get("skill_id", "analyze_data").replace("-", "_"),
            "docstring": kwargs.get("description", "Perform data analysis"),
            "params": self._get_params(kwargs),
            "param_docs": self._get_param_docs(kwargs),
            "return_type": kwargs.get("output_requirements", "dict"),
            "return_description": kwargs.get("output_requirements", "Analysis results"),
            "example_call": kwargs.get("example_call", "# Example"),
            "example_args": kwargs.get("example_args", "data"),
            "data_loading": self._get_data_loading(kwargs),
            "implementation": self._get_implementation(kwargs),
            "return_value": self._get_return_value(kwargs),
            "example_usage": kwargs.get("example_usage", "results = analyze_data('data.csv')"),
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
        return """data : str or DataFrame
        Path to data file or pandas DataFrame
    *args : additional positional arguments
        Additional arguments
    **kwargs : additional keyword arguments
        Additional keyword arguments"""
    
    def _get_data_loading(self, kwargs: Dict[str, Any]) -> str:
        """Get data loading code.
        
        Args:
            kwargs: Template variables
            
        Returns:
            Data loading code
        """
        return """if isinstance(data, str):
        df = pd.read_csv(data)
    else:
        df = pd.DataFrame(data)
    
    if df.empty:
        raise ValueError("Data cannot be empty")"""
    
    def _get_implementation(self, kwargs: Dict[str, Any]) -> str:
        """Get implementation code.
        
        Args:
            kwargs: Template variables
            
        Returns:
            Implementation code
        """
        return """results = {{
        'summary': df.describe(),
        'shape': df.shape,
        'columns': df.columns.tolist()
    }}"""
    
    def _get_return_value(self, kwargs: Dict[str, Any]) -> str:
        """Get return value expression.
        
        Args:
            kwargs: Template variables
            
        Returns:
            Return value expression
        """
        return "results"
    
    def get_name(self) -> str:
        """Get template name.
        
        Returns:
            Template name
        """
        return "Data Analysis"