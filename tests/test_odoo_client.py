"""Tests for Odoo client."""

import pytest
from unittest.mock import MagicMock, patch
from mcp_server_odoo.odoo_client import OdooClient, OdooConfig


@pytest.fixture
def odoo_config():
    """Create test Odoo configuration."""
    return OdooConfig(
        url="https://hzcont.odoo.com",
        database="test_db",
        username="test_user",
        password="test_pass",
        timeout=60,
    )


@pytest.fixture
def odoo_client(odoo_config):
    """Create Odoo client with mocked XML-RPC."""
    with patch("xmlrpc.client.ServerProxy"):
        client = OdooClient(odoo_config)
        client.common = MagicMock()
        client.models = MagicMock()
        return client


class TestOdooConfig:
    """Test OdooConfig validation."""
    
    def test_valid_config_with_password(self):
        """Test valid config with password."""
        config = OdooConfig(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert config.password == "test_pass"
        assert config.api_key is None
        
    def test_valid_config_with_api_key(self):
        """Test valid config with API key."""
        config = OdooConfig(
            url="https://test.odoo.com",
            database="test_db",
            username="test_user",
            api_key="test_key",
        )
        assert config.api_key == "test_key"
        assert config.password is None
        
    def test_invalid_config_no_auth(self):
        """Test config without password or API key."""
        with pytest.raises(ValueError, match="Either password or api_key must be provided"):
            OdooConfig(
                url="https://test.odoo.com",
                database="test_db",
                username="test_user",
            )


class TestOdooClient:
    """Test OdooClient methods."""
    
    def test_authenticate_success(self, odoo_client):
        """Test successful authentication."""
        odoo_client.common.authenticate.return_value = 123
        
        uid = odoo_client.authenticate()
        
        assert uid == 123
        assert odoo_client.uid == 123
        odoo_client.common.authenticate.assert_called_once_with(
            "test_db", "test_user", "test_pass", {}
        )
        
    def test_authenticate_failure(self, odoo_client):
        """Test authentication failure."""
        odoo_client.common.authenticate.return_value = False
        
        with pytest.raises(ValueError, match="Authentication failed"):
            odoo_client.authenticate()
            
    def test_search_records(self, odoo_client):
        """Test search method."""
        odoo_client.uid = 123
        odoo_client.models.execute_kw.return_value = [1, 2, 3]
        
        result = odoo_client.search(
            "res.partner",
            [["name", "ilike", "test"]],
            limit=10,
            order="name asc"
        )
        
        assert result == [1, 2, 3]
        odoo_client.models.execute_kw.assert_called_once_with(
            "test_db",
            123,
            "test_pass",
            "res.partner",
            "search",
            ([["name", "ilike", "test"]],),
            {"offset": 0, "limit": 10, "order": "name asc"}
        )
        
    def test_search_read(self, odoo_client):
        """Test search_read method."""
        odoo_client.uid = 123
        expected_result = [
            {"id": 1, "name": "Test Partner 1"},
            {"id": 2, "name": "Test Partner 2"},
        ]
        odoo_client.models.execute_kw.return_value = expected_result
        
        result = odoo_client.search_read(
            "res.partner",
            [["active", "=", True]],
            fields=["name", "email"],
            limit=5
        )
        
        assert result == expected_result
        
    def test_read_single_record(self, odoo_client):
        """Test reading a single record."""
        odoo_client.uid = 123
        odoo_client.models.execute_kw.return_value = [{"id": 1, "name": "Test"}]
        
        result = odoo_client.read("res.partner", 1, ["name"])
        
        assert result == {"id": 1, "name": "Test"}
        
    def test_read_multiple_records(self, odoo_client):
        """Test reading multiple records."""
        odoo_client.uid = 123
        expected = [{"id": 1, "name": "Test1"}, {"id": 2, "name": "Test2"}]
        odoo_client.models.execute_kw.return_value = expected
        
        result = odoo_client.read("res.partner", [1, 2], ["name"])
        
        assert result == expected
        
    def test_create_single_record(self, odoo_client):
        """Test creating a single record."""
        odoo_client.uid = 123
        odoo_client.models.execute_kw.return_value = [42]
        
        result = odoo_client.create("res.partner", {"name": "New Partner"})
        
        assert result == 42
        
    def test_create_multiple_records(self, odoo_client):
        """Test creating multiple records."""
        odoo_client.uid = 123
        odoo_client.models.execute_kw.return_value = [42, 43]
        
        result = odoo_client.create(
            "res.partner",
            [{"name": "Partner 1"}, {"name": "Partner 2"}]
        )
        
        assert result == [42, 43]
        
    def test_write_records(self, odoo_client):
        """Test updating records."""
        odoo_client.uid = 123
        odoo_client.models.execute_kw.return_value = True
        
        result = odoo_client.write(
            "res.partner",
            [1, 2],
            {"active": False}
        )
        
        assert result is True
        
    def test_unlink_records(self, odoo_client):
        """Test deleting records."""
        odoo_client.uid = 123
        odoo_client.models.execute_kw.return_value = True
        
        result = odoo_client.unlink("res.partner", [1, 2])
        
        assert result is True
        
    def test_fields_get(self, odoo_client):
        """Test getting field definitions."""
        odoo_client.uid = 123
        expected = {
            "name": {"type": "char", "string": "Name", "required": True},
            "email": {"type": "char", "string": "Email"},
        }
        odoo_client.models.execute_kw.return_value = expected
        
        result = odoo_client.fields_get("res.partner", ["name", "email"])
        
        assert result == expected
        
    def test_get_model_list(self, odoo_client):
        """Test getting model list."""
        odoo_client.uid = 123
        expected = [
            {"model": "res.partner", "name": "Contact", "transient": False},
            {"model": "sale.order", "name": "Sales Order", "transient": False},
        ]
        odoo_client.models.execute_kw.return_value = expected
        
        result = odoo_client.get_model_list()
        
        assert result == expected