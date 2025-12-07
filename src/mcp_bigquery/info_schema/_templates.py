"""Shared INFORMATION_SCHEMA query templates."""

INFO_SCHEMA_TEMPLATES = {
    "tables": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            table_type,
            creation_time,
            ddl
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
        {where_clause}
        ORDER BY table_name
        {limit_clause}
    """,
    "columns": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            column_name,
            ordinal_position,
            is_nullable,
            data_type,
            is_partitioning_column,
            clustering_ordinal_position
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        {where_clause}
        ORDER BY table_name, ordinal_position
        {limit_clause}
    """,
    "table_storage": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            creation_time,
            total_rows,
            total_partitions,
            total_logical_bytes,
            active_logical_bytes,
            long_term_logical_bytes,
            total_physical_bytes,
            active_physical_bytes,
            long_term_physical_bytes,
            time_travel_physical_bytes
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLE_STORAGE`
        {where_clause}
        ORDER BY total_logical_bytes DESC
        {limit_clause}
    """,
    "partitions": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            partition_id,
            total_rows,
            total_logical_bytes,
            total_physical_bytes,
            last_modified_time
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.PARTITIONS`
        {where_clause}
        ORDER BY table_name, partition_id
        {limit_clause}
    """,
    "views": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            view_definition,
            use_standard_sql
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.VIEWS`
        {where_clause}
        ORDER BY table_name
        {limit_clause}
    """,
    "routines": """
        SELECT 
            routine_catalog,
            routine_schema,
            routine_name,
            routine_type,
            language,
            routine_definition,
            created,
            last_altered
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.ROUTINES`
        {where_clause}
        ORDER BY routine_name
        {limit_clause}
    """,
}
