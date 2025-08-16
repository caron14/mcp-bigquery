# MCP Client Configuration

This guide covers configuration for various MCP (Model Context Protocol) clients beyond Claude Code, including custom implementations and integration platforms.

## Overview

MCP BigQuery is compatible with any MCP client that supports stdio-based server communication. The server follows the MCP specification and can be integrated into various environments and applications.

## MCP Specification Compliance

MCP BigQuery implements the following MCP capabilities:

- **Protocol Version**: MCP 1.0
- **Transport**: stdio (standard input/output)
- **Tools**: `bq_validate_sql`, `bq_dry_run_sql`
- **Error Handling**: Standard MCP error responses
- **Initialization**: Standard MCP initialization sequence

## Generic MCP Client Configuration

### Basic Configuration Schema

All MCP clients typically require these configuration elements:

```json
{
  "servers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "args": [],
      "env": {
        "BQ_PROJECT": "your-gcp-project",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      },
      "transport": "stdio"
    }
  }
}
```

### Environment Variables

Standard environment configuration for all clients:

| Variable | Type | Description | Required |
|----------|------|-------------|----------|
| `BQ_PROJECT` | string | GCP project ID | Yes |
| `BQ_LOCATION` | string | BigQuery location | No |
| `SAFE_PRICE_PER_TIB` | string | Cost per TiB (USD) | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | string | Service account key path | No |

## Custom MCP Client Implementation

### Python MCP Client

Example implementation using the official MCP Python SDK:

```python title="custom_mcp_client.py"
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_bigquery_client():
    # Configure server parameters
    server_params = StdioServerParameters(
        command="mcp-bigquery",
        args=[],
        env={
            "BQ_PROJECT": "your-gcp-project",
            "BQ_LOCATION": "US",
            "SAFE_PRICE_PER_TIB": "5.0"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools])
            
            # Validate SQL
            result = await session.call_tool(
                "bq_validate_sql",
                {"sql": "SELECT 1 as test"}
            )
            print("Validation result:", result.content[0].text)
            
            # Dry-run analysis
            result = await session.call_tool(
                "bq_dry_run_sql",
                {"sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"}
            )
            print("Dry-run result:", result.content[0].text)

if __name__ == "__main__":
    asyncio.run(run_bigquery_client())
```

### Node.js MCP Client

Example using the MCP TypeScript/JavaScript SDK:

```typescript title="custom_mcp_client.ts"
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

async function runBigQueryClient() {
  const transport = new StdioClientTransport({
    command: "mcp-bigquery",
    args: [],
    env: {
      BQ_PROJECT: "your-gcp-project",
      BQ_LOCATION: "US",
      SAFE_PRICE_PER_TIB: "5.0"
    }
  });

  const client = new Client(
    {
      name: "mcp-bigquery-client",
      version: "1.0.0",
    },
    {
      capabilities: {}
    }
  );

  await client.connect(transport);

  // List tools
  const tools = await client.listTools();
  console.log("Available tools:", tools.tools.map(t => t.name));

  // Validate SQL
  const validation = await client.callTool({
    name: "bq_validate_sql",
    arguments: {
      sql: "SELECT 1 as test"
    }
  });
  console.log("Validation:", validation.content[0].text);

  // Clean up
  await client.close();
}

runBigQueryClient().catch(console.error);
```

## Integration Platform Configurations

### Docker Compose

Deploy MCP BigQuery as a service:

```yaml title="docker-compose.yml"
version: '3.8'

services:
  mcp-bigquery:
    image: python:3.11-slim
    working_dir: /app
    volumes:
      - ./service-account-key.json:/app/service-account-key.json:ro
    environment:
      - BQ_PROJECT=your-gcp-project
      - BQ_LOCATION=US
      - SAFE_PRICE_PER_TIB=5.0
      - GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
    command: >
      sh -c "
        pip install mcp-bigquery &&
        mcp-bigquery
      "
    stdin_open: true
    tty: true

  mcp-client:
    image: node:18-alpine
    working_dir: /app
    volumes:
      - ./client:/app
    depends_on:
      - mcp-bigquery
    command: npm start
```

### Kubernetes Deployment

