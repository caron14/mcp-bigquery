"""Input validation models using Pydantic for MCP BigQuery server."""

from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
except ImportError:
    # Fallback for when Pydantic is not installed
    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def Field(default=None, **kwargs):
        return default

    def field_validator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def model_validator(**kwargs):
        def decorator(func):
            return func

        return decorator


from .constants import DEFAULT_LIMITS, TableType


class SQLValidationRequest(BaseModel):
    """Request model for SQL validation."""

    sql: str = Field(..., min_length=1, max_length=DEFAULT_LIMITS["max_query_length"])
    params: Optional[Dict[str, Any]] = Field(None, max_length=DEFAULT_LIMITS["max_parameter_count"])

    @field_validator("sql")
    @classmethod
    def validate_sql_not_empty(cls, v: str) -> str:
        """Ensure SQL is not just whitespace."""
        if not v.strip():
            raise ValueError("SQL query cannot be empty or only whitespace")
        return v

    @field_validator("params")
    @classmethod
    def validate_param_names(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate parameter names are alphanumeric with underscores."""
        if v is None:
            return v

        import re

        for param_name in v.keys():
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", param_name):
                raise ValueError(f"Invalid parameter name: {param_name}")

        return v


class DryRunRequest(BaseModel):
    """Request model for dry-run analysis."""

    sql: str = Field(..., min_length=1, max_length=DEFAULT_LIMITS["max_query_length"])
    params: Optional[Dict[str, Any]] = Field(None, max_length=DEFAULT_LIMITS["max_parameter_count"])
    pricePerTiB: Optional[float] = Field(None, gt=0, le=1000)

    @field_validator("sql")
    @classmethod
    def validate_sql_not_empty(cls, v: str) -> str:
        """Ensure SQL is not just whitespace."""
        if not v.strip():
            raise ValueError("SQL query cannot be empty or only whitespace")
        return v


class QueryAnalysisRequest(BaseModel):
    """Request model for query analysis."""

    sql: str = Field(..., min_length=1, max_length=DEFAULT_LIMITS["max_query_length"])
    params: Optional[Dict[str, Any]] = Field(None, max_length=DEFAULT_LIMITS["max_parameter_count"])

    @field_validator("sql")
    @classmethod
    def validate_sql_not_empty(cls, v: str) -> str:
        """Ensure SQL is not just whitespace."""
        if not v.strip():
            raise ValueError("SQL query cannot be empty or only whitespace")
        return v


class ListDatasetsRequest(BaseModel):
    """Request model for listing datasets."""

    project_id: Optional[str] = Field(None, pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
    max_results: Optional[int] = Field(DEFAULT_LIMITS["max_results"], ge=1, le=10000)


class ListTablesRequest(BaseModel):
    """Request model for listing tables."""

    dataset_id: str = Field(..., min_length=1, max_length=1024)
    project_id: Optional[str] = Field(None, pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
    max_results: Optional[int] = Field(DEFAULT_LIMITS["max_results"], ge=1, le=10000)
    table_type_filter: Optional[List[str]] = Field(None)

    @field_validator("table_type_filter")
    @classmethod
    def validate_table_types(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate table types are valid."""
        if v is None:
            return v

        valid_types = {t.value for t in TableType}
        for table_type in v:
            if table_type not in valid_types:
                raise ValueError(f"Invalid table type: {table_type}. Must be one of {valid_types}")

        return v


class DescribeTableRequest(BaseModel):
    """Request model for describing a table."""

    table_id: str = Field(..., min_length=1, max_length=1024)
    dataset_id: str = Field(..., min_length=1, max_length=1024)
    project_id: Optional[str] = Field(None, pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
    format_output: bool = Field(False)


class GetTableInfoRequest(BaseModel):
    """Request model for getting table info."""

    table_id: str = Field(..., min_length=1, max_length=1024)
    dataset_id: str = Field(..., min_length=1, max_length=1024)
    project_id: Optional[str] = Field(None, pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")


class QueryInfoSchemaRequest(BaseModel):
    """Request model for querying INFORMATION_SCHEMA."""

    query_type: str = Field(
        ..., pattern=r"^(tables|columns|table_storage|partitions|views|routines|custom)$"
    )
    dataset_id: str = Field(..., min_length=1, max_length=1024)
    project_id: Optional[str] = Field(None, pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
    table_filter: Optional[str] = Field(None, max_length=1024)
    custom_query: Optional[str] = Field(None, max_length=DEFAULT_LIMITS["max_query_length"])
    limit: int = Field(DEFAULT_LIMITS["info_schema_limit"], ge=1, le=10000)

    @model_validator(mode="after")
    def validate_custom_query(self) -> "QueryInfoSchemaRequest":
        """Validate custom_query is provided when query_type is 'custom'."""
        if self.query_type == "custom" and not self.custom_query:
            raise ValueError("custom_query is required when query_type is 'custom'")

        if self.query_type != "custom" and self.custom_query:
            raise ValueError("custom_query should only be provided when query_type is 'custom'")

        return self


class AnalyzePerformanceRequest(BaseModel):
    """Request model for analyzing query performance."""

    sql: str = Field(..., min_length=1, max_length=DEFAULT_LIMITS["max_query_length"])
    project_id: Optional[str] = Field(None, pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")

    @field_validator("sql")
    @classmethod
    def validate_sql_not_empty(cls, v: str) -> str:
        """Ensure SQL is not just whitespace."""
        if not v.strip():
            raise ValueError("SQL query cannot be empty or only whitespace")
        return v


def validate_request(request_class: type[BaseModel], data: dict) -> BaseModel:
    """
    Validate request data using a Pydantic model.

    Args:
        request_class: The Pydantic model class to use for validation
        data: The data to validate

    Returns:
        Validated model instance

    Raises:
        InvalidParameterError: If validation fails
    """
    from .exceptions import InvalidParameterError

    try:
        return request_class(**data)
    except ValueError as e:
        # Parse Pydantic error to get field name
        error_str = str(e)
        if "validation error" in error_str.lower():
            # Extract field name from error message
            lines = error_str.split("\n")
            for line in lines:
                if "->" in line:
                    field_name = line.split("->")[0].strip()
                    raise InvalidParameterError(field_name, error_str)

        raise InvalidParameterError("request", error_str)
    except Exception as e:
        raise InvalidParameterError("request", str(e))
