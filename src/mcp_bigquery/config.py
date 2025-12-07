"""Configuration management for MCP BigQuery server."""

import os
from dataclasses import dataclass, field

from .exceptions import ConfigurationError


@dataclass
class Config:
    """Configuration for MCP BigQuery server."""

    # BigQuery settings
    project_id: str | None = field(default=None)
    location: str | None = field(default=None)

    # Pricing settings
    price_per_tib: float = field(default=5.0)

    # Logging settings
    debug: bool = field(default=False)
    log_level: str = field(default="WARNING")

    # Performance settings
    max_results: int = field(default=1000)
    query_timeout: int = field(default=30)  # seconds
    cache_enabled: bool = field(default=True)
    cache_ttl: int = field(default=300)  # seconds

    # Connection pooling
    max_connections: int = field(default=10)
    connection_timeout: int = field(default=10)  # seconds

    # Rate limiting
    rate_limit_enabled: bool = field(default=False)
    requests_per_minute: int = field(default=60)

    # Schema discovery limits
    max_datasets: int = field(default=100)
    max_tables_per_dataset: int = field(default=1000)
    max_schema_depth: int = field(default=15)  # For nested fields

    # Security settings
    validate_sql_injection: bool = field(default=True)
    max_query_length: int = field(default=100000)  # characters
    max_parameter_count: int = field(default=100)

    # Feature flags
    enable_query_analysis: bool = field(default=True)
    enable_schema_discovery: bool = field(default=True)
    enable_performance_analysis: bool = field(default=True)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            project_id=os.getenv("BQ_PROJECT"),
            location=os.getenv("BQ_LOCATION"),
            price_per_tib=float(os.getenv("SAFE_PRICE_PER_TIB", "5.0")),
            debug=bool(os.getenv("DEBUG")),
            log_level=os.getenv("LOG_LEVEL", "WARNING"),
            max_results=int(os.getenv("MAX_RESULTS", "1000")),
            query_timeout=int(os.getenv("QUERY_TIMEOUT", "30")),
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "300")),
            max_connections=int(os.getenv("MAX_CONNECTIONS", "10")),
            connection_timeout=int(os.getenv("CONNECTION_TIMEOUT", "10")),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true",
            requests_per_minute=int(os.getenv("REQUESTS_PER_MINUTE", "60")),
            max_datasets=int(os.getenv("MAX_DATASETS", "100")),
            max_tables_per_dataset=int(os.getenv("MAX_TABLES_PER_DATASET", "1000")),
            max_schema_depth=int(os.getenv("MAX_SCHEMA_DEPTH", "15")),
            validate_sql_injection=os.getenv("VALIDATE_SQL_INJECTION", "true").lower() == "true",
            max_query_length=int(os.getenv("MAX_QUERY_LENGTH", "100000")),
            max_parameter_count=int(os.getenv("MAX_PARAMETER_COUNT", "100")),
            enable_query_analysis=os.getenv("ENABLE_QUERY_ANALYSIS", "true").lower() == "true",
            enable_schema_discovery=os.getenv("ENABLE_SCHEMA_DISCOVERY", "true").lower() == "true",
            enable_performance_analysis=os.getenv("ENABLE_PERFORMANCE_ANALYSIS", "true").lower()
            == "true",
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if self.price_per_tib <= 0:
            raise ConfigurationError("price_per_tib must be positive")

        if self.max_results <= 0:
            raise ConfigurationError("max_results must be positive")

        if self.query_timeout <= 0:
            raise ConfigurationError("query_timeout must be positive")

        if self.cache_ttl < 0:
            raise ConfigurationError("cache_ttl must be non-negative")

        if self.max_connections <= 0:
            raise ConfigurationError("max_connections must be positive")

        if self.connection_timeout <= 0:
            raise ConfigurationError("connection_timeout must be positive")

        if self.rate_limit_enabled and self.requests_per_minute <= 0:
            raise ConfigurationError(
                "requests_per_minute must be positive when rate limiting is enabled"
            )

        if self.max_query_length <= 0:
            raise ConfigurationError("max_query_length must be positive")

        if self.max_parameter_count <= 0:
            raise ConfigurationError("max_parameter_count must be positive")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigurationError(f"Invalid log_level: {self.log_level}")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "project_id": self.project_id,
            "location": self.location,
            "price_per_tib": self.price_per_tib,
            "debug": self.debug,
            "log_level": self.log_level,
            "max_results": self.max_results,
            "query_timeout": self.query_timeout,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "rate_limit_enabled": self.rate_limit_enabled,
            "requests_per_minute": self.requests_per_minute,
            "max_datasets": self.max_datasets,
            "max_tables_per_dataset": self.max_tables_per_dataset,
            "max_schema_depth": self.max_schema_depth,
            "validate_sql_injection": self.validate_sql_injection,
            "max_query_length": self.max_query_length,
            "max_parameter_count": self.max_parameter_count,
            "enable_query_analysis": self.enable_query_analysis,
            "enable_schema_discovery": self.enable_schema_discovery,
            "enable_performance_analysis": self.enable_performance_analysis,
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
