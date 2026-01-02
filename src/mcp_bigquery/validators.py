"""Input validation models using Pydantic for MCP BigQuery server."""

from __future__ import annotations

try:
    from pydantic import BaseModel, Field, field_validator
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


from .constants import TableType

PROJECT_ID_PATTERN = r"^(?:[a-z][a-z0-9-]{4,28}[a-z0-9]|[a-z0-9.-]+:[a-z][a-z0-9-]{4,28}[a-z0-9])$"


class ListDatasetsRequest(BaseModel):
    """Request model for listing datasets."""

    project_id: str | None = Field(None, pattern=PROJECT_ID_PATTERN)
    max_results: int | None = Field(None, ge=1, le=10000)


class ListTablesRequest(BaseModel):
    """Request model for listing tables."""

    dataset_id: str = Field(..., min_length=1, max_length=1024)
    project_id: str | None = Field(None, pattern=PROJECT_ID_PATTERN)
    max_results: int | None = Field(None, ge=1, le=10000)
    table_type_filter: list[str] | None = Field(None)

    @field_validator("table_type_filter")
    @classmethod
    def validate_table_types(cls, v: list[str] | None) -> list[str] | None:
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
    project_id: str | None = Field(None, pattern=PROJECT_ID_PATTERN)
    format_output: bool = Field(False)


class GetTableInfoRequest(BaseModel):
    """Request model for getting table info."""

    table_id: str = Field(..., min_length=1, max_length=1024)
    dataset_id: str = Field(..., min_length=1, max_length=1024)
    project_id: str | None = Field(None, pattern=PROJECT_ID_PATTERN)


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
                    raise InvalidParameterError(field_name, error_str) from e

        raise InvalidParameterError("request", error_str) from e
    except Exception as e:
        raise InvalidParameterError("request", str(e)) from e
