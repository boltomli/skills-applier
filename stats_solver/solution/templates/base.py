"""Base template class for code generation."""

from abc import ABC, abstractmethod
from typing import Any


class BaseTemplate(ABC):
    """Base class for code templates."""

    @abstractmethod
    def render(self, **kwargs: Any) -> str:
        """Render the template with the given variables.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered template string
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the template name.

        Returns:
            Template name
        """
        pass
