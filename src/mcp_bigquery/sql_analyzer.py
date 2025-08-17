"""SQL analysis utilities for MCP BigQuery server."""

import re
from typing import Any

import sqlparse


class SQLAnalyzer:
    """Analyzer for BigQuery SQL queries providing static analysis capabilities."""

    def __init__(self, sql: str):
        """Initialize the SQL analyzer with a query string.

        Args:
            sql: The SQL query string to analyze
        """
        self.sql = sql
        self.parsed = sqlparse.parse(sql)[0] if sql else None
        self._tables_cache: list[dict[str, str]] | None = None
        self._columns_cache: list[str] | None = None

    def analyze_structure(self) -> dict[str, Any]:
        """Analyze the SQL query structure.

        Returns:
            Dictionary containing structure analysis including:
            - query_type: Type of SQL query (SELECT, INSERT, etc.)
            - has_joins: Whether query contains JOINs
            - has_subqueries: Whether query contains subqueries
            - has_cte: Whether query uses CTEs (WITH clause)
            - has_aggregations: Whether query uses GROUP BY/aggregation functions
            - has_window_functions: Whether query uses window functions
            - complexity_score: Numerical complexity score
        """
        if not self.parsed:
            return {"error": "Unable to parse SQL query"}

        result = {
            "query_type": self._get_query_type(),
            "has_joins": self._has_joins(),
            "has_subqueries": self._has_subqueries(),
            "has_cte": self._has_cte(),
            "has_aggregations": self._has_aggregations(),
            "has_window_functions": self._has_window_functions(),
            "has_union": self._has_union(),
            "table_count": len(self._extract_tables()),
            "complexity_score": self._calculate_complexity_score(),
        }

        # Add JOIN details if present
        if result["has_joins"]:
            result["join_types"] = self._get_join_types()

        # Add function usage analysis
        functions_used = self._get_functions_used()
        if functions_used:
            result["functions_used"] = functions_used

        return result

    def extract_dependencies(self) -> dict[str, Any]:
        """Extract table and column dependencies from the SQL query.

        Returns:
            Dictionary containing:
            - tables: List of referenced tables with project/dataset/table info
            - columns: List of referenced columns
            - dependency_graph: Mapping of tables to their referenced columns
        """
        tables = self._extract_tables()
        columns = self._extract_columns()

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tables, columns)

        return {
            "tables": tables,
            "columns": columns,
            "dependency_graph": dependency_graph,
            "table_count": len(tables),
            "column_count": len(columns),
        }

    def validate_syntax_enhanced(self) -> dict[str, Any]:
        """Perform enhanced syntax validation with detailed error reporting.

        Returns:
            Dictionary containing:
            - is_valid: Whether the SQL syntax appears valid
            - issues: List of potential syntax issues
            - suggestions: List of improvement suggestions
            - bigquery_specific: BigQuery-specific validation results
        """
        issues = []
        suggestions = []

        # Check for common syntax issues
        issues.extend(self._check_common_syntax_issues())

        # Check BigQuery-specific syntax
        bq_issues = self._check_bigquery_specific_syntax()
        issues.extend(bq_issues)

        # Generate suggestions based on issues
        suggestions = self._generate_suggestions(issues)

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "bigquery_specific": {
                "uses_legacy_sql": self._uses_legacy_sql(),
                "has_array_syntax": self._has_array_syntax(),
                "has_struct_syntax": self._has_struct_syntax(),
            },
        }

    def _get_query_type(self) -> str:
        """Determine the type of SQL query."""
        if not self.parsed:
            return "UNKNOWN"

        first_token = self.parsed.token_first(skip_ws=True, skip_cm=True)
        if first_token:
            return str(first_token.value).upper()
        return "UNKNOWN"

    def _has_joins(self) -> bool:
        """Check if query contains JOIN operations."""
        sql_upper = self.sql.upper()
        join_patterns = [
            " JOIN ",
            " INNER JOIN ",
            " LEFT JOIN ",
            " RIGHT JOIN ",
            " FULL JOIN ",
            " CROSS JOIN ",
            " LEFT OUTER JOIN ",
            " RIGHT OUTER JOIN ",
            " FULL OUTER JOIN ",
        ]
        return any(pattern in sql_upper for pattern in join_patterns)

    def _has_subqueries(self) -> bool:
        """Check if query contains subqueries."""
        # Count parentheses that might indicate subqueries
        # Look for SELECT within parentheses
        pattern = r"\(\s*SELECT\s+"
        return bool(re.search(pattern, self.sql, re.IGNORECASE))

    def _has_cte(self) -> bool:
        """Check if query uses Common Table Expressions (WITH clause)."""
        pattern = r"^\s*WITH\s+"
        return bool(re.search(pattern, self.sql, re.IGNORECASE))

    def _has_aggregations(self) -> bool:
        """Check if query uses aggregation functions or GROUP BY."""
        sql_upper = self.sql.upper()

        # Check for GROUP BY
        if " GROUP BY " in sql_upper:
            return True

        # Check for common aggregation functions
        agg_functions = [
            "COUNT(",
            "SUM(",
            "AVG(",
            "MIN(",
            "MAX(",
            "ARRAY_AGG(",
            "STRING_AGG(",
            "STDDEV(",
            "VARIANCE(",
        ]
        return any(func in sql_upper for func in agg_functions)

    def _has_window_functions(self) -> bool:
        """Check if query uses window functions."""
        # Look for OVER clause which indicates window functions
        pattern = r"\bOVER\s*\("
        return bool(re.search(pattern, self.sql, re.IGNORECASE))

    def _has_union(self) -> bool:
        """Check if query uses UNION operations."""
        pattern = r"\bUNION\s+(ALL\s+)?"
        return bool(re.search(pattern, self.sql, re.IGNORECASE))

    def _get_join_types(self) -> list[str]:
        """Extract types of JOINs used in the query."""
        join_types = []
        sql_upper = self.sql.upper()

        # Check for specific JOIN patterns in order of specificity
        join_patterns = [
            ("LEFT OUTER JOIN", "LEFT OUTER"),
            ("RIGHT OUTER JOIN", "RIGHT OUTER"),
            ("FULL OUTER JOIN", "FULL OUTER"),
            ("INNER JOIN", "INNER"),
            ("LEFT JOIN", "LEFT"),
            ("RIGHT JOIN", "RIGHT"),
            ("FULL JOIN", "FULL"),
            ("CROSS JOIN", "CROSS"),
            (" JOIN ", "INNER"),  # Default JOIN is INNER JOIN
        ]

        for pattern, join_type in join_patterns:
            if pattern in sql_upper:
                join_types.append(join_type)

        return list(set(join_types))

    def _get_functions_used(self) -> list[str]:
        """Extract all functions used in the query."""
        functions = set()

        # Common BigQuery functions to look for
        function_pattern = r"\b([A-Z_]+)\s*\("
        matches = re.finditer(function_pattern, self.sql, re.IGNORECASE)

        for match in matches:
            func_name = match.group(1).upper()
            # Filter out SQL keywords that aren't functions
            if func_name not in ["SELECT", "FROM", "WHERE", "AND", "OR", "IN", "NOT", "AS", "ON"]:
                functions.add(func_name)

        return sorted(functions)

    def _extract_tables(self) -> list[dict[str, str]]:
        """Extract all referenced tables from the query."""
        if self._tables_cache is not None:
            return self._tables_cache

        tables = []

        # BigQuery table reference patterns
        # Format: [project.]dataset.table or `project.dataset.table`
        patterns = [
            r"FROM\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`",  # `project.dataset.table`
            r"FROM\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`",  # `dataset.table`
            r"FROM\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)",  # project.dataset.table
            r"FROM\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)",  # dataset.table
            r"JOIN\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`",  # `project.dataset.table` in JOIN
            r"JOIN\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`",  # `dataset.table` in JOIN
            r"JOIN\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)",  # project.dataset.table in JOIN
            r"JOIN\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)",  # dataset.table in JOIN
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, self.sql, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) == 3:
                    # project.dataset.table format
                    tables.append(
                        {
                            "project": groups[0],
                            "dataset": groups[1],
                            "table": groups[2],
                            "full_name": f"{groups[0]}.{groups[1]}.{groups[2]}",
                        }
                    )
                elif len(groups) == 2:
                    # dataset.table format
                    tables.append(
                        {
                            "project": None,
                            "dataset": groups[0],
                            "table": groups[1],
                            "full_name": f"{groups[0]}.{groups[1]}",
                        }
                    )

        # Remove duplicates
        seen = set()
        unique_tables = []
        for table in tables:
            if table["full_name"] not in seen:
                seen.add(table["full_name"])
                unique_tables.append(table)

        self._tables_cache = unique_tables
        return unique_tables

    def _extract_columns(self) -> list[str]:
        """Extract referenced column names from the query."""
        if self._columns_cache is not None:
            return self._columns_cache

        columns = set()

        # Extract columns from SELECT clause
        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        select_match = re.search(select_pattern, self.sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # Parse column names (simplified - doesn't handle all cases)
            column_pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b"
            for match in re.finditer(column_pattern, select_clause):
                col_name = match.group(1)
                # Filter out SQL keywords
                if col_name.upper() not in [
                    "AS",
                    "DISTINCT",
                    "CASE",
                    "WHEN",
                    "THEN",
                    "ELSE",
                    "END",
                ]:
                    columns.add(col_name)

        # Extract columns from WHERE clause
        where_pattern = r"WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|\s*$)"
        where_match = re.search(where_pattern, self.sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            column_pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*(?:[=<>!]|IS|IN|LIKE)"
            for match in re.finditer(column_pattern, where_clause, re.IGNORECASE):
                columns.add(match.group(1))

        self._columns_cache = sorted(columns)
        return self._columns_cache

    def _build_dependency_graph(
        self, tables: list[dict[str, str]], columns: list[str]
    ) -> dict[str, list[str]]:
        """Build a dependency graph mapping tables to their referenced columns."""
        # Simplified version - in production would need more sophisticated parsing
        graph = {}
        for table in tables:
            # Associate all found columns with each table (simplified)
            # In a real implementation, we'd parse which columns belong to which tables
            graph[table["full_name"]] = columns
        return graph

    def _calculate_complexity_score(self) -> int:
        """Calculate a complexity score for the SQL query."""
        score = 0

        # Base score by query length
        score += len(self.sql) // 100

        # Add points for various features
        if self._has_joins():
            score += 3 * len(self._get_join_types())
        if self._has_subqueries():
            score += 5
        if self._has_cte():
            score += 3
        if self._has_aggregations():
            score += 2
        if self._has_window_functions():
            score += 4
        if self._has_union():
            score += 3

        # Add points for number of tables
        score += len(self._extract_tables()) * 2

        # Add points for functions used
        score += len(self._get_functions_used())

        return min(score, 100)  # Cap at 100

    def _check_common_syntax_issues(self) -> list[dict[str, str]]:
        """Check for common SQL syntax issues."""
        issues = []

        # Check for SELECT *
        if re.search(r"SELECT\s+\*", self.sql, re.IGNORECASE):
            issues.append(
                {
                    "type": "performance",
                    "message": "SELECT * may impact performance - consider specifying columns",
                    "severity": "warning",
                }
            )

        # Check for missing WHERE clause in DELETE/UPDATE
        if re.search(r"^(DELETE|UPDATE)\s+", self.sql, re.IGNORECASE):
            if not re.search(r"\sWHERE\s+", self.sql, re.IGNORECASE):
                issues.append(
                    {
                        "type": "safety",
                        "message": "DELETE/UPDATE without WHERE clause affects all rows",
                        "severity": "error",
                    }
                )

        # Check for LIMIT without ORDER BY
        if re.search(r"\sLIMIT\s+\d+", self.sql, re.IGNORECASE):
            if not re.search(r"\sORDER\s+BY\s+", self.sql, re.IGNORECASE):
                issues.append(
                    {
                        "type": "consistency",
                        "message": "LIMIT without ORDER BY may return inconsistent results",
                        "severity": "warning",
                    }
                )

        return issues

    def _check_bigquery_specific_syntax(self) -> list[dict[str, str]]:
        """Check for BigQuery-specific syntax issues."""
        issues = []

        # Check for backticks in identifiers (recommended for BigQuery)
        if re.search(r"FROM\s+[a-zA-Z]", self.sql) and not re.search(r"FROM\s+`", self.sql):
            issues.append(
                {
                    "type": "style",
                    "message": "Consider using backticks for table references in BigQuery",
                    "severity": "info",
                }
            )

        # Check for #legacySQL or #standardSQL directives
        if "#legacySQL" in self.sql:
            issues.append(
                {
                    "type": "compatibility",
                    "message": "Legacy SQL is deprecated - consider using Standard SQL",
                    "severity": "warning",
                }
            )

        return issues

    def _generate_suggestions(self, issues: list[dict[str, str]]) -> list[str]:
        """Generate improvement suggestions based on identified issues."""
        suggestions = []

        for issue in issues:
            if issue["type"] == "performance" and "SELECT *" in issue["message"]:
                suggestions.append("Specify exact columns needed instead of using SELECT *")
            elif issue["type"] == "safety":
                suggestions.append("Add a WHERE clause to limit the scope of the operation")
            elif issue["type"] == "consistency":
                suggestions.append("Add ORDER BY clause before LIMIT for consistent results")
            elif issue["type"] == "style":
                suggestions.append(
                    "Use backticks (`) around table and column names for better compatibility"
                )
            elif issue["type"] == "compatibility":
                suggestions.append(
                    "Migrate to Standard SQL for better feature support and performance"
                )

        return suggestions

    def _uses_legacy_sql(self) -> bool:
        """Check if query uses Legacy SQL syntax."""
        return "#legacySQL" in self.sql or bool(re.search(r"\[.*:.*\..*\]", self.sql))

    def _has_array_syntax(self) -> bool:
        """Check if query uses ARRAY syntax."""
        return bool(re.search(r"\bARRAY\s*[\[\<]", self.sql, re.IGNORECASE))

    def _has_struct_syntax(self) -> bool:
        """Check if query uses STRUCT syntax."""
        return bool(re.search(r"\bSTRUCT\s*[\(\<]", self.sql, re.IGNORECASE))
