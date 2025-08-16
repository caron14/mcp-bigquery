# Claude Code Configuration

This guide provides comprehensive setup instructions for using MCP BigQuery with Claude Code, Anthropic's official desktop application.

## Overview

Claude Code integrates with MCP servers through a JSON configuration file that specifies server commands, arguments, and environment variables. MCP BigQuery communicates via standard input/output (stdio) for secure, efficient operation.

## Prerequisites

Before configuring Claude Code, ensure you have:

1. **Claude Code installed** - Download from [claude.ai/code](https://claude.ai/code)
2. **Python 3.10+** - Check with `python --version`
3. **MCP BigQuery installed** - See [installation guide](../get-started/installation.md)
4. **Google Cloud authentication** - See [authentication guide](../get-started/authentication.md)

## Configuration File Location

Claude Code reads MCP server configurations from platform-specific locations:

=== "macOS"
    ```
    ~/Library/Application Support/Claude/claude_desktop_config.json
    ```

=== "Windows"
    ```
    %APPDATA%\Claude\claude_desktop_config.json
    ```

=== "Linux"
    ```
    ~/.config/claude/claude_desktop_config.json
    ```

## Basic Configuration

### PyPI Installation (Recommended)

If you installed MCP BigQuery from PyPI using `pip install mcp-bigquery`:

```json title="claude_desktop_config.json"
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

### Source Installation

If you installed from source or are developing locally:

```json title="claude_desktop_config.json"
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "python",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

### Virtual Environment

If using a Python virtual environment:

```json title="claude_desktop_config.json"
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

## Environment Variables

Configure MCP BigQuery behavior through environment variables:

### Required Variables

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-gcp-project-id"
      }
    }
  }
}
```

### Optional Variables

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "BQ_LOCATION": "asia-northeast1",
        "SAFE_PRICE_PER_TIB": "6.5",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account-key.json"
      }
    }
  }
}
```

### Variable Reference

| Variable | Description | Example Values | Default |
|----------|-------------|----------------|---------|
| `BQ_PROJECT` | GCP project ID for BigQuery operations | `my-data-project` | From ADC |
| `BQ_LOCATION` | BigQuery processing location | `US`, `EU`, `asia-northeast1` | None |
| `SAFE_PRICE_PER_TIB` | Price per TiB for cost estimation (USD) | `5.0`, `6.25` | `5.0` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key file | `/Users/me/sa-key.json` | None |

## Authentication Setup

### Method 1: Application Default Credentials (Recommended)

Set up user authentication for development:

```bash
# Install Google Cloud SDK
# macOS: brew install google-cloud-sdk
# Windows: Download from cloud.google.com
# Linux: Follow cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set default project (optional)
gcloud config set project your-gcp-project-id
```

Configuration:
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-gcp-project-id"
      }
    }
  }
}
```

### Method 2: Service Account Key

For production or automated environments:

1. **Create service account** in Google Cloud Console
2. **Download key file** (JSON format)
3. **Configure path** in environment variables

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/yourname/path/to/service-account-key.json"
      }
    }
  }
}
```

!!! warning "Security Note"
    Store service account keys securely. Never commit them to version control or share them publicly.

## Platform-Specific Configurations

### macOS

#### Homebrew Python
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "/opt/homebrew/bin/python3",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

#### pyenv Python
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "/Users/yourname/.pyenv/versions/3.11.5/bin/python",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id"
      }
    }
  }
}
```

### Windows

#### System Python
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "C:\\Python311\\python.exe",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "GOOGLE_APPLICATION_CREDENTIALS": "C:\\Users\\YourName\\service-account-key.json"
      }
    }
  }
}
```

#### Anaconda Python
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "C:\\Users\\YourName\\anaconda3\\python.exe",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id"
      }
    }
  }
}
```

### Linux

#### System Python
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "/usr/bin/python3",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id",
        "PATH": "/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

#### Virtual Environment
```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "/home/yourname/venv/bin/python",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project-id"
      }
    }
  }
}
```

## Advanced Configuration

### Multiple Projects

Configure access to multiple GCP projects:

