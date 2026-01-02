"""Lightweight SQL analysis utilities."""

from __future__ import annotations

import re
from typing import Any

KEYWORDS = {"AS", "ON", "WHERE", "AND", "OR", "LEFT", "RIGHT", "INNER", "FULL", "CROSS"}


class SQLAnalyzer:
    """Minimal SQL analyzer for dependencies and heuristic checks."""

    def __init__(self, sql: str) -> None:
        self.sql = sql
        self._tables_cache: list[dict[str, str]] | None = None
        self._columns_cache: list[str] | None = None

    def extract_dependencies(self) -> dict[str, Any]:
        tables = self._extract_tables()
        columns = self._extract_columns()
        return {
            "tables": tables,
            "columns": columns,
            "dependency_graph": {table["full_name"]: columns for table in tables},
            "table_count": len(tables),
            "column_count": len(columns),
        }

    def validate_syntax_enhanced(self) -> dict[str, Any]:
        issues = self._check_common_syntax_issues() + self._check_bigquery_specific_syntax()
        suggestions = self._generate_suggestions(issues)
        has_errors = any(issue.get("severity") == "error" for issue in issues)

        return {
            "is_valid": not has_errors,
            "issues": issues,
            "suggestions": suggestions,
            "bigquery_specific": {
                "uses_legacy_sql": "#legacySQL" in self.sql,
                "has_array_syntax": bool(re.search(r"\bARRAY\s*[\[\<]", self.sql, re.IGNORECASE)),
                "has_struct_syntax": bool(re.search(r"\bSTRUCT\s*[\(\<]", self.sql, re.IGNORECASE)),
            },
        }

    def _extract_tables(self) -> list[dict[str, str]]:
        if self._tables_cache is not None:
            return self._tables_cache

        patterns = [
            (r"FROM\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`", 3),
            (r"FROM\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`", 2),
            (r"FROM\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)", 3),
            (r"FROM\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)", 2),
            (r"JOIN\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`", 3),
            (r"JOIN\s+`([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)`", 2),
            (r"JOIN\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)", 3),
            (r"JOIN\s+([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?:\s|$)", 2),
            (r"FROM\s+([a-zA-Z0-9_]+)(?:\s+[a-zA-Z0-9_]+)?(?:\s|$|,)", 1),
            (r"JOIN\s+([a-zA-Z0-9_]+)(?:\s+[a-zA-Z0-9_]+)?(?:\s+ON|\s|$)", 1),
        ]

        tables: list[dict[str, str]] = []
        for pattern, group_count in patterns:
            for match in re.finditer(pattern, self.sql, re.IGNORECASE):
                groups = match.groups()
                if group_count == 3:
                    tables.append(
                        {
                            "project": groups[0],
                            "dataset": groups[1],
                            "table": groups[2],
                            "full_name": f"{groups[0]}.{groups[1]}.{groups[2]}",
                            "name": f"{groups[0]}.{groups[1]}.{groups[2]}",
                        }
                    )
                elif group_count == 2:
                    tables.append(
                        {
                            "project": None,
                            "dataset": groups[0],
                            "table": groups[1],
                            "full_name": f"{groups[0]}.{groups[1]}",
                            "name": f"{groups[0]}.{groups[1]}",
                        }
                    )
                else:
                    table_name = groups[0]
                    if table_name.upper() not in KEYWORDS and not any(
                        t.get("table") == table_name for t in tables
                    ):
                        tables.append(
                            {
                                "project": None,
                                "dataset": None,
                                "table": table_name,
                                "full_name": table_name,
                                "name": table_name,
                            }
                        )

        unique_tables: list[dict[str, str]] = []
        seen = set()
        for table in tables:
            if table["full_name"] not in seen:
                seen.add(table["full_name"])
                unique_tables.append(table)

        self._tables_cache = unique_tables
        return unique_tables

    def _extract_columns(self) -> list[str]:
        if self._columns_cache is not None:
            return self._columns_cache

        columns = set()
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", self.sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            for match in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", select_match.group(1)):
                col = match.group(1)
                if col.upper() not in {"AS", "DISTINCT", "CASE", "WHEN", "THEN", "ELSE", "END"}:
                    columns.add(col)

        where_match = re.search(
            r"WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|\s*$)",
            self.sql,
            re.IGNORECASE | re.DOTALL,
        )
        if where_match:
            for match in re.finditer(
                r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b\s*(?:[=<>!]|IS|IN|LIKE)",
                where_match.group(1),
                re.IGNORECASE,
            ):
                columns.add(match.group(1))

        self._columns_cache = sorted(columns)
        return self._columns_cache

    def _check_common_syntax_issues(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if re.search(r"SELECT\s+\*", self.sql, re.IGNORECASE):
            issues.append(
                {
                    "type": "performance",
                    "message": "SELECT * may impact performance - consider specifying columns",
                    "severity": "warning",
                }
            )
        if re.search(r"^(DELETE|UPDATE)\s+", self.sql, re.IGNORECASE) and not re.search(
            r"\sWHERE\s+", self.sql, re.IGNORECASE
        ):
            issues.append(
                {
                    "type": "safety",
                    "message": "DELETE/UPDATE without WHERE clause affects all rows",
                    "severity": "error",
                }
            )
        if re.search(r"\sLIMIT\s+\d+", self.sql, re.IGNORECASE) and not re.search(
            r"\sORDER\s+BY\s+", self.sql, re.IGNORECASE
        ):
            issues.append(
                {
                    "type": "consistency",
                    "message": "LIMIT without ORDER BY may return inconsistent results",
                    "severity": "warning",
                }
            )
        return issues

    def _check_bigquery_specific_syntax(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        if re.search(r"FROM\s+[a-zA-Z]", self.sql) and not re.search(r"FROM\s+`", self.sql):
            issues.append(
                {
                    "type": "style",
                    "message": "Consider using backticks for table references in BigQuery",
                    "severity": "info",
                }
            )
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
        suggestions = []
        for issue in issues:
            issue_type = issue["type"]
            if issue_type == "performance" and "SELECT *" in issue["message"]:
                suggestions.append("Specify exact columns needed instead of using SELECT *")
            elif issue_type == "safety":
                suggestions.append("Add a WHERE clause to limit the scope of the operation")
            elif issue_type == "consistency":
                suggestions.append("Add ORDER BY clause before LIMIT for consistent results")
            elif issue_type == "style":
                suggestions.append("Use backticks (`) around table and column names")
            elif issue_type == "compatibility":
                suggestions.append("Migrate to Standard SQL for better support")
        return suggestions
