# NeoDB MCP Server

A Message Control Protocol (MCP) server implementation for interacting with [NeoDB](https://neodb.social/), a social book cataloging service. This server provides tools to fetch user information, search books, and retrieve detailed book information through NeoDB's API.

## Available Tools

The server provides the following tools:

1. **get-user-info**
   - Gets current user's basic information
   - No parameters required

2. **search-books**
   - Searches items in the catalog
   - Parameters:
     - `query` (string): Search query for books

3. **get-book**
   - Gets detailed information about a specific book
   - Parameters:
     - `book_id` (string): The ID of the book to retrieve

## Usage with Claude Desktop

### Get Access Token

[Official guide](https://neodb.net/api/)

### Update Config `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "neodb": {
      "command": "uv",
      "args": [
        "--directory",
        "<PATH_TO_PROJECT_DIR>",
        "run",
        "<PATH_TO_SCRIPT>",
        "<API_BASE> e.g. https://neodb.social",
        "<ACCESS_TOKEN>"
      ]
    }
  }
}
```

Where:
- `<API_BASE>`: The base URL for the NeoDB API
- `<ACCESS_TOKEN>`: Your NeoDB API access token

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
