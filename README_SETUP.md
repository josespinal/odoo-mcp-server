# Odoo MCP Server Setup Guide

## Prerequisites

Before using the MCP server, you need to ensure your Odoo instance is properly configured:

### 1. Enable API Access in Odoo

1. Log into your Odoo instance at https://hzcont.odoo.com
2. Go to Settings → Users & Companies → Users
3. Select your user (admin)
4. Ensure "Developer Mode" is activated (Settings → Activate Developer Mode)
5. In the user form, check for "API Key" or "External API" settings

### 2. Generate API Key

1. In your user profile, look for "API Keys" or "Security" tab
2. Click "New API Key" or "Generate API Key"
3. Give it a description like "MCP Server Access"
4. Copy the generated key immediately (it won't be shown again)

### 3. Find Your Database Name

When logged into Odoo, check the URL. It might show the database name, or you can:
1. Go to Settings → Database Info (in Developer Mode)
2. Or check the browser's developer console for database info

### 4. Check Your Username

Your username might be:
- `admin`
- Your email address used to log in
- Check in Settings → Users → Your User → Login field

## Configuration

Update the `.env` file with the correct values:

```env
ODOO_URL=https://hzcont.odoo.com
ODOO_DB=hzcont              # Update this with actual database name
ODOO_USERNAME=admin         # Update this with your actual login
ODOO_API_KEY=your_api_key   # Update this with your generated API key
```

## Testing the Connection

Run the test script:
```bash
source venv/bin/activate
python test_connection.py
```

## MCP Server Configuration for Claude Desktop

Add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "/Users/viktorzeman/work/odoo-mcp-server/venv/bin/python",
      "args": ["-m", "mcp_server_odoo"],
      "cwd": "/Users/viktorzeman/work/odoo-mcp-server"
    }
  }
}
```

Note: We're using the virtual environment's Python to ensure all dependencies are available.

## Troubleshooting

1. **Authentication Failed**: 
   - Verify API key is active in Odoo
   - Check if XML-RPC is enabled (some Odoo instances disable it)
   - Ensure the user has proper permissions

2. **Database Not Found**:
   - The database name might be different from the subdomain
   - Try logging into Odoo and checking the actual database name

3. **Connection Refused**:
   - Ensure the URL doesn't include `/web` or other paths
   - Check if your IP is whitelisted (if Odoo has IP restrictions)