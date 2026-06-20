"""Lightweight SQL analysis utilities using sqlparse."""

from __future__ import annotations

import re
from typing import Any, cast

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Parenthesis, TokenList
from sqlparse.tokens import Wildcard

KEYWORDS = {"AS", "ON", "WHERE", "AND", "OR", "LEFT", "RIGHT", "INNER", "FULL", "CROSS"}


class SQLAnalyzer:
    """SQL analyzer utilizing sqlparse AST traversal for reliable dependency and syntax analysis."""

    def __init__(self, sql: str) -> None:
        self.sql = sql
        self._tables_cache: list[dict[str, str | None]] | None = None
        self._columns_cache: list[str] | None = None

    def extract_dependencies(self) -> dict[str, Any]:
        """Extract table and column dependencies from the SQL query."""
        tables = self._extract_tables()
        columns = self._extract_columns()

        # Key of dependency_graph is the physical table full name
        dependency_graph = {t["full_name"]: columns for t in tables if t["full_name"] is not None}

        return {
            "tables": tables,
            "columns": columns,
            "dependency_graph": dependency_graph,
            "table_count": len(tables),
            "column_count": len(columns),
        }

    def validate_syntax_enhanced(self) -> dict[str, Any]:
        """Perform enhanced static validation check on common SQL issues."""
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

    def _extract_ctes(self, parsed: TokenList) -> set[str]:
        """Extract CTE (WITH clause) temporary table names."""
        ctes: set[str] = set()

        def walk(token: Any) -> None:
            if isinstance(token, TokenList):
                for t in token.tokens:
                    if isinstance(t, Identifier):
                        # Detect CTE: identifier AS ( parenthesis )
                        has_as = False
                        has_paren = False
                        for child in t.tokens:
                            if child.is_keyword and child.value.upper() == "AS":
                                has_as = True
                            if isinstance(child, Parenthesis):
                                has_paren = True
                        if has_as and has_paren:
                            real_name = cast(Any, t).get_real_name() or cast(Any, t).get_name()
                            if real_name:
                                ctes.add(real_name.strip("`'\""))
                    walk(t)

        walk(parsed)
        return ctes

    def _extract_tables(self) -> list[dict[str, str | None]]:
        """Extract all physical BigQuery table dependencies, excluding CTEs."""
        if self._tables_cache is not None:
            return self._tables_cache

        parsed_statements = sqlparse.parse(self.sql)
        if not parsed_statements:
            return []

        parsed = parsed_statements[0]
        cte_names = self._extract_ctes(parsed)

        tables: list[dict[str, str | None]] = []
        seen_tables: set[str] = set()

        def walk(token: Any, in_from_or_join: bool = False) -> None:
            if isinstance(token, TokenList):
                current_in_from_or_join = in_from_or_join
                for t in token.tokens:
                    # Detect start of table references
                    if t.is_keyword and t.value.upper() in {
                        "FROM",
                        "JOIN",
                        "INNER JOIN",
                        "LEFT JOIN",
                        "RIGHT JOIN",
                        "FULL JOIN",
                        "CROSS JOIN",
                    }:
                        current_in_from_or_join = True
                        continue

                    # Other keywords (except AS, ON, AND, OR) stop the table context
                    if t.is_keyword and t.value.upper() not in {"AS", "ON", "AND", "OR"}:
                        current_in_from_or_join = False

                    if current_in_from_or_join:
                        if isinstance(t, Identifier):
                            process_identifier(t)
                        elif isinstance(t, IdentifierList):
                            for identifier in cast(Any, t).get_identifiers():
                                if isinstance(identifier, Identifier):
                                    process_identifier(identifier)

                    walk(t, current_in_from_or_join)

        def process_identifier(identifier: Identifier) -> None:
            real_name = cast(Any, identifier).get_real_name()
            if not real_name:
                # Fallback to identifier value
                real_name = identifier.value.split()[0]

            real_name = real_name.strip("`'\"")

            # Check if this is a CTE table
            if real_name in cte_names:
                return

            # Parse fully-qualified name
            parts = real_name.split(".")
            proj: str | None = None
            ds: str | None = None
            tbl: str | None = None

            if len(parts) == 3:
                proj, ds, tbl = parts[0], parts[1], parts[2]
                full_name = f"{proj}.{ds}.{tbl}"
            elif len(parts) == 2:
                ds, tbl = parts[0], parts[1]
                full_name = f"{ds}.{tbl}"
            else:
                tbl = parts[0]
                full_name = parts[0]

            # Avoid extracting standard keyword values or numeric constants
            if tbl.upper() in KEYWORDS or tbl.isdigit():
                return

            if full_name not in seen_tables:
                seen_tables.add(full_name)
                tables.append(
                    {
                        "project": proj,
                        "dataset": ds,
                        "table": tbl,
                        "full_name": full_name,
                        "name": full_name,
                    }
                )

        walk(parsed)
        self._tables_cache = tables
        return tables

    def _extract_columns(self) -> list[str]:
        """Extract column names from SELECT clause and filter predicates, ignoring aliases."""
        if self._columns_cache is not None:
            return self._columns_cache

        parsed_statements = sqlparse.parse(self.sql)
        if not parsed_statements:
            return []

        parsed = parsed_statements[0]
        cte_names = self._extract_ctes(parsed)
        physical_tables = self._extract_tables()

        # Build set of table/alias/CTE names to exclude them from extracted columns
        excluded_names = {t["table"] for t in physical_tables if t["table"] is not None}
        excluded_names.update(cte_names)

        # Standard SQL keywords and typical function names to ignore as column names
        excluded_keywords = {
            "AS",
            "DISTINCT",
            "CASE",
            "WHEN",
            "THEN",
            "ELSE",
            "END",
            "NULL",
            "TRUE",
            "FALSE",
            "AND",
            "OR",
            "NOT",
            "IN",
            "IS",
            "LIKE",
            "BETWEEN",
            "EXISTS",
            "CAST",
            "COALESCE",
            "SUM",
            "COUNT",
            "AVG",
            "MIN",
            "MAX",
            "GROUP",
            "BY",
            "ORDER",
            "LIMIT",
            "HAVING",
            "SELECT",
            "FROM",
            "JOIN",
            "WHERE",
            "ON",
            "USING",
            "UNION",
            "ALL",
            "ARRAY",
            "STRUCT",
            "DATE",
            "TIMESTAMP",
            "DATETIME",
            "TIME",
            "STRING",
            "INT64",
            "FLOAT64",
            "BOOL",
            "BYTES",
            "DESC",
            "ASC",
            "OVER",
            "PARTITION",
            "ROWS",
            "UNBOUNDED",
            "PRECEDING",
            "FOLLOWING",
        }

        columns: set[str] = set()

        def walk(token: Any) -> None:
            if isinstance(token, Identifier):
                # Ignore the alias part (AS alias_name) of the identifier
                tokens_to_scan = []
                for t in token.tokens:
                    if t.is_keyword and t.value.upper() == "AS":
                        break
                    tokens_to_scan.append(t)

                for t in tokens_to_scan:
                    if isinstance(t, Identifier):
                        walk(t)
                    elif t.ttype in sqlparse.tokens.Name:
                        process_name_token(t.value)
                    else:
                        walk(t)
                return

            if isinstance(token, TokenList):
                for t in token.tokens:
                    # Skip wildcards (SELECT * or table.*)
                    if t.ttype is Wildcard or (t.value and t.value == "*"):
                        continue
                    walk(t)
            elif token.ttype in sqlparse.tokens.Name:
                process_name_token(token.value)

        def process_name_token(val: str) -> None:
            clean_val = val.strip("`'\"")

            # Handle dotted notation (e.g. table.column or struct.field)
            if "." in clean_val:
                parts = clean_val.split(".")
                if parts[0] in excluded_names:
                    col_name = parts[-1]
                else:
                    col_name = parts[0]
            else:
                col_name = clean_val

            if (
                col_name.upper() not in excluded_keywords
                and col_name not in excluded_names
                and not col_name.isdigit()
                and not col_name.startswith((".", " "))
                and col_name != ""
            ):
                columns.add(col_name)

        walk(parsed)
        sorted_cols = sorted(columns)
        self._columns_cache = sorted_cols
        return sorted_cols

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
        suggestions: list[str] = []
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
