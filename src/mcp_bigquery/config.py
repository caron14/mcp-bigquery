"""Configuration management for MCP BigQuery server."""

import os
from dataclasses import dataclass, field

from .exceptions import ConfigurationError


@dataclass
class Config:
    """Configuration for MCP BigQuery server."""

    project_id: str | None = field(default=None)
    location: str | None = field(default=None)
    log_level: str = field(default="WARNING")

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            project_id=os.getenv("BQ_PROJECT"),
            location=os.getenv("BQ_LOCATION"),
            log_level=os.getenv("LOG_LEVEL", "WARNING"),
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigurationError(f"Invalid log_level: {self.log_level}")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "project_id": self.project_id,
            "location": self.location,
            "log_level": self.log_level,
        }


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.validate()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    config.validate()
    _config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None
