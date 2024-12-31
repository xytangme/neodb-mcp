from typing import Any
import sys
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import asyncio
import json

server = Server("neodb")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="get-user-info",
            description="Get current user's basic info",
            inputSchema={
                "type": "object",
                "properties": {},  # No parameters needed
                "required": [],
            },
        ),
        types.Tool(
            name="search-books",
            description="Search items in catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for books",
                    }
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get-book",
            description="Get detailed information about a specific book",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "The ID of the book to retrieve",
                    },
                },
                "required": ["book_id"],
            },
        ),
    ]

async def make_neodb_request(client: httpx.AsyncClient, access_token: str, endpoint: str, api_base: str) -> dict[str, Any] | None:
    """
    Make an authenticated request to the NeoDB API

    Args:
        client (httpx.AsyncClient): The HTTP client to use
        access_token (str): The access token obtained from get_access_token
        endpoint (str): The API endpoint to call (e.g., '/api/me')
        api_base (str): The base URL for the NeoDB API

    Returns:
        dict: The API response
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    url = f"{api_base}{endpoint}"
    
    try:
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (4xx, 5xx status codes)
        return None, e.response.status_code
    except Exception as e:
        # Handle other errors (network issues, timeouts, etc)
        return None, 500  # Return 500 for internal errors


def format_book(book: dict) -> str:
    """Format a book into a concise string."""
    return (
        f"Title: {book.get('title', 'Unknown')}\n"
        f"Author: {book.get('author', 'Unknown')}\n"
        f"Rating: {book.get('rating', 'N/A')}\n"
        f"Description: {book.get('description', 'No description available')}\n"
        "---"
    )

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can fetch book data and return formatted responses.
    """
    # Access the configuration from server instance
    api_base = server.config.get("api_base")
    access_token = server.config.get("access_token")
    
    if not api_base or not access_token:
        return [types.TextContent(type="text", text="Server configuration missing API base URL or access token")]

    if name == "get-user-info":
        """
        https://neodb.social/developer/#/user/users_api_me
        """       
        async with httpx.AsyncClient() as client:
            user_data, status_code = await make_neodb_request(
                client,
                access_token,
                '/api/me',
                api_base
            )

            if status_code != 200:
                error_message = {
                    401: "Unauthorized",
                }.get(status_code, f"Request failed with status code: {status_code}")
                
                return [types.TextContent(type="text", text=error_message)]

            if not user_data:
                return [types.TextContent(type="text", text="Failed to retrieve user information")]

            # Format user information
            user_text = (
                f"User Information:\n"
                f"Username: {user_data.get('username', 'Unknown')}\n"
                f"Display Name: {user_data.get('display_name', 'Unknown')}\n"
                f"Email: {user_data.get('email', 'Not provided')}\n"
                f"URL: {user_data.get('url', 'Not provided')}\n"
                f"Account Created: {user_data.get('created_at', 'Unknown')}\n"
            )

            return [
                types.TextContent(
                    type="text",
                    text=user_text
                )
            ]

    elif name == "search-books":
        """
        https://neodb.social/developer/#/catalog/catalog_api_search_item
        #TBD category and page parameters not supported
        """
        query = arguments.get("query")
        if not query:
            raise ValueError("Missing query parameter")

        async with httpx.AsyncClient() as client:
            search_data, status_code = await make_neodb_request(
                client, 
                access_token,
                f"/api/catalog/search?query={query}&page=1",
                api_base
            )

            if status_code != 200:
                error_message = {
                    400: "Bad request",
                }.get(status_code, f"Request failed with status code: {status_code}")
                
                return [types.TextContent(type="text", text=error_message)]

            if not search_data:
                return [types.TextContent(type="text", text=f"Failed to search books")]

            books = search_data.get("data", [])
            if not books:
                return [types.TextContent(type="text", text=f"No books found for query: {query}")]

            # Format each book into a concise string
            formatted_books = [format_book(book) for book in books]
            books_text = f"Search results for '{query}':\n\n" + "\n".join(formatted_books)

            return [
                types.TextContent(
                    type="text",
                    text=books_text
                )
            ]

    elif name == "get-book":
        book_id = arguments.get("book_id")
        if not book_id:
            raise ValueError("Missing book_id parameter")

        async with httpx.AsyncClient() as client:
            book_data = await make_neodb_request(
                client,
                access_token,
                f"/api/book/{book_id}",
                api_base
            )

            if not book_data:
                return [types.TextContent(type="text", text=f"Failed to retrieve book with ID: {book_id}")]

            # Format detailed book information
            book_text = format_book(book_data)
            
            return [
                types.TextContent(
                    type="text",
                    text=book_text
                )
            ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Check if correct number of arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python script.py <api_base_url> <access_token>")
        sys.exit(1)
    
    # Get arguments from command line
    api_base = sys.argv[1]
    access_token = sys.argv[2]
        
    # Store configuration in server instance
    server.config = {
        "api_base": api_base,
        "access_token": access_token
    }
    
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="neodb",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())