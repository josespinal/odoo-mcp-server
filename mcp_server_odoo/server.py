"""MCP server for Odoo integration."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import ValidationError

from .odoo_client import OdooClient, OdooConfig

# Load environment variables
# Look for .env file starting from this script's directory, then walk up the directory tree
# This ensures the .env file is found regardless of where the command is run from
script_dir = Path(__file__).parent
# Walk up from script directory looking for .env file
current_path = script_dir
while current_path != current_path.parent:
    env_file = current_path / ".env"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)
        break
    current_path = current_path.parent
else:
    # Fallback to default behavior (current working directory)
    load_dotenv()

# Initialize MCP server
server = Server("odoo-mcp-server")

# Global Odoo client instance
odoo_client: OdooClient | None = None


def get_odoo_client() -> OdooClient:
    """Get or create Odoo client instance."""
    global odoo_client

    if odoo_client is None:
        try:
            # Parse verify_ssl from environment (defaults to False for local development)
            verify_ssl_str = os.environ.get("ODOO_VERIFY_SSL", "false").lower()
            verify_ssl = verify_ssl_str in ("true", "1", "yes", "on")
            
            config = OdooConfig(
                url=os.environ["ODOO_URL"],
                database=os.environ["ODOO_DB"],
                username=os.environ["ODOO_USERNAME"],
                password=os.environ.get("ODOO_PASSWORD"),
                api_key=os.environ.get("ODOO_API_KEY"),
                timeout=int(os.environ.get("ODOO_TIMEOUT", "120")),
                verify_ssl=verify_ssl,
            )
            odoo_client = OdooClient(config)
        except (KeyError, ValidationError) as e:
            raise ValueError(f"Invalid Odoo configuration: {e}") from e

    return odoo_client


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_records",
            description="Search for Odoo records",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Odoo model name (e.g., 'res.partner', 'sale.order')",
                    },
                    "domain": {
                        "type": "array",
                        "description": "Search domain in Odoo format (e.g., [['name', 'ilike', 'john']])",
                        "items": {
                            "type": "array",
                            "items": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "number"},
                                    {"type": "boolean"},
                                    {
                                        "type": "array",
                                        "items": {
                                            "oneOf": [
                                                {"type": "string"},
                                                {"type": "number"},
                                                {"type": "boolean"}
                                            ]
                                        }
                                    }
                                ]
                            }
                        },
                    },
                    "fields": {
                        "type": "array",
                        "description": "List of fields to return",
                        "items": {"type": "string"},
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of records to skip",
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order (e.g., 'name asc, id desc')",
                    },
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="create_record",
            description="Create a new Odoo record",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "values": {
                        "type": "object",
                        "description": "Field values for the new record",
                    },
                },
                "required": ["model", "values"],
            },
        ),
        Tool(
            name="update_record",
            description="Update existing Odoo records",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "ids": {
                        "type": "array",
                        "description": "List of record IDs to update",
                        "items": {"type": "integer"},
                    },
                    "values": {
                        "type": "object",
                        "description": "Field values to update",
                    },
                },
                "required": ["model", "ids", "values"],
            },
        ),
        Tool(
            name="delete_record",
            description="Delete Odoo records",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "ids": {
                        "type": "array",
                        "description": "List of record IDs to delete",
                        "items": {"type": "integer"},
                    },
                },
                "required": ["model", "ids"],
            },
        ),
        Tool(
            name="get_record",
            description="Get specific Odoo records by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "ids": {
                        "type": "array",
                        "description": "List of record IDs to retrieve",
                        "items": {"type": "integer"},
                    },
                    "fields": {
                        "type": "array",
                        "description": "List of fields to return",
                        "items": {"type": "string"},
                    },
                },
                "required": ["model", "ids"],
            },
        ),
        Tool(
            name="list_models",
            description="List all available Odoo models",
            inputSchema={
                "type": "object",
                "properties": {
                    "transient": {
                        "type": "boolean",
                        "description": "Include transient (wizard) models",
                    },
                },
            },
        ),
        Tool(
            name="get_model_fields",
            description="Get field definitions for an Odoo model",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "fields": {
                        "type": "array",
                        "description": "Specific fields to get info for (optional)",
                        "items": {"type": "string"},
                    },
                },
                "required": ["model"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        client = get_odoo_client()

        if name == "search_records":
            result = await asyncio.to_thread(
                client.search_read,
                model=arguments["model"],
                domain=arguments.get("domain", []),
                fields=arguments.get("fields"),
                offset=arguments.get("offset", 0),
                limit=arguments.get("limit"),
                order=arguments.get("order"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "create_record":
            # Validate and normalize values parameter
            values = arguments["values"]

            if isinstance(values, dict):
                # Correct format - single record creation
                pass
            elif isinstance(values, list):
                # Check if it's a list of dictionaries (batch creation) or malformed
                if values and isinstance(values[0], dict):
                    # Valid batch creation
                    pass
                else:
                    # Malformed list - provide helpful error
                    raise ValueError(
                        f"Invalid 'values' format. Expected dictionary or list of dictionaries. "
                        f"Got {type(values).__name__} with contents: {values}"
                    )
            else:
                raise ValueError(
                    f"Invalid 'values' type. Expected dictionary or list of dictionaries. "
                    f"Got {type(values).__name__}: {values}"
                )

            result = await asyncio.to_thread(
                client.create,
                model=arguments["model"],
                values=values,
            )
            return [TextContent(type="text", text=f"Created record with ID: {result}")]

        elif name == "update_record":
            success = await asyncio.to_thread(
                client.write,
                model=arguments["model"],
                ids=arguments["ids"],
                values=arguments["values"],
            )
            return [
                TextContent(
                    type="text",
                    text=f"Update {'successful' if success else 'failed'} for IDs: {arguments['ids']}",
                )
            ]

        elif name == "delete_record":
            success = await asyncio.to_thread(
                client.unlink,
                model=arguments["model"],
                ids=arguments["ids"],
            )
            return [
                TextContent(
                    type="text",
                    text=f"Delete {'successful' if success else 'failed'} for IDs: {arguments['ids']}",
                )
            ]

        elif name == "get_record":
            result = await asyncio.to_thread(
                client.read,
                model=arguments["model"],
                ids=arguments["ids"],
                fields=arguments.get("fields"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "list_models":
            models = await asyncio.to_thread(client.get_model_list)
            if not arguments.get("transient", False):
                models = [m for m in models if not m.get("transient", False)]

            # Format output
            output = "Available Odoo models:\n"
            for model in sorted(models, key=lambda x: x["model"]):
                output += f"- {model['model']}: {model['name']}\n"

            return [TextContent(type="text", text=output)]

        elif name == "get_model_fields":
            fields = await asyncio.to_thread(
                client.fields_get,
                model=arguments["model"],
                fields=arguments.get("fields"),
            )
            return [TextContent(type="text", text=json.dumps(fields, indent=2, default=str))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {str(e)}")]


async def main() -> None:
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
