"""Type definitions for MCP BigQuery server."""

from typing import Any, TypedDict


# Base error types
class ErrorLocation(TypedDict):
    """Error location information."""

    line: int
    column: int


class ErrorInfo(TypedDict):
    """Error information structure."""

    code: str
    message: str
    location: ErrorLocation | None
    details: list[Any] | None


# SQL validation response types
class ValidSQLResponse(TypedDict):
    """Response for valid SQL."""

    isValid: bool


class InvalidSQLResponse(TypedDict):
    """Response for invalid SQL."""

    isValid: bool
    error: ErrorInfo


# Table reference types
class TableReference(TypedDict):
    """BigQuery table reference."""

    project: str | None
    dataset: str
    table: str
    full_name: str | None


class FullTableReference(TypedDict):
    """Complete BigQuery table reference."""

    project: str
    dataset: str
    table: str
    full_id: str | None


# Schema field types
class SchemaField(TypedDict):
    """BigQuery schema field."""

    name: str
    type: str
    mode: str
    description: str | None
    fields: list["SchemaField"] | None  # For nested fields


# Dry-run response types
class DryRunSuccessResponse(TypedDict):
    """Successful dry-run response."""

    totalBytesProcessed: int
    usdEstimate: float
    referencedTables: list[FullTableReference]
    schemaPreview: list[SchemaField]


class DryRunErrorResponse(TypedDict):
    """Error response for dry-run."""

    error: ErrorInfo


# Query structure analysis types
class QueryStructureResponse(TypedDict):
    """Query structure analysis response."""

    query_type: str
    has_joins: bool
    has_subqueries: bool
    has_cte: bool
    has_aggregations: bool
    has_window_functions: bool
    has_union: bool
    table_count: int
    complexity_score: int
    join_types: list[str]
    functions_used: list[str]


# Dependency extraction types
class DependencyResponse(TypedDict):
    """Dependency extraction response."""

    tables: list[TableReference]
    columns: list[str]
    dependency_graph: dict[str, list[str]]
    table_count: int
    column_count: int


# Syntax validation types
class ValidationIssue(TypedDict):
    """Validation issue details."""

    type: str
    message: str
    severity: str


class BigQuerySpecificFeatures(TypedDict):
    """BigQuery-specific syntax features."""

    uses_legacy_sql: bool
    has_array_syntax: bool
    has_struct_syntax: bool


class SyntaxValidationResponse(TypedDict):
    """Enhanced syntax validation response."""

    is_valid: bool
    issues: list[ValidationIssue]
    suggestions: list[str]
    bigquery_specific: BigQuerySpecificFeatures


# Dataset types
class DatasetInfo(TypedDict):
    """Dataset information."""

    dataset_id: str
    project: str
    location: str
    created: str
    modified: str
    description: str | None
    labels: dict[str, str]
    default_table_expiration_ms: int | None
    default_partition_expiration_ms: int | None


class DatasetListResponse(TypedDict):
    """Dataset list response."""

    project: str
    dataset_count: int
    datasets: list[DatasetInfo]


# Table partitioning and clustering types
class PartitioningInfo(TypedDict):
    """Table partitioning information."""

    type: str
    field: str | None
    expiration_ms: int | None
    require_partition_filter: bool | None


class TimePartitioning(TypedDict):
    """Time-based partitioning details."""

    type: str
    field: str | None
    require_partition_filter: bool


# Table information types
class TableStatistics(TypedDict):
    """Table statistics."""

    num_bytes: int
    num_rows: int
    num_long_term_bytes: int | None
    creation_time: str | None
    num_active_logical_bytes: int | None
    num_long_term_logical_bytes: int | None


class TableInfo(TypedDict):
    """Table information."""

    table_id: str
    dataset_id: str
    project: str
    table_type: str
    created: str
    modified: str
    description: str | None
    labels: dict[str, str]
    num_bytes: int
    num_rows: int
    location: str
    partitioning: PartitioningInfo | None
    clustering_fields: list[str] | None


class TableListResponse(TypedDict):
    """Table list response."""

    dataset_id: str
    project: str
    table_count: int
    tables: list[TableInfo]


# Describe table response
class DescribeTableResponse(TypedDict):
    """Describe table response."""

    table_id: str
    dataset_id: str
    project: str
    table_type: str
    schema: list[SchemaField]
    description: str | None
    created: str
    modified: str
    statistics: TableStatistics
    partitioning: PartitioningInfo | None
    clustering_fields: list[str] | None
    formatted_schema: str | None


# Comprehensive table info response
class TimeTravelInfo(TypedDict):
    """Time travel configuration."""

    max_time_travel_hours: int


class ClusteringInfo(TypedDict):
    """Clustering configuration."""

    fields: list[str]


class ComprehensiveTableInfo(TypedDict):
    """Comprehensive table information response."""

    table_id: str
    dataset_id: str
    project: str
    full_table_id: str
    table_type: str
    created: str
    modified: str
    expires: str | None
    description: str | None
    labels: dict[str, str]
    location: str
    self_link: str
    etag: str
    friendly_name: str | None
    statistics: TableStatistics
    time_travel: TimeTravelInfo | None
    partitioning: dict[str, Any] | None
    clustering: ClusteringInfo | None
    encryption_configuration: dict[str, str] | None
    require_partition_filter: bool | None
    table_constraints: dict[str, Any] | None


# INFORMATION_SCHEMA response types
class InfoSchemaMetadata(TypedDict):
    """INFORMATION_SCHEMA query metadata."""

    total_bytes_processed: int
    estimated_cost_usd: float
    cache_hit: bool


class InfoSchemaResponse(TypedDict):
    """INFORMATION_SCHEMA query response."""

    query_type: str
    dataset_id: str
    project: str
    query: str
    schema: list[SchemaField]
    metadata: InfoSchemaMetadata
    info: str


# Performance analysis types
class OptimizationSuggestion(TypedDict):
    """Query optimization suggestion."""

    type: str
    severity: str
    message: str
    recommendation: str


class QueryAnalysis(TypedDict):
    """Query analysis details."""

    bytes_processed: int
    bytes_billed: int
    gigabytes_processed: float
    estimated_cost_usd: float
    referenced_tables: list[FullTableReference]
    table_count: int


class EstimatedExecution(TypedDict):
    """Estimated execution details."""

    note: str
    complexity_indicator: str


class PerformanceAnalysisResponse(TypedDict):
    """Performance analysis response."""

    query_analysis: QueryAnalysis
    performance_score: int
    performance_rating: str
    optimization_suggestions: list[OptimizationSuggestion]
    suggestion_count: int
    estimated_execution: EstimatedExecution


# Union types for responses
SQLValidationResponse = ValidSQLResponse | InvalidSQLResponse
DryRunResponse = DryRunSuccessResponse | DryRunErrorResponse
