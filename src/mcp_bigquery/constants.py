"""Constants for MCP BigQuery server."""

from enum import Enum

# BigQuery constants
BYTES_PER_TIB = 1024 * 1024 * 1024 * 1024  # 1 TiB in bytes
BYTES_PER_GIB = 1024 * 1024 * 1024  # 1 GiB in bytes
DEFAULT_PRICE_PER_TIB = 5.0  # USD per TiB
MIN_BILLING_BYTES = 10 * 1024 * 1024  # 10 MB minimum billing

# Query complexity scoring weights
COMPLEXITY_WEIGHTS = {
    "base": 10,
    "join": 5,
    "subquery": 10,
    "cte": 8,
    "aggregation": 3,
    "window_function": 7,
    "union": 5,
    "distinct": 2,
    "function": 1,
}

# Maximum complexity score
MAX_COMPLEXITY_SCORE = 100

# Performance score thresholds
PERFORMANCE_THRESHOLDS = {
    "EXCELLENT": 90,
    "GOOD": 70,
    "FAIR": 50,
    "POOR": 30,
}

# SQL Keywords for detection
SQL_KEYWORDS = {
    "DDL": ["CREATE", "ALTER", "DROP", "TRUNCATE"],
    "DML": ["INSERT", "UPDATE", "DELETE", "MERGE"],
    "DQL": ["SELECT"],
    "DCL": ["GRANT", "REVOKE"],
    "TCL": ["COMMIT", "ROLLBACK", "SAVEPOINT"],
}

# BigQuery-specific functions
BIGQUERY_FUNCTIONS = {
    "ARRAY": ["ARRAY_AGG", "ARRAY_CONCAT", "ARRAY_LENGTH", "ARRAY_TO_STRING"],
    "STRUCT": ["STRUCT", "AS STRUCT"],
    "GEOGRAPHY": ["ST_GEOGPOINT", "ST_DISTANCE", "ST_AREA"],
    "ML": ["ML.PREDICT", "ML.EVALUATE", "ML.TRAINING_INFO"],
    "DATETIME": ["DATETIME", "DATETIME_ADD", "DATETIME_SUB", "DATETIME_DIFF"],
    "TIMESTAMP": ["TIMESTAMP", "TIMESTAMP_ADD", "TIMESTAMP_SUB", "TIMESTAMP_DIFF"],
}

# Aggregation functions
AGGREGATION_FUNCTIONS = [
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "STDDEV",
    "VARIANCE",
    "ARRAY_AGG",
    "STRING_AGG",
    "APPROX_COUNT_DISTINCT",
    "APPROX_QUANTILES",
    "ANY_VALUE",
    "COUNTIF",
    "LOGICAL_AND",
    "LOGICAL_OR",
]

# Window functions
WINDOW_FUNCTIONS = [
    "ROW_NUMBER",
    "RANK",
    "DENSE_RANK",
    "PERCENT_RANK",
    "CUME_DIST",
    "NTILE",
    "LAG",
    "LEAD",
    "FIRST_VALUE",
    "LAST_VALUE",
    "NTH_VALUE",
]

# Join types
JOIN_TYPES = ["INNER", "LEFT", "RIGHT", "FULL", "CROSS"]

# Legacy SQL patterns
LEGACY_SQL_PATTERNS = [
    r"\[[\w-]+:[\w-]+\.[\w-]+\]",  # [project:dataset.table]
    r"TABLE_DATE_RANGE",
    r"TABLE_QUERY",
    r"FLATTEN",
    r"WITHIN\s+RECORD",
    r"WITHIN\s+GROUP",
]

# BigQuery data types
BIGQUERY_DATA_TYPES = [
    "INT64",
    "FLOAT64",
    "NUMERIC",
    "BIGNUMERIC",
    "BOOL",
    "STRING",
    "BYTES",
    "DATE",
    "TIME",
    "DATETIME",
    "TIMESTAMP",
    "GEOGRAPHY",
    "JSON",
    "ARRAY",
    "STRUCT",
]


