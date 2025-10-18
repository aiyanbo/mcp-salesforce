# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server implementation for Salesforce integration. MCP is a protocol that enables AI assistants to interact with external systems through standardized server implementations.

## Development Setup

### Package Manager
This project uses **uv** as the Python package manager. UV is a fast Python package installer and resolver written in Rust.

### Python Version
- Required: Python 3.13+
- Version is pinned in `.python-version`

### Common Commands

#### Environment Setup
```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install dependencies
uv pip install -e .
```

#### Running the Application
```bash
# Run the main script
python main.py

# Or run as module
python -m mcp_salesforce
```

#### Development Workflow
```bash
# Add new dependencies
uv pip install <package-name>

# Update dependencies
uv pip compile pyproject.toml -o requirements.txt

# Freeze current environment
uv pip freeze > requirements.txt
```

## Architecture Notes

### MCP Server Pattern
This project implements an MCP server, which means:
- It should expose tools/resources that can be called by MCP clients
- It needs to handle JSON-RPC 2.0 protocol communication
- It should implement proper authentication with Salesforce APIs
- Tools should be idempotent and handle errors gracefully

### Expected Structure
As this codebase grows, expect to see:
- `src/mcp_salesforce/` - Main package directory
  - `server.py` - MCP server implementation
  - `salesforce/` - Salesforce API client and utilities
  - `tools/` - Individual MCP tool implementations (SOQL queries, object operations, etc.)
  - `resources/` - MCP resource implementations
- `tests/` - Test suite
- Configuration for Salesforce credentials (should use environment variables)

### Key Considerations
- Salesforce authentication: OAuth 2.0 flow or username/password/token
- API versioning: Salesforce REST API versions should be configurable
- Rate limiting: Implement proper rate limiting to respect Salesforce API limits
- Error handling: Salesforce API errors should be properly translated to MCP error responses
- Bulk operations: Consider supporting Salesforce Bulk API for large data operations
