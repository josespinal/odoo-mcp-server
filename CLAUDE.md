# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for Odoo ERP integration. It enables AI assistants to interact with Odoo instances through a standardized protocol.

## Development Commands

```bash
# Install dependencies
pip install -e .
pip install -e ".[dev]"  # For development with test dependencies

# Run tests
pytest
pytest --cov  # With coverage report
pytest -v  # Verbose output

# Run the MCP server
python -m mcp_server_odoo

# Type checking
mypy mcp_server_odoo

# Linting
ruff check .
ruff format .
```

## Architecture

### Core Components

1. **MCP Server (`server.py`)**: Implements the MCP protocol, handling requests from AI assistants
2. **Odoo Client (`odoo_client.py`)**: XML-RPC client for Odoo API communication
3. **Tools (`tools.py`)**: MCP tool definitions for Odoo operations (search, create, update, delete)

### Key Design Patterns

- **Async/Await**: The server uses asyncio for handling concurrent requests
- **XML-RPC**: Communication with Odoo uses XML-RPC protocol through `xmlrpc.client`
- **Environment-based Config**: Sensitive data (URLs, credentials) stored in environment variables
- **Type Safety**: Use type hints throughout, validate with mypy

### MCP Tools Structure

Tools follow the MCP specification with:
- `name`: Unique identifier
- `description`: Human-readable purpose
- `input_schema`: JSON Schema for parameters
- `handler`: Async function implementing the tool logic

Example tool pattern:
```python
@server.tool()
async def search_records(model: str, domain: list = None, fields: list = None, limit: int = None):
    """Search Odoo records"""
    # Implementation
```

## Environment Configuration

Required environment variables (set in `.env` file):
- `ODOO_URL`: Full URL to Odoo instance (e.g., https://mycompany.odoo.com)
- `ODOO_DB`: Database name (optional if only one database)
- `ODOO_USERNAME`: Odoo username
- `ODOO_PASSWORD` or `ODOO_API_KEY`: Authentication credential

## Testing Approach

- Unit tests for individual components (client, tools)
- Integration tests with mock Odoo responses
- Test MCP protocol compliance
- Validate error handling and edge cases

## Common Odoo Models

When implementing tools, these are frequently used Odoo models:
- `res.partner`: Contacts (customers, suppliers)
- `sale.order`: Sales orders
- `account.move`: Invoices and accounting entries
- `product.product`: Products
- `stock.move`: Inventory movements

## Security Considerations

- Never expose Odoo credentials in logs or error messages
- Validate and sanitize all inputs before sending to Odoo
- Implement rate limiting for API calls
- Use read-only operations where possible
- Follow principle of least privilege for Odoo user permissions