```json
{
  "mcpServers": {
    "mcp-bigquery-prod": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "production-project",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    },
    "mcp-bigquery-dev": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "development-project",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

### Custom Pricing

Configure region-specific pricing:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-project",
        "BQ_LOCATION": "asia-northeast1",
        "SAFE_PRICE_PER_TIB": "6.25"
      }
    }
  }
}
```

### Debug Mode

Enable verbose logging for troubleshooting:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-project",
        "LOG_LEVEL": "DEBUG",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Testing Configuration

### Verify Installation

1. **Check MCP BigQuery is installed**:
   ```bash
   # Test the command
   mcp-bigquery --version
   
   # Or test as module
   python -m mcp_bigquery --version
   ```

2. **Validate configuration file**:
   ```bash
   # Check JSON syntax
   python -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Test authentication**:
   ```bash
   # Verify gcloud auth
   gcloud auth list
   
   # Test BigQuery access
   gcloud alpha bigquery queries list --limit=1
   ```

### Claude Code Integration

1. **Restart Claude Code** after configuration changes
2. **Check server status** in Claude Code:
   - Look for MCP server indicator
   - Check for connection errors
3. **Test tools**:
   - Try validating a simple SQL query
   - Check for proper error messages

### Test Queries

Validate your setup with these example queries:

#### Basic Validation
```
Please validate this SQL query:
SELECT 1 as test_column
```

#### Cost Estimation
```
Please run a dry-run analysis of this query:
SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 10
```

#### Parameterized Query
```
Please validate this parameterized query:
SELECT * FROM users WHERE created_date = @start_date AND status = @user_status

With parameters:
- start_date: "2024-01-01"
- user_status: "active"
```

## Troubleshooting

### Common Issues

#### Server Not Found
```
Error: mcp-bigquery command not found
```

**Solutions**:
- Verify installation: `pip list | grep mcp-bigquery`
- Check PATH in environment variables
- Use full Python path instead of `mcp-bigquery`

#### Permission Denied
```
Error: Permission denied to project
```

**Solutions**:
- Check `BQ_PROJECT` value matches your GCP project
- Verify BigQuery API is enabled
- Grant `roles/bigquery.jobUser` permission

#### Authentication Failed
```
Error: Could not automatically determine credentials
```

**Solutions**:
- Run `gcloud auth application-default login`
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Verify service account key file exists and is readable

#### Invalid JSON Configuration
```
Error: Invalid JSON in configuration file
```

**Solutions**:
- Validate JSON syntax: `python -m json.tool config.json`
- Check for trailing commas
- Ensure proper escaping of backslashes in paths

### Debug Steps

1. **Check Claude Code logs**:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.local/share/Claude/logs/`

2. **Test MCP server manually**:
   ```bash
   # Run server directly
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}' | mcp-bigquery
   ```

3. **Verify environment**:
   ```bash
   # Check Python version
   python --version
   
   # Check pip packages
   pip list | grep -E "(mcp|bigquery|google)"
   
   # Test Google Cloud authentication
   python -c "from google.cloud import bigquery; print('Success')"
   ```

### Getting Help

If you continue experiencing issues:

1. **Check configuration** against examples above
2. **Review error messages** carefully
3. **Search existing issues** on [GitHub](https://github.com/caron14/mcp-bigquery/issues)
4. **Create new issue** with:
   - Operating system and version
   - Python version
   - Configuration file (redacted)
   - Complete error messages
   - Steps to reproduce

## Best Practices

### Security
- Use Application Default Credentials for development
- Store service account keys securely in production
- Regularly rotate service account keys
- Grant minimal required permissions

### Performance
- Set appropriate `BQ_LOCATION` for your data
- Monitor query costs with realistic `SAFE_PRICE_PER_TIB`
- Use parameterized queries for better validation

### Maintenance
- Keep MCP BigQuery updated: `pip install --upgrade mcp-bigquery`
- Monitor Google Cloud quotas and billing
- Review and update permissions periodically

## Next Steps

- [Explore examples](../examples/index.md) for real-world usage
- [Learn about parameters](../guides/parameters.md) for advanced queries
- [Understand cost estimation](../guides/cost-estimation.md) for optimization
- [Configure other MCP clients](mcp-clients.md) for different environments