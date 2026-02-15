"""Odoo client based on the odooly library."""

import os
import xmlrpc
import ssl
import http.client
from typing import Any, cast
from urllib.parse import urlparse

from pydantic import BaseModel, Field

try:
    from odooly import Client as OdoolyClient  # type: ignore
except Exception:  # pragma: no cover - odooly might not be installed in tests
    OdoolyClient = None  # type: ignore


class CustomClient(OdoolyClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport = CustomTransport()


class CustomHTTPTransport(xmlrpc.client.Transport):
    """Transport for HTTP (non-SSL) connections."""
    
    def send_headers(self, connection, headers):
        # Get custom header from environment variables
        header_name = os.getenv("ODOO_CUSTOM_HEADER_NAME", "X-API-KEY")
        header_value = os.getenv("ODOO_CUSTOM_HEADER_VALUE", "api-key")
        
        if header_name and header_value:
            connection.putheader(header_name, header_value)
            super().send_headers(connection, headers)
        else:
            super().send_headers(connection, headers)


class CustomTransport(xmlrpc.client.SafeTransport):
    def __init__(self, context=None, verify_ssl: bool = False):
        # Store verify_ssl flag first
        self.verify_ssl = verify_ssl
        
        # Create SSL context before calling parent constructor
        if context is None:
            if verify_ssl:
                # Use default SSL context with verification enabled
                context = ssl.create_default_context()
            else:
                # Disable SSL verification (useful for local development)
                # This handles self-signed certificates and older SSL/TLS versions
                context = ssl._create_unverified_context()
                # Explicitly disable hostname checking and certificate verification
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                # Set options for better compatibility with older servers
                # Allow older protocols that might be used by local Odoo instances
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3
                # Don't require specific ciphers
                context.set_ciphers('DEFAULT')
        
        # Store context before calling super().__init__ so parent can use it
        self.context = context
        super().__init__(context)

    def make_connection(self, host):
        """Override to ensure our SSL context is used for HTTPS connections."""
        # Ensure context is set correctly - this is critical for localhost HTTPS
        if not hasattr(self, 'context') or self.context is None:
            # Create unverified context as fallback
            self.context = ssl._create_unverified_context()
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE
            self.context.options |= ssl.OP_NO_SSLv2
            self.context.options |= ssl.OP_NO_SSLv3
            self.context.set_ciphers('DEFAULT')
        
        # Always ensure unverified settings when verify_ssl is False
        if not self.verify_ssl:
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE
        
        # Parse host and port
        if ':' in host:
            host_str, port_str = host.rsplit(':', 1)
            try:
                port = int(port_str)
                host = host_str
            except ValueError:
                port = 443
        else:
            port = 443
        
        # Create HTTPS connection with our unverified context
        # This bypasses any SSL verification issues for localhost
        return http.client.HTTPSConnection(host, port, context=self.context)

    def send_headers(self, connection, headers):
        # Get custom header from environment variables
        header_name = os.getenv("ODOO_CUSTOM_HEADER_NAME", "laportena")
        header_value = os.getenv("ODOO_CUSTOM_HEADER_VALUE", "ke8l5qeobg")
        
        if header_name and header_value:
            connection.putheader(header_name, header_value)
            super().send_headers(connection, headers)
        else:
            super().send_headers(connection, headers)


class OdooConfig(BaseModel):
    """Configuration for Odoo connection."""
    
    model_config = {"arbitrary_types_allowed": True}

    url: str = Field(..., description="Odoo instance URL")
    database: str = Field(..., description="Odoo database name")
    username: str = Field(..., description="Odoo username (e.g. email)")
    password: str | None = Field(None, description="Odoo password")
    api_key: str | None = Field(None, description="Odoo API key")
    timeout: int = Field(120, description="Request timeout in seconds")
    verify_ssl: bool = Field(False, description="Enable SSL certificate verification (set to True for production)")
    transport: CustomTransport | CustomHTTPTransport | None = Field(None, description="Custom transport")

    def model_post_init(self, __context: Any) -> None:  # pragma: no cover - pydantic hook
        """Validate that either password or api_key is provided."""
        if not self.password and not self.api_key:
            raise ValueError("Either password or api_key must be provided")


class OdooClient:
    """Client for interacting with Odoo via the odooly library."""

    def __init__(self, config: OdooConfig) -> None:
        """Initialize Odoo client with configuration."""
        if OdoolyClient is None:  # pragma: no cover - handled in tests
            raise ImportError("odooly is required to use OdooClient")

        self.config = config
        self.url = config.url.rstrip("/")
        self.database = config.database
        self.username = config.username
        self.password = config.api_key or config.password
        self.timeout = config.timeout
        self.uid: int | None = None
        
        # Detect HTTP vs HTTPS and use appropriate transport
        if config.transport:
            self.transport = config.transport
        else:
            parsed_url = urlparse(self.url)
            if parsed_url.scheme == "https":
                # Use SafeTransport for HTTPS connections
                self.transport = CustomTransport(verify_ssl=config.verify_ssl)
            elif parsed_url.scheme == "http":
                # Use regular Transport for HTTP connections (localhost)
                self.transport = CustomHTTPTransport()
            else:
                # Default to HTTPS transport if scheme is unclear
                self.transport = CustomTransport(verify_ssl=config.verify_ssl)
        
        # Initialise odooly client and environment
        self.client = OdoolyClient(
            self.url,
            self.database,
            self.username,
            self.password,
            transport=self.transport,
        )
        self.env = self.client.env

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def authenticate(self) -> int:
        """Authenticate with Odoo and return user ID."""
        if self.uid is None:
            self.uid = self.client.authenticate(
                self.database,
                self.username,
                self.password,
                {},
            )
            if not self.uid:
                raise ValueError("Authentication failed. Check your credentials.")
        return self.uid

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def search(
        self,
        model: str,
        domain: list[list[Any]] | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> Any:
        """Search for record IDs matching the domain."""
        domain = domain or []
        kwargs: dict[str, Any] = {"offset": offset}
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order

        return self.env[model].search(domain, **kwargs)

    def search_read(
        self,
        model: str,
        domain: list[list[Any]] | None = None,
        fields: list[str] | None = None,
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> Any:
        """Search and read records in a single call."""
        domain = domain or []
        kwargs: dict[str, Any] = {"offset": offset}
        if fields is not None:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order is not None:
            kwargs["order"] = order

        return self.env[model].search_read(domain, **kwargs)

    def read(
        self,
        model: str,
        ids: int | list[int],
        fields: list[str] | None = None,
    ) -> Any:
        """Read records by IDs."""
        if isinstance(ids, int):
            ids = [ids]

        kwargs: dict[str, Any] = {}
        if fields is not None:
            kwargs["fields"] = fields

        result = self.env[model].read(ids, **kwargs)
        return result[0] if len(ids) == 1 else result

    def create(
        self,
        model: str,
        values: dict[str, Any] | list[dict[str, Any]],
    ) -> Any:
        """Create one or more records."""
        single_record = isinstance(values, dict)
        if single_record:
            values_to_create = [cast(dict[str, Any], values)]
        else:
            values_to_create = cast(list[dict[str, Any]], values)

        result = self.env[model].create(values_to_create)
        return result[0] if single_record else result

    def write(
        self,
        model: str,
        ids: int | list[int],
        values: dict[str, Any],
    ) -> Any:
        """Update records."""
        if isinstance(ids, int):
            ids = [ids]

        return self.env[model].write(ids, values)

    def unlink(
        self,
        model: str,
        ids: int | list[int],
    ) -> Any:
        """Delete records."""
        if isinstance(ids, int):
            ids = [ids]

        return self.env[model].unlink(ids)

    def fields_get(
        self,
        model: str,
        fields: list[str] | None = None,
        attributes: list[str] | None = None,
    ) -> Any:
        """Get field definitions for a model."""
        kwargs: dict[str, Any] = {}
        if fields is not None:
            kwargs["fields"] = fields
        if attributes is not None:
            kwargs["attributes"] = attributes

        return self.env[model].fields_get(**kwargs)

    def get_model_list(self) -> Any:
        """Get list of all available models."""
        return self.env["ir.model"].search_read([], ["model", "name", "transient"])
