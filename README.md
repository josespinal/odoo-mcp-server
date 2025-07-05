# MCP Server for Odoo

A Model Context Protocol (MCP) server that enables AI assistants to interact with Odoo ERP systems. This server provides tools for searching, creating, updating, and managing Odoo records through a standardized interface.

## Features

- 🔍 **Search Records**: Query any Odoo model with complex domain filters
- ➕ **Create Records**: Add new records to any Odoo model
- ✏️ **Update Records**: Modify existing records
- 🗑️ **Delete Records**: Remove records from the system
- 📊 **Read Records**: Fetch detailed information about specific records
- 🔗 **Execute Methods**: Call custom methods on Odoo models
- 📋 **List Models**: Discover available models in your Odoo instance
- 🔧 **Model Introspection**: Get field definitions for any model

## Installation

### Via pip (recommended)

```bash
pip install odoo-mcp-server
```

### From source

```bash
git clone https://github.com/vzeman/odoo-mcp-server.git
cd odoo-mcp-server
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in your project directory or set these environment variables:

```env
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username@example.com
ODOO_API_KEY=your-api-key-here
```

### Getting Odoo Credentials

1. **API Key**: 
   - Log into your Odoo instance
   - Go to Settings → Users & Companies → Users
   - Select your user
   - Under "API Keys" or "Security" tab, create a new API key
   - Copy the key immediately (it won't be shown again)

2. **Database Name**:
   - Usually visible in the URL when logged in
   - Or check Settings → Activate Developer Mode → Database Info

3. **Username**:
   - Your login email address

## Usage with Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "mcp_server_odoo"],
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DB": "your-database",
        "ODOO_USERNAME": "your-email@example.com",
        "ODOO_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

### search_records
Search for records in any Odoo model.

**Parameters:**
- `model` (required): The Odoo model name (e.g., 'res.partner', 'sale.order')
- `domain`: Odoo domain filter (default: [])
- `fields`: List of fields to return
- `limit`: Maximum number of records
- `offset`: Number of records to skip
- `order`: Sort order (e.g., 'name asc, id desc')

**Example prompts:**
- "Find all customers in California"
- "Show me sales orders from last month"
- "List products with stock quantity below 10"

### get_record
Get detailed information about specific records.

**Parameters:**
- `model` (required): The Odoo model name
- `ids` (required): List of record IDs
- `fields`: List of fields to return (optional)

**Example prompts:**
- "Show me details of customer with ID 42"
- "Get information about sales order SO0123"

### create_record
Create new records in Odoo.

**Parameters:**
- `model` (required): The Odoo model name
- `values` (required): Dictionary of field values

**Example prompts:**
- "Create a new customer named 'Acme Corp' with email contact@acme.com"
- "Add a new product called 'Widget Pro' with price $99.99"

### update_record
Update existing records.

**Parameters:**
- `model` (required): The Odoo model name
- `ids` (required): List of record IDs to update
- `values` (required): Dictionary of field values to update

**Example prompts:**
- "Update customer 42's phone number to +1-555-0123"
- "Change the status of sales order SO0123 to confirmed"

### delete_record
Delete records from Odoo (use with caution).

**Parameters:**
- `model` (required): The Odoo model name
- `ids` (required): List of record IDs to delete

**Example prompts:**
- "Delete the test customer record with ID 999"
- "Remove cancelled sales orders older than 2 years"

### execute_method
Execute custom methods on Odoo models.

**Parameters:**
- `model` (required): The Odoo model name
- `method` (required): Method name to execute
- `ids`: List of record IDs (if method requires)
- `args`: Additional positional arguments
- `kwargs`: Additional keyword arguments

**Example prompts:**
- "Confirm sales order SO0123"
- "Send invoice INV/2024/0001 by email"

### list_models
Discover available models in your Odoo instance.

**Parameters:**
- `transient`: Include transient (wizard) models (default: false)

**Example prompts:**
- "What models are available in Odoo?"
- "Show me all installed models"

### get_model_fields
Get field definitions for a model.

**Parameters:**
- `model` (required): The Odoo model name
- `fields`: Specific fields to get info for (optional)

**Example prompts:**
- "What fields are available on the customer model?"
- "Show me the structure of sales orders"

## Common Use Cases

### Customer Management
```
"Find all customers who haven't made a purchase in 6 months"
"Create a new contact for Acme Corp named John Doe"
"Update the credit limit for customer 'BigCo Industries'"
```

### Sales Operations
```
"Show me all draft quotations"
"Create a sales order for customer Acme Corp with 10 units of Product A"
"Convert quotation SO0123 to a confirmed order"
```

### Inventory Management
```
"List all products with stock below reorder point"
"Update the quantity on hand for SKU-12345"
"Find all pending stock moves"
```

### Financial Operations
```
"Show me all unpaid invoices"
"Create a vendor bill for Office Supplies Inc"
"List payments received today"
```

## Model Reference

Common Odoo models you can interact with:

- `res.partner` - Customers, suppliers, and contacts
- `sale.order` - Sales orders and quotations
- `account.move` - Invoices and bills
- `product.product` - Product variants
- `product.template` - Product templates
- `stock.move` - Stock movements
- `purchase.order` - Purchase orders
- `project.project` - Projects
- `project.task` - Project tasks
- `hr.employee` - Employees
- `res.users` - System users
- `res.company` - Companies

## Security Considerations

- Store credentials securely using environment variables
- Use API keys instead of passwords when possible
- Grant minimum necessary permissions to the API user
- Regularly rotate API keys
- Monitor API usage through Odoo's logs

## Troubleshooting

### Authentication Failed
- Verify your API key is active in Odoo
- Check if the username is correct (usually your email)
- Ensure the database name matches exactly

### Connection Refused
- Verify the Odoo URL (should not include `/web`)
- Check if your IP is whitelisted (if applicable)
- Ensure XML-RPC is enabled on your Odoo instance

### Model Not Found
- The model might require additional modules to be installed
- Use `list_models` to see available models
- Check if you have permissions for that model

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest
```

### Type Checking
```bash
mypy mcp_server_odoo
```

### Linting
```bash
ruff check .
ruff format .
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/vzeman/odoo-mcp-server/issues).