"""Tests for MCP server."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp_server_odoo.server import server, get_odoo_client, call_tool


@pytest.fixture
def mock_odoo_client():
    """Create mock Odoo client."""
    client = MagicMock()
    client.search_read = MagicMock()
    client.create = MagicMock()
    client.write = MagicMock()
    client.unlink = MagicMock()
    client.read = MagicMock()
    client.get_model_list = MagicMock()
    client.fields_get = MagicMock()
    return client


@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables."""
    monkeypatch.setenv("ODOO_URL", "https://test.odoo.com")
    monkeypatch.setenv("ODOO_DB", "test_db")
    monkeypatch.setenv("ODOO_USERNAME", "test_user")
    monkeypatch.setenv("ODOO_PASSWORD", "test_pass")


class TestServer:
    """Test MCP server functionality."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools."""
        from mcp_server_odoo.server import list_tools
        tools = await list_tools()
        
        tool_names = [tool.name for tool in tools]
        assert "search_records" in tool_names
        assert "create_record" in tool_names
        assert "update_record" in tool_names
        assert "delete_record" in tool_names
        assert "get_record" in tool_names
        assert "list_models" in tool_names
        assert "get_model_fields" in tool_names
        
    @pytest.mark.asyncio
    async def test_search_records_tool(self, mock_odoo_client, mock_env):
        """Test search_records tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.search_read.return_value = [
                {"id": 1, "name": "Test Partner"},
                {"id": 2, "name": "Another Partner"},
            ]
            
            result = await call_tool(
                "search_records",
                {
                    "model": "res.partner",
                    "domain": [["name", "ilike", "test"]],
                    "fields": ["name", "email"],
                    "limit": 10
                }
            )
            
            assert len(result) == 1
            assert result[0].type == "text"
            data = json.loads(result[0].text)
            assert len(data) == 2
            assert data[0]["name"] == "Test Partner"
            
    @pytest.mark.asyncio
    async def test_create_record_tool(self, mock_odoo_client, mock_env):
        """Test create_record tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.create.return_value = 42
            
            result = await call_tool(
                "create_record",
                {
                    "model": "res.partner",
                    "values": {"name": "New Partner", "email": "new@example.com"}
                }
            )
            
            assert len(result) == 1
            assert "Created record with ID: 42" in result[0].text
            
    @pytest.mark.asyncio
    async def test_update_record_tool(self, mock_odoo_client, mock_env):
        """Test update_record tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.write.return_value = True
            
            result = await call_tool(
                "update_record",
                {
                    "model": "res.partner",
                    "ids": [1, 2],
                    "values": {"active": False}
                }
            )
            
            assert len(result) == 1
            assert "Update successful" in result[0].text
            
    @pytest.mark.asyncio
    async def test_delete_record_tool(self, mock_odoo_client, mock_env):
        """Test delete_record tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.unlink.return_value = True
            
            result = await call_tool(
                "delete_record",
                {
                    "model": "res.partner",
                    "ids": [1, 2]
                }
            )
            
            assert len(result) == 1
            assert "Delete successful" in result[0].text
            
    @pytest.mark.asyncio
    async def test_get_record_tool(self, mock_odoo_client, mock_env):
        """Test get_record tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.read.return_value = {"id": 1, "name": "Test Partner"}
            
            result = await call_tool(
                "get_record",
                {
                    "model": "res.partner",
                    "ids": [1],
                    "fields": ["name", "email"]
                }
            )
            
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["id"] == 1
            assert data["name"] == "Test Partner"
            
    @pytest.mark.asyncio
    async def test_list_models_tool(self, mock_odoo_client, mock_env):
        """Test list_models tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.get_model_list.return_value = [
                {"model": "res.partner", "name": "Contact", "transient": False},
                {"model": "sale.order", "name": "Sales Order", "transient": False},
                {"model": "wizard.test", "name": "Test Wizard", "transient": True},
            ]
            
            result = await call_tool("list_models", {"transient": False})
            
            assert len(result) == 1
            assert "res.partner: Contact" in result[0].text
            assert "sale.order: Sales Order" in result[0].text
            assert "wizard.test" not in result[0].text
            
    @pytest.mark.asyncio
    async def test_get_model_fields_tool(self, mock_odoo_client, mock_env):
        """Test get_model_fields tool."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.fields_get.return_value = {
                "name": {"type": "char", "string": "Name"},
                "email": {"type": "char", "string": "Email"},
            }
            
            result = await call_tool(
                "get_model_fields",
                {"model": "res.partner", "fields": ["name", "email"]}
            )
            
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert "name" in data
            assert data["name"]["type"] == "char"
            
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_odoo_client, mock_env):
        """Test error handling in tools."""
        with patch("mcp_server_odoo.server.get_odoo_client", return_value=mock_odoo_client):
            mock_odoo_client.search_read.side_effect = Exception("Connection error")
            
            result = await call_tool(
                "search_records",
                {"model": "res.partner"}
            )
            
            assert len(result) == 1
            assert "Error: Exception: Connection error" in result[0].text
            
    @pytest.mark.asyncio
    async def test_unknown_tool(self, mock_env):
        """Test calling unknown tool."""
        result = await call_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert "Unknown tool: unknown_tool" in result[0].text