# Salesforce MCP Server

An MCP (Model Context Protocol) server implementation for Salesforce integration, enabling AI assistants to interact with Salesforce data through standardized tools.

## Features

This MCP server provides three powerful tools for Salesforce integration:

- **list_objects**: List all available Salesforce objects with their metadata
- **describe_object**: Get detailed field information for a specific Salesforce object
- **execute_soql_query**: Execute SOQL queries against your Salesforce instance

## Prerequisites

- Python 3.13+
- A Salesforce account with API access
- Salesforce security token (see setup instructions below)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd mcp-salesforce
```

2. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

3. Install dependencies:
```bash
uv pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Salesforce credentials:
```env
SALESFORCE_USERNAME=your_username@example.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token
```

### Getting Your Salesforce Security Token

1. Log in to Salesforce
2. Go to **Setup** > **Personal Setup** > **My Personal Information** > **Reset My Security Token**
3. Click **Reset Security Token**
4. Check your email for the new security token

## Usage

### Running the Server

Start the MCP server using one of the following methods:

```bash
# Method 1: Run directly with Python
python main.py

# Method 2: Use the installed command
mcp-salesforce

# Method 3: Run with uv (recommended)
uv run mcp-salesforce
```

### Testing with MCP Inspector

The MCP Inspector is a powerful tool for testing and debugging your MCP server. It provides an interactive interface to explore available tools and test them with different parameters.

**Method 1: Using uv run with mcp-salesforce command (recommended)**
```bash
npx @modelcontextprotocol/inspector uv run mcp-salesforce
```

**Method 2: Using uv run with Python directly**
```bash
npx @modelcontextprotocol/inspector uv run python main.py
```

This will:
1. Start the MCP Inspector web interface
2. Launch your Salesforce MCP server
3. Open a browser window where you can:
   - View all available tools
   - Test each tool with custom parameters
   - See the JSON responses
   - Debug any issues

**Note:** Make sure your `.env` file is configured with valid Salesforce credentials before running the inspector.

### Available Tools

#### 1. list_objects

Lists all available Salesforce objects in your org.

**Returns:**
- Dictionary containing:
  - `objects`: Array of object metadata, each with:
    - `name`: API name of the object
    - `label`: Display label
    - `custom`: Whether it's a custom object
    - `queryable`: Whether it can be queried via SOQL
    - `searchable`: Whether it's searchable
    - `createable`: Whether new records can be created
    - `updateable`: Whether records can be updated
    - `deletable`: Whether records can be deleted

#### 2. describe_object

Get all fields for a specific Salesforce object.

**Parameters:**
- `object_name` (string): The API name of the Salesforce object (e.g., 'Account', 'Contact', 'CustomObject__c')

**Returns:**
- Dictionary containing:
  - `name`: Object API name
  - `fields`: Array of field definitions with:
    - `name`: Field API name
    - `label`: Field display label
    - `type`: Data type (string, number, date, picklist, etc.)
    - `length`, `precision`, `scale`: Size constraints
    - `required`: Whether the field is required
    - `unique`: Whether values must be unique
    - `createable`, `updateable`: Field permissions
    - `calculated`: Whether it's a formula field
    - `defaultValue`: Default value for the field
    - `picklistValues`: Available values (for picklist fields)
    - `referenceTo`: Referenced object (for lookup/master-detail fields)

#### 3. execute_soql_query

Execute SOQL (Salesforce Object Query Language) queries.

**Parameters:**
- `query` (string): The SOQL query string (e.g., 'SELECT Id, Name FROM Account LIMIT 10')

**Returns:**
- Dictionary containing:
  - `query`: The executed SOQL query string
  - `rows`: Array of records with queried fields
  - `row_count`: Total number of records returned
  - `columns`: Array of column names in the result set

**Important SOQL Rules:**
1. **CANNOT use SELECT \*** - You MUST specify column names explicitly
2. **Aggregate queries CANNOT use LIMIT** - Queries using COUNT, SUM, AVG, MIN, MAX cannot have LIMIT clause

**Example Queries:**
```sql
-- Get first 10 accounts
SELECT Id, Name, Industry FROM Account LIMIT 10

-- Get contacts with filters
SELECT Id, FirstName, LastName, Email FROM Contact WHERE Email != null LIMIT 20

-- Join query (using relationship)
SELECT Id, Name, Owner.Name FROM Account WHERE CreatedDate = TODAY
```

## Development

### Project Structure

```
mcp-salesforce/
├── main.py              # Main MCP server implementation
├── pyproject.toml       # Project configuration and dependencies
├── .env.example         # Example environment variables
├── .env                 # Your actual credentials (git-ignored)
└── README.md           # This file
```

### Dependencies

- **fastmcp**: Framework for building MCP servers
- **simple-salesforce**: Python client for Salesforce REST API
- **python-dotenv**: Load environment variables from .env files

### Adding to Claude Desktop

To use this MCP server with Claude Desktop, add the following to your Claude Desktop configuration:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-salesforce",
        "run",
        "mcp-salesforce"
      ]
    }
  }
}
```

Replace `/absolute/path/to/mcp-salesforce` with the actual path to your project directory.

**Alternative configuration using Python directly:**
```json
{
  "mcpServers": {
    "salesforce": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-salesforce",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```

## Error Handling

The server includes comprehensive error handling:

- **Missing Credentials**: Clear error message if environment variables are not set
- **Authentication Errors**: Salesforce API authentication failures are reported
- **Invalid Queries**: SOQL syntax errors are returned with helpful messages
- **API Limits**: Respects Salesforce API rate limits

## Security Notes

- Never commit your `.env` file to version control
- Keep your Salesforce security token secure
- Consider using OAuth 2.0 for production deployments
- Regularly rotate your security token

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions:
- Check the [simple-salesforce documentation](https://github.com/simple-salesforce/simple-salesforce)
- Review [Salesforce API documentation](https://developer.salesforce.com/docs/apis)
- Open an issue in this repository
