"""Sample data generator for testing and examples."""

import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import random

from ..skills.metadata_schema import DataType, SkillCategory

logger = logging.getLogger(__name__)


class SampleDataSize(str, Enum):
    """Sample data size categories."""
    
    TINY = "tiny"  # 5-10 items
    SMALL = "small"  # 10-50 items
    MEDIUM = "medium"  # 50-200 items
    LARGE = "large"  # 200-1000 items


@dataclass
class SampleData:
    """Generated sample data."""
    
    data: Any
    description: str
    data_type: DataType
    size: int
    metadata: Dict[str, Any]


class SampleDataGenerator:
    """Generator for sample data for testing and examples."""
    
    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize sample data generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
    
    def generate(
        self,
        data_type: DataType,
        size: SampleDataSize = SampleDataSize.SMALL,
        context: Optional[Dict[str, Any]] = None
    ) -> SampleData:
        """Generate sample data.
        
        Args:
            data_type: Type of data to generate
            size: Size category
            context: Optional context for generation
            
        Returns:
            Generated sample data
        """
        n = self._get_size_value(size)
        
        if data_type == DataType.NUMERICAL:
            return self._generate_numerical(n, context)
        elif data_type == DataType.CATEGORICAL:
            return self._generate_categorical(n, context)
        elif data_type == DataType.TIME_SERIES:
            return self._generate_time_series(n, context)
        elif data_type == DataType.BOOLEAN:
            return self._generate_boolean(n, context)
        elif data_type == DataType.MIXED:
            return self._generate_mixed(n, context)
        else:
            return self._generate_numerical(n, context)
    
    def _get_size_value(self, size: SampleDataSize) -> int:
        """Get numeric size value.
        
        Args:
            size: Size category
            
        Returns:
            Numeric size
        """
        sizes = {
            SampleDataSize.TINY: random.randint(5, 10),
            SampleDataSize.SMALL: random.randint(10, 50),
            SampleDataSize.MEDIUM: random.randint(50, 200),
            SampleDataSize.LARGE: random.randint(200, 1000),
        }
        return sizes[size]
    
    def _generate_numerical(self, n: int, context: Optional[Dict[str, Any]]) -> SampleData:
        """Generate numerical sample data.
        
        Args:
            n: Number of data points
            context: Optional context
            
        Returns:
            Generated numerical data
        """
        # Generate normal distribution by default
        data = [random.gauss(50, 15) for _ in range(n)]
        
        description = f"Sample of {n} numerical values from normal distribution (μ=50, σ=15)"
        
        return SampleData(
            data=data,
            description=description,
            data_type=DataType.NUMERICAL,
            size=n,
            metadata={
                "distribution": "normal",
                "mean": 50,
                "std": 15,
            },
        )
    
    def _generate_categorical(self, n: int, context: Optional[Dict[str, Any]]) -> SampleData:
        """Generate categorical sample data.
        
        Args:
            n: Number of data points
            context: Optional context
            
        Returns:
            Generated categorical data
        """
        categories = ["A", "B", "C", "D"]
        data = [random.choice(categories) for _ in range(n)]
        
        description = f"Sample of {n} categorical values with {len(categories)} categories"
        
        return SampleData(
            data=data,
            description=description,
            data_type=DataType.CATEGORICAL,
            size=n,
            metadata={
                "categories": categories,
                "counts": {cat: data.count(cat) for cat in categories},
            },
        )
    
    def _generate_time_series(self, n: int, context: Optional[Dict[str, Any]]) -> SampleData:
        """Generate time series sample data.
        
        Args:
            n: Number of data points
            context: Optional context
            
        Returns:
            Generated time series data
        """
        # Generate trend + noise
        trend = [i * 0.5 for i in range(n)]
        noise = [random.gauss(0, 2) for _ in range(n)]
        data = [t + n for t, n in zip(trend, noise)]
        
        description = f"Sample of {n} time series points with linear trend and noise"
        
        return SampleData(
            data=data,
            description=description,
            data_type=DataType.TIME_SERIES,
            size=n,
            metadata={
                "trend": "linear",
                "trend_slope": 0.5,
                "noise_std": 2,
            },
        )
    
    def _generate_boolean(self, n: int, context: Optional[Dict[str, Any]]) -> SampleData:
        """Generate boolean sample data.
        
        Args:
            n: Number of data points
            context: Optional context
            
        Returns:
            Generated boolean data
        """
        data = [random.choice([True, False]) for _ in range(n)]
        
        description = f"Sample of {n} boolean values"
        
        return SampleData(
            data=data,
            description=description,
            data_type=DataType.BOOLEAN,
            size=n,
            metadata={
                "true_count": sum(data),
                "false_count": n - sum(data),
            },
        )
    
    def _generate_mixed(self, n: int, context: Optional[Dict[str, Any]]) -> SampleData:
        """Generate mixed sample data.
        
        Args:
            n: Number of data points
            context: Optional context
            
        Returns:
            Generated mixed data
        """
        # Generate dictionary with mixed types
        data = []
        for i in range(n):
            item = {
                "id": i,
                "value": random.gauss(50, 15),
                "category": random.choice(["A", "B", "C"]),
                "flag": random.choice([True, False]),
            }
            data.append(item)
        
        description = f"Sample of {n} mixed-type records"
        
        return SampleData(
            data=data,
            description=description,
            data_type=DataType.MIXED,
            size=n,
            metadata={
                "fields": ["id", "value", "category", "flag"],
            },
        )
    
    def generate_for_skill(
        self,
        category: SkillCategory,
        size: SampleDataSize = SampleDataSize.SMALL
    ) -> SampleData:
        """Generate sample data appropriate for a skill category.
        
        Args:
            category: Skill category
            size: Size category
            
        Returns:
            Generated sample data
        """
        if category == SkillCategory.STATISTICAL_METHOD:
            return self._generate_numerical(self._get_size_value(size), None)
        elif category == SkillCategory.MATHEMATICAL_IMPLEMENTATION:
            return self._generate_numerical(self._get_size_value(size), None)
        elif category == SkillCategory.VISUALIZATION:
            return self._generate_time_series(self._get_size_value(size), None)
        else:
            return self._generate_mixed(self._get_size_value(size), None)
    
    def generate_two_sample_data(
        self,
        size: SampleDataSize = SampleDataSize.SMALL,
        effect_size: float = 0.5
    ) -> Dict[str, SampleData]:
        """Generate two sample datasets for comparison.
        
        Args:
            size: Size category
            effect_size: Effect size between samples
            
        Returns:
            Dictionary with 'sample1' and 'sample2' data
        """
        n = self._get_size_value(size)
        
        # Generate two samples with different means
        sample1_data = [random.gauss(50, 10) for _ in range(n)]
        sample2_data = [random.gauss(50 + effect_size * 10, 10) for _ in range(n)]
        
        sample1 = SampleData(
            data=sample1_data,
            description=f"Sample 1: {n} values from N(50, 10)",
            data_type=DataType.NUMERICAL,
            size=n,
            metadata={"mean": 50, "std": 10},
        )
        
        sample2 = SampleData(
            data=sample2_data,
            description=f"Sample 2: {n} values from N({50 + effect_size * 10}, 10)",
            data_type=DataType.NUMERICAL,
            size=n,
            metadata={"mean": 50 + effect_size * 10, "std": 10},
        )
        
        return {"sample1": sample1, "sample2": sample2}
    
    def generate_code_representation(self, sample_data: SampleData) -> str:
        """Generate Python code representation of sample data.
        
        Args:
            sample_data: Sample data
            
        Returns:
            Python code string
        """
        if sample_data.data_type == DataType.NUMERICAL:
            values = ", ".join([f"{v:.2f}" for v in sample_data.data[:10]])
            if sample_data.size > 10:
                values += ", ..."
            return f"import numpy as np\ndata = np.array([{values}])"
        
        elif sample_data.data_type == DataType.CATEGORICAL:
            values = ", ".join([f"'{v}'" for v in sample_data.data[:10]])
            if sample_data.size > 10:
                values += ", ..."
            return f"data = [{values}]"
        
        elif sample_data.data_type == DataType.BOOLEAN:
            values = ", ".join([str(v) for v in sample_data.data[:10]])
            if sample_data.size > 10:
                values += ", ..."
            return f"data = [{values}]"
        
        elif sample_data.data_type == DataType.TIME_SERIES:
            values = ", ".join([f"{v:.2f}" for v in sample_data.data[:10]])
            if sample_data.size > 10:
                values += ", ..."
            return f"import numpy as np\ndata = np.array([{values}])"
        
        else:
            return f"data = {sample_data.data}"