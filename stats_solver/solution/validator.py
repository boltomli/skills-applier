"""Code validator for checking generated code."""

import logging
import ast
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A validation issue found in code."""
    
    severity: ValidationSeverity
    message: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    suggestion: Optional[str]


@dataclass
class ValidationResult:
    """Result of code validation."""
    
    is_valid: bool
    issues: List[ValidationIssue]
    error_count: int
    warning_count: int
    info_count: int
    summary: str


class CodeValidator:
    """Validator for checking generated Python code."""
    
    # Common error patterns
    ERROR_PATTERNS = {
        "import_error": r"import\s+\w+\s+#\s+(?:missing|not\s+available)",
        "undefined_variable": r"(?:print|return)\s*\(\s*(\w+)\s*\)",
        "syntax_error": r"#\s+(?:syntax\s+error|invalid)",
    }
    
    # Warning patterns
    WARNING_PATTERNS = {
        "deprecated": r"#\s+(?:deprecated|obsolete)",
        "todo": r"#\s+TODO|FIXME|XXX",
        "hardcoded": r"(?:=|==)\s*\d+\s+#\s+(?:hardcoded|magic)",
    }
    
    def __init__(self) -> None:
        """Initialize code validator."""
        pass
    
    def validate(self, code: str) -> ValidationResult:
        """Validate generated code.
        
        Args:
            code: Python code to validate
            
        Returns:
            Validation result
        """
        issues = []
        
        # Check syntax
        syntax_issues = self._check_syntax(code)
        issues.extend(syntax_issues)
        
        # Check imports
        import_issues = self._check_imports(code)
        issues.extend(import_issues)
        
        # Check structure
        structure_issues = self._check_structure(code)
        issues.extend(structure_issues)
        
        # Check style
        style_issues = self._check_style(code)
        issues.extend(style_issues)
        
        # Check best practices
        practice_issues = self._check_best_practices(code)
        issues.extend(practice_issues)
        
        # Count by severity
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)
        
        is_valid = error_count == 0
        summary = self._generate_summary(is_valid, error_count, warning_count, info_count)
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            summary=summary,
        )
    
    def _check_syntax(self, code: str) -> List[ValidationIssue]:
        """Check for syntax errors.
        
        Args:
            code: Code to check
            
        Returns:
            List of syntax issues
        """
        issues = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                code_snippet=self._get_line(code, e.lineno),
                suggestion="Fix the syntax error in the code",
            ))
        
        return issues
    
    def _check_imports(self, code: str) -> List[ValidationIssue]:
        """Check import statements.
        
        Args:
            code: Code to check
            
        Returns:
            List of import issues
        """
        issues = []
        
        # Check for duplicate imports
        import_pattern = r"^\s*(?:import|from)\s+(\S+)"
        imports = re.findall(import_pattern, code, re.MULTILINE)
        
        if len(imports) != len(set(imports)):
            duplicates = [imp for imp in imports if imports.count(imp) > 1]
            for dup in set(duplicates):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Duplicate import: {dup}",
                    line_number=None,
                    code_snippet=f"import {dup}",
                    suggestion="Remove duplicate import statements",
                ))
        
        # Check for unused imports (simple check)
        tree = ast.parse(code)
        imported_names = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = imported_names - used_names
        for name in unused:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message=f"Unused import: {name}",
                line_number=None,
                code_snippet=f"import {name}",
                suggestion="Remove unused import statements",
            ))
        
        return issues
    
    def _check_structure(self, code: str) -> List[ValidationIssue]:
        """Check code structure.
        
        Args:
            code: Code to check
            
        Returns:
            List of structure issues
        """
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Check for docstrings
            has_docstring = False
            if tree.body and isinstance(tree.body[0], ast.Expr):
                if isinstance(tree.body[0].value, ast.Constant):
                    has_docstring = isinstance(tree.body[0].value.value, str)
            
            if not has_docstring:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Missing module docstring",
                    line_number=1,
                    code_snippet=code.split("\n")[0],
                    suggestion="Add a module-level docstring",
                ))
            
            # Check for functions without docstrings
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not (node.body and isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant) and
                           isinstance(node.body[0].value.value, str)):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"Function '{node.name}' missing docstring",
                            line_number=node.lineno,
                            code_snippet=f"def {node.name}(...):",
                            suggestion="Add a docstring to the function",
                        ))
        
        except Exception as e:
            logger.warning(f"Could not check structure: {e}")
        
        return issues
    
    def _check_style(self, code: str) -> List[ValidationIssue]:
        """Check code style.
        
        Args:
            code: Code to check
            
        Returns:
            List of style issues
        """
        issues = []
        lines = code.split("\n")
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 100:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message=f"Line too long ({len(line)} characters)",
                    line_number=i,
                    code_snippet=line[:50] + "...",
                    suggestion="Break long lines into multiple lines",
                ))
            
            # Check for trailing whitespace
            if line != line.rstrip():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Trailing whitespace",
                    line_number=i,
                    code_snippet=line,
                    suggestion="Remove trailing whitespace",
                ))
        
        return issues
    
    def _check_best_practices(self, code: str) -> List[ValidationIssue]:
        """Check Python best practices.
        
        Args:
            code: Code to check
            
        Returns:
            List of best practice issues
        """
        issues = []
        
        # Check for bare except
        bare_except_pattern = r"except\s*:"
        if re.search(bare_except_pattern, code):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Bare except clause",
                line_number=None,
                code_snippet="except:",
                suggestion="Specify exception type to catch",
            ))
        
        # Check for print statements in functions (except main block)
        print_pattern = r"print\s*\("
        if re.search(print_pattern, code):
            # Check if it's in main block
            if "__main__" not in code:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Print statement found (consider using logging)",
                    line_number=None,
                    code_snippet="print(",
                    suggestion="Use logging module instead of print",
                ))
        
        # Check for magic numbers
        magic_number_pattern = r"(?:[^a-zA-Z_]|^)\b\d{3,}\b(?![a-zA-Z])"
        if re.search(magic_number_pattern, code):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Magic number found",
                line_number=None,
                code_snippet=None,
                suggestion="Define magic numbers as constants",
            ))
        
        return issues
    
    def _get_line(self, code: str, line_number: Optional[int]) -> Optional[str]:
        """Get a specific line from code.
        
        Args:
            code: Code string
            line_number: Line number (1-indexed)
            
        Returns:
            Line content or None
        """
        if line_number is None:
            return None
        
        lines = code.split("\n")
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return None
    
    def _generate_summary(
        self,
        is_valid: bool,
        error_count: int,
        warning_count: int,
        info_count: int
    ) -> str:
        """Generate validation summary.
        
        Args:
            is_valid: Whether code is valid
            error_count: Number of errors
            warning_count: Number of warnings
            info_count: Number of info messages
            
        Returns:
            Summary string
        """
        if is_valid:
            if warning_count == 0 and info_count == 0:
                return "Code is valid with no issues"
            else:
                parts = []
                if warning_count > 0:
                    parts.append(f"{warning_count} warning(s)")
                if info_count > 0:
                    parts.append(f"{info_count} info message(s)")
                return f"Code is valid with {', '.join(parts)}"
        else:
            return f"Code is invalid: {error_count} error(s), {warning_count} warning(s), {info_count} info message(s)"
    
    def fix_issues(self, code: str, issues: List[ValidationIssue]) -> str:
        """Attempt to automatically fix validation issues.
        
        Args:
            code: Code to fix
            issues: Issues to fix
            
        Returns:
            Fixed code
        """
        fixed_code = code
        
        for issue in issues:
            if issue.severity == ValidationSeverity.INFO and issue.message == "Trailing whitespace":
                # Remove trailing whitespace
                if issue.line_number:
                    lines = fixed_code.split("\n")
                    if 1 <= issue.line_number <= len(lines):
                        lines[issue.line_number - 1] = lines[issue.line_number - 1].rstrip()
                    fixed_code = "\n".join(lines)
        
        return fixed_code
    
    def validate_batch(self, codes: List[str]) -> List[ValidationResult]:
        """Validate multiple code snippets.
        
        Args:
            codes: List of code snippets
            
        Returns:
            List of validation results
        """
        return [self.validate(code) for code in codes]