# Table type enums
class TableType(Enum):
    """BigQuery table types."""

    TABLE = "TABLE"
    VIEW = "VIEW"
    EXTERNAL = "EXTERNAL"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"
    SNAPSHOT = "SNAPSHOT"


# Field modes
class FieldMode(Enum):
    """BigQuery field modes."""

    NULLABLE = "NULLABLE"
    REQUIRED = "REQUIRED"
    REPEATED = "REPEATED"


# Partitioning types
class PartitioningType(Enum):
    """BigQuery partitioning types."""

    DAY = "DAY"
    HOUR = "HOUR"
    MONTH = "MONTH"
    YEAR = "YEAR"
    INTEGER_RANGE = "INTEGER_RANGE"


# Error codes
class ErrorCode(Enum):
    """Error codes for MCP BigQuery server."""

    INVALID_SQL = "INVALID_SQL"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    CONFIG_ERROR = "CONFIG_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    TABLE_NOT_FOUND = "TABLE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# Severity levels
class Severity(Enum):
    """Severity levels for issues and suggestions."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Issue types
class IssueType(Enum):
    """Types of issues in SQL validation."""

    SYNTAX = "syntax"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BEST_PRACTICE = "best_practice"
    COMPATIBILITY = "compatibility"
    CONSISTENCY = "consistency"


# Optimization types
class OptimizationType(Enum):
    """Types of query optimizations."""

    SELECT_STAR = "SELECT_STAR"
    MISSING_WHERE = "MISSING_WHERE"
    MISSING_LIMIT = "MISSING_LIMIT"
    HIGH_DATA_SCAN = "HIGH_DATA_SCAN"
    MISSING_PARTITION_FILTER = "MISSING_PARTITION_FILTER"
    CROSS_JOIN = "CROSS_JOIN"
    CARTESIAN_PRODUCT = "CARTESIAN_PRODUCT"
    SUBOPTIMAL_JOIN = "SUBOPTIMAL_JOIN"
    MISSING_INDEX = "MISSING_INDEX"
    REDUNDANT_OPERATION = "REDUNDANT_OPERATION"


# INFORMATION_SCHEMA views
INFO_SCHEMA_VIEWS = {
    "SCHEMATA": "List all datasets",
    "TABLES": "List all tables in a dataset",
    "COLUMNS": "List all columns in tables",
    "TABLE_STORAGE": "Storage statistics for tables",
    "PARTITIONS": "Partition information",
    "VIEWS": "View definitions",
    "ROUTINES": "Stored procedures and functions",
    "ROUTINE_OPTIONS": "Routine options",
    "PARAMETERS": "Routine parameters",
    "TABLE_OPTIONS": "Table options",
    "COLUMN_FIELD_PATHS": "Nested field paths",
    "KEY_COLUMN_USAGE": "Key constraints",
    "TABLE_CONSTRAINTS": "Table constraints",
}

# Default limits
DEFAULT_LIMITS = {
    "max_results": 1000,
    "max_query_length": 100000,
    "max_parameter_count": 100,
    "max_schema_depth": 15,
    "info_schema_limit": 100,
}

# Timeout values (in seconds)
TIMEOUTS = {
    "query": 30,
    "connection": 10,
    "cache_ttl": 300,
}

# Cache keys prefixes
CACHE_KEY_PREFIX = {
    "client": "bq_client",
    "schema": "bq_schema",
    "dataset": "bq_dataset",
    "table": "bq_table",
    "query": "bq_query",
}

# Regular expressions
REGEX_PATTERNS = {
    "error_location": r"\[(\d+):(\d+)\]",
    "table_reference": r"(?:(`[^`]+`)|(\b[\w-]+))\.(?:(`[^`]+`)|(\b[\w-]+))\.(?:(`[^`]+`)|(\b[\w-]+))",
    "dataset_table": r"(?:(`[^`]+`)|(\b[\w-]+))\.(?:(`[^`]+`)|(\b[\w-]+))",
    "parameter": r"@(\w+)",
    "backtick_identifier": r"`[^`]+`",
}
