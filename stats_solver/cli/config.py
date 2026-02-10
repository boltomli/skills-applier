"""Configuration management for CLI."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class Config:
    """Configuration settings."""
    
    # LLM settings
    llm_provider: str = "ollama"
    llm_host: str = "localhost"
    llm_port: int = 11434
    llm_model: str = "llama3"
    llm_timeout: int = 30
    
    # Application settings
    log_level: str = "INFO"
    max_recommendations: int = 5
    output_dir: str = "output"
    
    # Feature flags
    enable_llm_classification: bool = True
    enable_auto_metadata: bool = True
    enable_code_generation: bool = True
    
    # Skill paths
    skill_base_paths: list[str] = None
    
    def __post_init__(self):
        if self.skill_base_paths is None:
            self.skill_base_paths = []


class ConfigManager:
    """Manager for configuration settings."""
    
    DEFAULT_CONFIG_FILE = "config/default.yaml"
    ENV_CONFIG_FILE = ".env"
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize config manager.
        
        Args:
            config_file: Path to config file
        """
        self.config_file = config_file or Path(self.DEFAULT_CONFIG_FILE)
        self.config = Config()
        self.load_config()
    
    def load_config(self) -> Config:
        """Load configuration from file and environment.
        
        Returns:
            Loaded configuration
        """
        # Load from file
        if self.config_file.exists():
            self._load_from_file()
        
        # Load from environment
        self._load_from_env()
        
        return self.config
    
    def _load_from_file(self):
        """Load configuration from YAML file."""
        try:
            import yaml
            
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data:
                self._apply_config(data)
                logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # LLM settings
        if os.getenv("LLM_PROVIDER"):
            self.config.llm_provider = os.getenv("LLM_PROVIDER")
        if os.getenv("LLM_HOST"):
            self.config.llm_host = os.getenv("LLM_HOST")
        if os.getenv("LLM_PORT"):
            self.config.llm_port = int(os.getenv("LLM_PORT"))
        if os.getenv("LLM_MODEL"):
            self.config.llm_model = os.getenv("LLM_MODEL")
        if os.getenv("LLM_TIMEOUT"):
            self.config.llm_timeout = int(os.getenv("LLM_TIMEOUT"))
        
        # Application settings
        if os.getenv("LOG_LEVEL"):
            self.config.log_level = os.getenv("LOG_LEVEL")
        if os.getenv("MAX_RECOMMENDATIONS"):
            self.config.max_recommendations = int(os.getenv("MAX_RECOMMENDATIONS"))
        if os.getenv("OUTPUT_DIR"):
            self.config.output_dir = os.getenv("OUTPUT_DIR")
        
        # Feature flags
        if os.getenv("ENABLE_LLM_CLASSIFICATION"):
            self.config.enable_llm_classification = os.getenv("ENABLE_LLM_CLASSIFICATION").lower() == "true"
        if os.getenv("ENABLE_AUTO_METADATA"):
            self.config.enable_auto_metadata = os.getenv("ENABLE_AUTO_METADATA").lower() == "true"
        if os.getenv("ENABLE_CODE_GENERATION"):
            self.config.enable_code_generation = os.getenv("ENABLE_CODE_GENERATION").lower() == "true"
        
        # Skill paths
        if os.getenv("SKILL_BASE_PATH"):
            paths = os.getenv("SKILL_BASE_PATH").split(",")
            self.config.skill_base_paths = [p.strip() for p in paths]
    
    def _apply_config(self, data: Dict[str, Any]):
        """Apply configuration data to config object.
        
        Args:
            data: Configuration dictionary
        """
        # LLM settings
        if "llm" in data:
            llm = data["llm"]
            if "provider" in llm:
                self.config.llm_provider = llm["provider"]
            if "host" in llm:
                self.config.llm_host = llm["host"]
            if "port" in llm:
                self.config.llm_port = llm["port"]
            if "model" in llm:
                self.config.llm_model = llm["model"]
            if "timeout" in llm:
                self.config.llm_timeout = llm["timeout"]
        
        # Application settings
        if "app" in data:
            app = data["app"]
            if "log_level" in app:
                self.config.log_level = app["log_level"]
            if "max_recommendations" in app:
                self.config.max_recommendations = app["max_recommendations"]
            if "output_dir" in app:
                self.config.output_dir = app["output_dir"]
        
        # Feature flags
        if "features" in data:
            features = data["features"]
            if "enable_llm_classification" in features:
                self.config.enable_llm_classification = features["enable_llm_classification"]
            if "enable_auto_metadata" in features:
                self.config.enable_auto_metadata = features["enable_auto_metadata"]
            if "enable_code_generation" in features:
                self.config.enable_code_generation = features["enable_code_generation"]
        
        # Skill paths
        if "skills" in data and "base_paths" in data["skills"]:
            self.config.skill_base_paths = data["skills"]["base_paths"]
    
    def save_config(self, config_file: Optional[Path] = None) -> bool:
        """Save configuration to file.
        
        Args:
            config_file: Path to save config (uses default if None)
            
        Returns:
            True if successful
        """
        target_file = config_file or self.config_file
        
        try:
            import yaml
            
            data = {
                "llm": {
                    "provider": self.config.llm_provider,
                    "host": self.config.llm_host,
                    "port": self.config.llm_port,
                    "model": self.config.llm_model,
                    "timeout": self.config.llm_timeout,
                },
                "app": {
                    "log_level": self.config.log_level,
                    "max_recommendations": self.config.max_recommendations,
                    "output_dir": self.config.output_dir,
                },
                "features": {
                    "enable_llm_classification": self.config.enable_llm_classification,
                    "enable_auto_metadata": self.config.enable_auto_metadata,
                    "enable_code_generation": self.config.enable_code_generation,
                },
                "skills": {
                    "base_paths": self.config.skill_base_paths,
                },
            }
            
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Saved configuration to {target_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        parts = key.split(".")
        value = self.config
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
            
        Returns:
            True if successful
        """
        parts = key.split(".")
        obj = self.config
        
        # Navigate to parent object
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                logger.error(f"Invalid config key: {key}")
                return False
        
        # Set value
        if hasattr(obj, parts[-1]):
            setattr(obj, parts[-1], value)
            logger.info(f"Set config: {key} = {value}")
            return True
        else:
            logger.error(f"Invalid config key: {key}")
            return False
    
    def display_config(self):
        """Display current configuration."""
        console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")
        
        # LLM configuration
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        table.add_column("Description")
        
        # LLM settings
        table.add_row("LLM Provider", self.config.llm_provider, "LLM provider (ollama, lm_studio)")
        table.add_row("LLM Host", self.config.llm_host, "LLM server host")
        table.add_row("LLM Port", str(self.config.llm_port), "LLM server port")
        table.add_row("LLM Model", self.config.llm_model, "Default LLM model")
        table.add_row("LLM Timeout", str(self.config.llm_timeout), "Connection timeout (seconds)")
        
        console.print(table)
        
        # Application settings
        console.print("\n[bold cyan]Application Settings[/bold cyan]\n")
        
        app_table = Table(show_header=True, header_style="bold magenta")
        app_table.add_column("Setting", style="cyan")
        app_table.add_column("Value")
        app_table.add_column("Description")
        
        app_table.add_row("Log Level", self.config.log_level, "Logging level")
        app_table.add_row("Max Recommendations", str(self.config.max_recommendations), "Maximum recommendations to return")
        app_table.add_row("Output Directory", self.config.output_dir, "Default output directory")
        
        console.print(app_table)
        
        # Feature flags
        console.print("\n[bold cyan]Feature Flags[/bold cyan]\n")
        
        feature_table = Table(show_header=True, header_style="bold magenta")
        feature_table.add_column("Feature", style="cyan")
        feature_table.add_column("Enabled")
        feature_table.add_column("Description")
        
        feature_table.add_row(
            "LLM Classification",
            "Yes" if self.config.enable_llm_classification else "No",
            "Use LLM for skill classification"
        )
        feature_table.add_row(
            "Auto Metadata",
            "Yes" if self.config.enable_auto_metadata else "No",
            "Automatically generate skill metadata"
        )
        feature_table.add_row(
            "Code Generation",
            "Yes" if self.config.enable_code_generation else "No",
            "Enable code generation features"
        )
        
        console.print(feature_table)
        
        # Skill paths
        if self.config.skill_base_paths:
            console.print("\n[bold cyan]Skill Base Paths[/bold cyan]\n")
            for path in self.config.skill_base_paths:
                console.print(f"  • {path}")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Validate LLM settings
        if self.config.llm_port < 1 or self.config.llm_port > 65535:
            issues.append(f"Invalid LLM port: {self.config.llm_port}")
        
        if self.config.llm_timeout < 1:
            issues.append(f"Invalid LLM timeout: {self.config.llm_timeout}")
        
        # Validate application settings
        if self.config.max_recommendations < 1:
            issues.append(f"Invalid max_recommendations: {self.config.max_recommendations}")
        
        # Validate skill paths
        for path in self.config.skill_base_paths:
            if not Path(path).exists():
                warnings.append(f"Skill path does not exist: {path}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = Config()
        console.print("[yellow]Configuration reset to defaults.[/yellow]")
    
    def export_env_file(self, env_file: Optional[Path] = None) -> bool:
        """Export configuration to .env file.
        
        Args:
            env_file: Path to save .env file
            
        Returns:
            True if successful
        """
        target_file = env_file or Path(self.ENV_CONFIG_FILE)
        
        try:
            env_content = f"""# LLM Configuration
LLM_PROVIDER={self.config.llm_provider}
LLM_HOST={self.config.llm_host}
LLM_PORT={self.config.llm_port}
LLM_MODEL={self.config.llm_model}
LLM_TIMEOUT={self.config.llm_timeout}

# Application Settings
LOG_LEVEL={self.config.log_level}
MAX_RECOMMENDATIONS={self.config.max_recommendations}
OUTPUT_DIR={self.config.output_dir}

# Feature Flags
ENABLE_LLM_CLASSIFICATION={str(self.config.enable_llm_classification).lower()}
ENABLE_AUTO_METADATA={str(self.config.enable_auto_metadata).lower()}
ENABLE_CODE_GENERATION={str(self.config.enable_code_generation).lower()}

# Skill Paths
SKILL_BASE_PATH={','.join(self.config.skill_base_paths)}
"""
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            
            logger.info(f"Exported configuration to {target_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export .env file: {e}")
            return False