```yaml title="mcp-bigquery-deployment.yaml"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-bigquery
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mcp-bigquery
  template:
    metadata:
      labels:
        app: mcp-bigquery
    spec:
      serviceAccountName: mcp-bigquery-sa
      containers:
      - name: mcp-bigquery
        image: python:3.11-slim
        command: ["sh", "-c"]
        args:
          - |
            pip install mcp-bigquery
            mcp-bigquery
        env:
        - name: BQ_PROJECT
          value: "your-gcp-project"
        - name: BQ_LOCATION
          value: "US"
        - name: SAFE_PRICE_PER_TIB
          value: "5.0"
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        stdin: true
        tty: true
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-bigquery-sa
  annotations:
    iam.gke.io/gcp-service-account: mcp-bigquery@your-project.iam.gserviceaccount.com
```

### Cloud Run Configuration

```yaml title="cloud-run.yaml"
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mcp-bigquery
  annotations:
    run.googleapis.com/ingress: private
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/service-account: mcp-bigquery@your-project.iam.gserviceaccount.com
    spec:
      containers:
      - image: gcr.io/your-project/mcp-bigquery
        env:
        - name: BQ_PROJECT
          value: "your-gcp-project"
        - name: BQ_LOCATION
          value: "US"
        - name: SAFE_PRICE_PER_TIB
          value: "5.0"
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
        ports:
        - containerPort: 8080
```

## Framework-Specific Integrations

### FastAPI Integration

Wrap MCP BigQuery in a REST API:

```python title="fastapi_wrapper.py"
import asyncio
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

app = FastAPI(title="MCP BigQuery API")

class SQLValidationRequest(BaseModel):
    sql: str
    params: dict = {}

class DryRunRequest(BaseModel):
    sql: str
    params: dict = {}
    pricePerTiB: float = 5.0

async def get_mcp_session():
    server_params = StdioServerParameters(
        command="mcp-bigquery",
        args=[],
        env={
            "BQ_PROJECT": "your-gcp-project",
            "BQ_LOCATION": "US",
            "SAFE_PRICE_PER_TIB": "5.0"
        }
    )
    
    read, write = await stdio_client(server_params).__aenter__()
    session = await ClientSession(read, write).__aenter__()
    await session.initialize()
    return session

@app.post("/validate")
async def validate_sql(request: SQLValidationRequest):
    session = await get_mcp_session()
    try:
        result = await session.call_tool(
            "bq_validate_sql",
            {"sql": request.sql, "params": request.params}
        )
        return json.loads(result.content[0].text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await session.close()

@app.post("/dry-run")
async def dry_run_sql(request: DryRunRequest):
    session = await get_mcp_session()
    try:
        result = await session.call_tool(
            "bq_dry_run_sql",
            {
                "sql": request.sql,
                "params": request.params,
                "pricePerTiB": request.pricePerTiB
            }
        )
        return json.loads(result.content[0].text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Express.js Integration

Node.js REST API wrapper:

```javascript title="express_wrapper.js"
const express = require('express');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio');
const { Client } = require('@modelcontextprotocol/sdk/client');

const app = express();
app.use(express.json());

async function createMCPClient() {
  const transport = new StdioClientTransport({
    command: 'mcp-bigquery',
    args: [],
    env: {
      BQ_PROJECT: 'your-gcp-project',
      BQ_LOCATION: 'US',
      SAFE_PRICE_PER_TIB: '5.0'
    }
  });

  const client = new Client(
    { name: 'mcp-bigquery-api', version: '1.0.0' },
    { capabilities: {} }
  );

  await client.connect(transport);
  return client;
}

app.post('/validate', async (req, res) => {
  const client = await createMCPClient();
  try {
    const { sql, params = {} } = req.body;
    const result = await client.callTool({
      name: 'bq_validate_sql',
      arguments: { sql, params }
    });
    res.json(JSON.parse(result.content[0].text));
  } catch (error) {
    res.status(400).json({ error: error.message });
  } finally {
    await client.close();
  }
});

app.post('/dry-run', async (req, res) => {
  const client = await createMCPClient();
  try {
    const { sql, params = {}, pricePerTiB = 5.0 } = req.body;
    const result = await client.callTool({
      name: 'bq_dry_run_sql',
      arguments: { sql, params, pricePerTiB }
    });
    res.json(JSON.parse(result.content[0].text));
  } catch (error) {
    res.status(400).json({ error: error.message });
  } finally {
    await client.close();
  }
});

app.listen(3000, () => {
  console.log('MCP BigQuery API listening on port 3000');
});
```

## CI/CD Integration

### GitHub Actions

```yaml title=".github/workflows/sql-validation.yml"
name: SQL Validation

