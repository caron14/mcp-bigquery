"""BigQuery client helper for MCP server."""

import os
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError


def get_bigquery_client() -> bigquery.Client:
    """
    Create and return a configured BigQuery client.
    
    Uses Application Default Credentials (ADC) by default.
    Respects environment variables:
    - BQ_PROJECT: GCP project ID
    - BQ_LOCATION: Default location for BigQuery operations
    
    Returns:
        bigquery.Client: Configured BigQuery client
        
    Raises:
        DefaultCredentialsError: If credentials cannot be found
    """
    project = os.environ.get("BQ_PROJECT")
    location = os.environ.get("BQ_LOCATION")
    
    try:
        # Create client with location if provided
        if location:
            client = bigquery.Client(project=project, location=location)
        else:
            client = bigquery.Client(project=project)
        return client
    except DefaultCredentialsError as e:
        raise DefaultCredentialsError(
            "No BigQuery credentials found. Please set up Application Default Credentials "
            "or provide a service account key. "
            "Run 'gcloud auth application-default login' for local development."
        ) from e