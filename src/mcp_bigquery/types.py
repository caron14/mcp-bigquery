"""Type definitions for MCP BigQuery server."""

from typing import Any, List, Optional, TypedDict, Union


# Base error types
class ErrorLocation(TypedDict):
    """Error location information."""

    line: int
    column: int


class ErrorInfo(TypedDict):
    """Error information structure."""

    code: str
    message: str
    location: Optional[ErrorLocation]
    details: Optional[List[Any]]


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

    project: Optional[str]
    dataset: str
    table: str
    full_name: Optional[str]


class FullTableReference(TypedDict):
    """Complete BigQuery table reference."""

    project: str
    dataset: str
    table: str
    full_id: Optional[str]


# Schema field types
class SchemaField(TypedDict):
    """BigQuery schema field."""

    name: str
    type: str
    mode: str
    description: Optional[str]
    fields: Optional[List["SchemaField"]]  # For nested fields


# Dry-run response types
class DryRunSuccessResponse(TypedDict):
    """Successful dry-run response."""

    totalBytesProcessed: int
    usdEstimate: float
    referencedTables: List[FullTableReference]
    schemaPreview: List[SchemaField]


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
    join_types: List[str]
    functions_used: List[str]


# Dependency extraction types
class DependencyResponse(TypedDict):
    """Dependency extraction response."""

    tables: List[TableReference]
    columns: List[str]
    dependency_graph: dict[str, List[str]]
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
    issues: List[ValidationIssue]
    suggestions: List[str]
    bigquery_specific: BigQuerySpecificFeatures


# Dataset types
class DatasetInfo(TypedDict):
    """Dataset information."""

    dataset_id: str
    project: str
    location: str
    created: str
    modified: str
    description: Optional[str]
    labels: dict[str, str]
    default_table_expiration_ms: Optional[int]
    default_partition_expiration_ms: Optional[int]


class DatasetListResponse(TypedDict):
    """Dataset list response."""

    project: str
    dataset_count: int
    datasets: List[DatasetInfo]


# Table partitioning and clustering types
class PartitioningInfo(TypedDict):
    """Table partitioning information."""

    type: str
    field: Optional[str]
    expiration_ms: Optional[int]
    require_partition_filter: Optional[bool]


class TimePartitioning(TypedDict):
    """Time-based partitioning details."""

    type: str
    field: Optional[str]
    require_partition_filter: bool


# Table information types
class TableStatistics(TypedDict):
    """Table statistics."""

    num_bytes: int
    num_rows: int
    num_long_term_bytes: Optional[int]
    creation_time: Optional[str]
    num_active_logical_bytes: Optional[int]
    num_long_term_logical_bytes: Optional[int]


class TableInfo(TypedDict):
    """Table information."""

    table_id: str
    dataset_id: str
    project: str
    table_type: str
    created: str
    modified: str
    description: Optional[str]
    labels: dict[str, str]
    num_bytes: int
    num_rows: int
    location: str
    partitioning: Optional[PartitioningInfo]
    clustering_fields: Optional[List[str]]


class TableListResponse(TypedDict):
    """Table list response."""

    dataset_id: str
    project: str
    table_count: int
    tables: List[TableInfo]


# Describe table response
class DescribeTableResponse(TypedDict):
    """Describe table response."""

    table_id: str
    dataset_id: str
    project: str
    table_type: str
    schema: List[SchemaField]
    description: Optional[str]
    created: str
    modified: str
    statistics: TableStatistics
    partitioning: Optional[PartitioningInfo]
    clustering_fields: Optional[List[str]]
    formatted_schema: Optional[str]


# Comprehensive table info response
class TimeTravelInfo(TypedDict):
    """Time travel configuration."""

    max_time_travel_hours: int


class ClusteringInfo(TypedDict):
    """Clustering configuration."""

    fields: List[str]


class ComprehensiveTableInfo(TypedDict):
    """Comprehensive table information response."""

    table_id: str
    dataset_id: str
    project: str
    full_table_id: str
    table_type: str
    created: str
    modified: str
    expires: Optional[str]
    description: Optional[str]
    labels: dict[str, str]
    location: str
    self_link: str
    etag: str
    friendly_name: Optional[str]
    statistics: TableStatistics
    time_travel: Optional[TimeTravelInfo]
    partitioning: Optional[dict[str, Any]]
    clustering: Optional[ClusteringInfo]
    encryption_configuration: Optional[dict[str, str]]
    require_partition_filter: Optional[bool]
    table_constraints: Optional[dict[str, Any]]


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
    schema: List[SchemaField]
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
    referenced_tables: List[FullTableReference]
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
    optimization_suggestions: List[OptimizationSuggestion]
    suggestion_count: int
    estimated_execution: EstimatedExecution


# Union types for responses
SQLValidationResponse = Union[ValidSQLResponse, InvalidSQLResponse]
DryRunResponse = Union[DryRunSuccessResponse, DryRunErrorResponse]