on:
  pull_request:
    paths:
      - 'sql/**/*.sql'

jobs:
  validate-sql:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install MCP BigQuery
      run: pip install mcp-bigquery
    
    - name: Set up authentication
      env:
        GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
      run: |
        echo "$GOOGLE_CREDENTIALS" > /tmp/credentials.json
        export GOOGLE_APPLICATION_CREDENTIALS="/tmp/credentials.json"
    
    - name: Validate SQL files
      env:
        BQ_PROJECT: ${{ secrets.BQ_PROJECT }}
        BQ_LOCATION: "US"
        GOOGLE_APPLICATION_CREDENTIALS: "/tmp/credentials.json"
      run: |
        python -c "
        import asyncio
        import glob
        import json
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        async def validate_files():
            server_params = StdioServerParameters(
                command='mcp-bigquery', args=[], env={
                    'BQ_PROJECT': '${{ secrets.BQ_PROJECT }}',
                    'BQ_LOCATION': 'US',
                    'GOOGLE_APPLICATION_CREDENTIALS': '/tmp/credentials.json'
                }
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    for sql_file in glob.glob('sql/**/*.sql', recursive=True):
                        with open(sql_file, 'r') as f:
                            sql_content = f.read()
                        
                        result = await session.call_tool(
                            'bq_validate_sql',
                            {'sql': sql_content}
                        )
                        
                        validation = json.loads(result.content[0].text)
                        if not validation.get('isValid', False):
                            print(f'❌ {sql_file}: {validation.get(\"error\", {}).get(\"message\", \"Unknown error\")}')
                            exit(1)
                        else:
                            print(f'✅ {sql_file}: Valid')
        
        asyncio.run(validate_files())
        "
```

### GitLab CI

```yaml title=".gitlab-ci.yml"
stages:
  - validate

sql-validation:
  stage: validate
  image: python:3.11
  before_script:
    - pip install mcp-bigquery
    - echo "$GOOGLE_CREDENTIALS" > /tmp/credentials.json
    - export GOOGLE_APPLICATION_CREDENTIALS="/tmp/credentials.json"
  script:
    - |
      python -c "
      import asyncio
      import glob
      import json
      import os
      from mcp import ClientSession, StdioServerParameters
      from mcp.client.stdio import stdio_client
      
      async def validate_sql_files():
          server_params = StdioServerParameters(
              command='mcp-bigquery',
              args=[],
              env={
                  'BQ_PROJECT': os.environ['BQ_PROJECT'],
                  'BQ_LOCATION': 'US',
                  'GOOGLE_APPLICATION_CREDENTIALS': '/tmp/credentials.json'
              }
          )
          
          async with stdio_client(server_params) as (read, write):
              async with ClientSession(read, write) as session:
                  await session.initialize()
                  
                  errors = []
                  for sql_file in glob.glob('**/*.sql', recursive=True):
                      with open(sql_file, 'r') as f:
                          sql_content = f.read()
                      
                      result = await session.call_tool(
                          'bq_validate_sql',
                          {'sql': sql_content}
                      )
                      
                      validation = json.loads(result.content[0].text)
                      if not validation.get('isValid', False):
                          error_msg = validation.get('error', {}).get('message', 'Unknown error')
                          errors.append(f'{sql_file}: {error_msg}')
                          print(f'❌ {sql_file}: {error_msg}')
                      else:
                          print(f'✅ {sql_file}: Valid')
                  
                  if errors:
                      print(f'\n{len(errors)} SQL validation errors found:')
                      for error in errors:
                          print(f'  - {error}')
                      exit(1)
                  else:
                      print(f'\n✅ All SQL files are valid!')
      
      asyncio.run(validate_sql_files())
      "
  variables:
    BQ_PROJECT: $BQ_PROJECT
  only:
    changes:
      - "**/*.sql"
```

## Testing MCP Integration

### Protocol Compliance Test

```python title="test_mcp_compliance.py"
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_compliance():
    """Test MCP BigQuery server compliance with MCP specification."""
    
    server_params = StdioServerParameters(
        command="mcp-bigquery",
        args=[],
        env={"BQ_PROJECT": "test-project"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Test initialization
            await session.initialize()
            print("✅ Server initialization successful")
            
            # Test list_tools
            tools = await session.list_tools()
            expected_tools = {"bq_validate_sql", "bq_dry_run_sql"}
            actual_tools = {tool.name for tool in tools}
            
            assert expected_tools == actual_tools, f"Expected {expected_tools}, got {actual_tools}"
            print("✅ Tools list matches specification")
            
            # Test tool schemas
            for tool in tools:
                assert hasattr(tool, 'inputSchema'), f"Tool {tool.name} missing inputSchema"
                assert 'properties' in tool.inputSchema, f"Tool {tool.name} schema missing properties"
                assert 'sql' in tool.inputSchema['properties'], f"Tool {tool.name} missing sql parameter"
            print("✅ Tool schemas are valid")
            
            # Test error handling
            try:
                await session.call_tool("nonexistent_tool", {})
                assert False, "Should have raised an error for nonexistent tool"
            except Exception:
                print("✅ Error handling works correctly")
            
            print("🎉 All MCP compliance tests passed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_compliance())
```

### Performance Test

```python title="test_performance.py"
import asyncio
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def performance_test():
    """Test MCP BigQuery server performance."""
    
    server_params = StdioServerParameters(
        command="mcp-bigquery",
        args=[],
        env={"BQ_PROJECT": "your-test-project"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test concurrent requests
            queries = [
                "SELECT 1",
                "SELECT COUNT(*) FROM unnest([1,2,3])",
                "SELECT 'hello' as greeting",
                "SELECT CURRENT_TIMESTAMP()",
                "SELECT * FROM unnest(['a', 'b', 'c']) as letter"
            ]
            
            start_time = time.time()
            
            tasks = []
            for query in queries:
                task = session.call_tool("bq_validate_sql", {"sql": query})
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ Validated {len(queries)} queries in {duration:.2f} seconds")
            print(f"📊 Average: {duration/len(queries):.3f} seconds per query")
            
            # Verify all results
            for i, result in enumerate(results):
                response = json.loads(result.content[0].text)
                assert response.get('isValid') == True, f"Query {i} failed validation"
            
            print("🎉 Performance test completed successfully!")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

## Troubleshooting

### Common Integration Issues

#### Protocol Version Mismatch
```
Error: Unsupported protocol version
```
**Solution**: Ensure your MCP client supports MCP 1.0 specification.

#### Transport Configuration
```
Error: Failed to establish stdio connection
```
**Solution**: Verify the command path and arguments are correct for your environment.

#### Environment Variables Not Set
```
Error: Could not determine credentials
```
**Solution**: Ensure all required environment variables are passed to the server process.

### Debug Tools

#### Raw MCP Communication Test
```bash
# Test server directly with JSON-RPC
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | mcp-bigquery
```

#### Environment Debug Script
```python
import os
import subprocess
import sys

def debug_environment():
    print("=== Environment Debug ===")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    
    # Check MCP BigQuery installation
    try:
        result = subprocess.run([sys.executable, "-m", "mcp_bigquery", "--version"], 
                              capture_output=True, text=True)
        print(f"MCP BigQuery: {result.stdout.strip()}")
    except Exception as e:
        print(f"MCP BigQuery: Error - {e}")
    
    # Check environment variables
    env_vars = ["BQ_PROJECT", "BQ_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"{var}: {value}")
    
    # Test Google Cloud authentication
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        print(f"BigQuery client: Connected to project {client.project}")
    except Exception as e:
        print(f"BigQuery client: Error - {e}")

if __name__ == "__main__":
    debug_environment()
```

## Best Practices

### Security
- Use service accounts with minimal permissions
- Rotate credentials regularly  
- Never expose credentials in logs or configuration files
- Use secure credential storage (Kubernetes secrets, etc.)

### Performance
- Implement connection pooling for high-frequency usage
- Cache session initialization when possible
- Use async/await patterns for concurrent operations
- Monitor resource usage in production

### Reliability
- Implement retry logic for transient failures
- Add circuit breakers for external dependencies
- Monitor server health and restart on failures
- Use structured logging for debugging

### Monitoring
- Track tool usage metrics
- Monitor BigQuery API quotas
- Log validation failures for analysis
- Set up alerting for authentication issues

## Support

For additional help with MCP client integration:

- Review the [MCP specification](https://spec.modelcontextprotocol.io/)
- Check [GitHub discussions](https://github.com/caron14/mcp-bigquery/discussions) for community solutions
- Submit [GitHub issues](https://github.com/caron14/mcp-bigquery/issues) for bugs or feature requests
- Join the MCP community for general protocol questions