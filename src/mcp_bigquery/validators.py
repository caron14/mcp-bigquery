"""Input validation models using Pydantic for MCP BigQuery server."""

from __future__ import annotations

from typing import Annotated, Any, TypeVar

from pydantic import BaseModel, Field, ValidationError, field_validator

from .constants import TableType
from .exceptions import InvalidParameterError

PROJECT_ID_PATTERN = r"^(?:[a-z][a-z0-9-]{4,28}[a-z0-9]|[a-z0-9.-]+:[a-z][a-z0-9-]{4,28}[a-z0-9])$"

# Common custom types to make the validation definitions DRY
ProjectId = Annotated[str, Field(pattern=PROJECT_ID_PATTERN)]
DatasetId = Annotated[str, Field(min_length=1, max_length=1024)]
TableId = Annotated[str, Field(min_length=1, max_length=1024)]

T = TypeVar("T", bound=BaseModel)


class ListDatasetsRequest(BaseModel):
    """Request model for listing datasets."""

    project_id: ProjectId | None = Field(None)
    max_results: int | None = Field(None, ge=1, le=10000)


class ListTablesRequest(BaseModel):
    """Request model for listing tables."""

    dataset_id: DatasetId
    project_id: ProjectId | None = Field(None)
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

    table_id: TableId
    dataset_id: DatasetId
    project_id: ProjectId | None = Field(None)
    format_output: bool = Field(False)


class GetTableInfoRequest(BaseModel):
    """Request model for getting table info."""

    table_id: TableId
    dataset_id: DatasetId
    project_id: ProjectId | None = Field(None)


class PreviewTableRequest(BaseModel):
    """Request model for previewing table data."""

    dataset_id: DatasetId
    table_id: TableId
    project_id: ProjectId | None = Field(None)
    max_results: int = Field(5, ge=1)


def validate_request(request_class: type[T], data: dict[str, Any]) -> T:
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
    try:
        return request_class(**data)
    except ValidationError as e:
        # Smart ValidationError parsing mapping to clear InvalidParameterError
        errors = e.errors()
        if errors:
            first_error = errors[0]
            loc = first_error.get("loc", ())
            field_name = str(loc[0]) if loc else "request"
            msg = first_error.get("msg", "Validation error")
            raise InvalidParameterError(
                field_name, f"Validation error for field '{field_name}': {msg}"
            ) from e
        raise InvalidParameterError("request", str(e)) from e
    except Exception as e:
        raise InvalidParameterError("request", str(e)) from e
