"""LLM-based metadata extractor for skills."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .metadata_schema import SkillMetadata, SkillCategory, DataType
from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class LLMMetadataExtractor:
    """Extract enriched metadata from skills using LLM."""
    
    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize LLM metadata extractor.
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm_provider = llm_provider
    
    async def extract_metadata(
        self,
        skill_path: Path,
        basic_metadata: Optional[SkillMetadata] = None
    ) -> SkillMetadata:
        """Extract full metadata from a skill directory.
        
        Args:
            skill_path: Path to the skill directory
            basic_metadata: Optional existing basic metadata to enhance
            
        Returns:
            Complete skill metadata
        """
        # Read skill files
        code_content = self._read_skill_files(skill_path)
        
        if not code_content:
            logger.warning(f"No Python files found in {skill_path}")
            return basic_metadata or SkillMetadata(
                name=skill_path.name,
                id=skill_path.name,
                path=str(skill_path),
                category=SkillCategory.MATHEMATICAL_IMPLEMENTATION,
                description="No metadata available",
            )
        
        # Build prompt
        prompt = self._build_extraction_prompt(skill_path.name, code_content)
        
        try:
            result = await self.llm_provider.generate_json(
                prompt,
                system_prompt="You are an expert in mathematics, statistics, and Python programming. Extract structured metadata from code.",
            )
            
            # Create or update metadata
            if basic_metadata:
                metadata = basic_metadata
            else:
                metadata = SkillMetadata(
                    name=result.get("name", skill_path.name),
                    id=skill_path.name,
                    path=str(skill_path),
                    category=SkillCategory(result.get("category", "mathematical_implementation")),
                    description=result.get("description", ""),
                )
            
            # Update fields from LLM result
            self._update_metadata_from_result(metadata, result)
            
            metadata.source = "llm"
            metadata.confidence = result.get("confidence", 0.8)
            
            logger.info(f"Extracted metadata for {skill_path.name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata for {skill_path.name}: {e}")
            # Return basic metadata
            return basic_metadata or SkillMetadata(
                name=skill_path.name,
                id=skill_path.name,
                path=str(skill_path),
                category=SkillCategory.MATHEMATICAL_IMPLEMENTATION,
                description="Metadata extraction failed",
                source="fallback",
            )
    
    def _read_skill_files(self, skill_path: Path) -> str:
        """Read and concatenate Python files from skill directory.
        
        Args:
            skill_path: Path to skill directory
            
        Returns:
            Concatenated code content
        """
        content_parts = []
        
        for item in skill_path.iterdir():
            if item.is_file() and item.suffix == ".py":
                try:
                    code = item.read_text(encoding="utf-8", errors="ignore")
                    content_parts.append(f"# File: {item.name}\n{code}\n")
                except Exception as e:
                    logger.warning(f"Failed to read {item}: {e}")
        
        return "\n".join(content_parts)
    
    def _build_extraction_prompt(self, skill_name: str, code_content: str) -> str:
        """Build metadata extraction prompt.
        
        Args:
            skill_name: Name of the skill
            code_content: Code content to analyze
            
        Returns:
            Prompt string
        """
        # Truncate content if too long (approximate token limit)
        max_length = 8000
        if len(code_content) > max_length:
            code_content = code_content[:max_length] + "\n... [truncated]"
        
        return f"""Analyze the following Python code for a mathematical/statistical skill named "{skill_name}" and extract comprehensive metadata:

```python
{code_content}
```

Return a JSON object with the following fields:
- name: A clean, readable name for this skill
- category: One of: "statistical_method", "mathematical_implementation", "data_analysis", "visualization", "algorithm"
- description: A one-sentence description of what this skill does
- long_description: A detailed description (2-3 sentences) explaining the purpose and use cases
- tags: Array of 5-10 relevant tags (e.g., "hypothesis_testing", "regression", "optimization")
- data_types: Array of applicable input data types (numerical, categorical, time_series, text, boolean, mixed)
- output_format: Format of output if applicable (e.g., "plot", "table", "number", "boolean") or null
- statistical_concept: Main statistical concept if applicable (e.g., "hypothesis_testing", "regression_analysis") or null
- algorithm_name: Name of algorithm if applicable (e.g., "QuickSort", "Dijkstra") or null
- assumptions: Array of statistical assumptions if any (e.g., "normality", "independent_samples")
- use_cases: Array of 3-5 example use cases or problem scenarios
- dependencies: Array of Python library dependencies detected in the code
- complexity: Time/space complexity if applicable (e.g., "O(n log n)") or null
- confidence: Your confidence in this extraction (0.0 to 1.0)"""
    
    def _update_metadata_from_result(self, metadata: SkillMetadata, result: Dict) -> None:
        """Update metadata with extraction result.
        
        Args:
            metadata: Metadata to update
            result: Extraction result from LLM
        """
        # Description
        if "description" in result and result["description"]:
            metadata.description = result["description"]
        
        if "long_description" in result and result["long_description"]:
            metadata.long_description = result["long_description"]
        
        # Category
        if "category" in result:
            try:
                metadata.category = SkillCategory(result["category"])
            except ValueError:
                pass
        
        # Tags
        if "tags" in result:
            for tag in result["tags"]:
                if tag not in metadata.tags:
                    metadata.tags.append(tag)
        
        # Data types
        if "data_types" in result:
            metadata.input_data_types = []
            for dt in result["data_types"]:
                try:
                    metadata.input_data_types.append(DataType(dt))
                except ValueError:
                    pass
        
        # Output format
        if "output_format" in result:
            metadata.output_format = result["output_format"]
        
        # Statistical concept
        if "statistical_concept" in result:
            metadata.statistical_concept = result["statistical_concept"]
        
        # Algorithm name
        if "algorithm_name" in result:
            metadata.algorithm_name = result["algorithm_name"]
        
        # Assumptions
        if "assumptions" in result:
            metadata.assumptions = result["assumptions"]
        
        # Use cases
        if "use_cases" in result:
            metadata.use_cases = result["use_cases"]
        
        # Dependencies
        if "dependencies" in result:
            for dep in result["dependencies"]:
                if dep not in metadata.dependencies:
                    metadata.dependencies.append(dep)
        
        # Complexity
        if "complexity" in result:
            metadata.complexity = result["complexity"]
    
    async def batch_extract(self, skill_paths: List[Path]) -> List[SkillMetadata]:
        """Extract metadata for multiple skills.
        
        Args:
            skill_paths: List of skill directory paths
            
        Returns:
            List of extracted metadata
        """
        results = []
        
        for skill_path in skill_paths:
            metadata = await self.extract_metadata(skill_path)
            results.append(metadata)
        
        logger.info(f"Extracted metadata for {len(results)} skills")
        return results