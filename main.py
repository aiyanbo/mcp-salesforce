"""
Salesforce MCP Server

This module implements an MCP server for Salesforce integration using FastMCP.
It provides tools to interact with Salesforce objects and run SOQL queries.
"""

import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from simple_salesforce import Salesforce

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Salesforce MCP Server")

# Global Salesforce client instance
sf_client: Salesforce | None = None


def get_salesforce_client() -> Salesforce:
    """
    Get or create a Salesforce client instance.

    Returns:
        Salesforce: Authenticated Salesforce client

    Raises:
        ValueError: If required environment variables are not set
    """
    global sf_client

    if sf_client is None:
        username = os.getenv("SALESFORCE_USERNAME")
        password = os.getenv("SALESFORCE_PASSWORD")
        security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")

        if not username or not password or not security_token:
            raise ValueError(
                "Missing required Salesforce credentials. "
                "Please set SALESFORCE_USERNAME, SALESFORCE_PASSWORD, and SALESFORCE_SECURITY_TOKEN "
                "environment variables."
            )

        sf_client = Salesforce(
            username=username,
            password=password,
            security_token=security_token
        )

    return sf_client


@mcp.tool()
def list_objects() -> dict[str, Any]:
    """
    List all available Salesforce objects.

    Returns:
        List of dictionaries containing object metadata including name, label,
        whether it's custom, and other attributes.
    """
    sf = get_salesforce_client()

    # Get global describe to list all objects
    describe = sf.describe()

    # Extract relevant information for each object
    objects = []
    for sobject in describe["sobjects"]:
        objects.append({
            "name": sobject["name"],
            "label": sobject["label"],
            "custom": sobject["custom"],
            "queryable": sobject["queryable"],
            "searchable": sobject["searchable"],
            "createable": sobject["createable"],
            "updateable": sobject["updateable"],
            "deletable": sobject["deletable"],
        })

    return {
        "objects": objects
    }


@mcp.tool()
def describe_object(object_name: str) -> dict[str, Any]:
    """
    Get all fields for a specific Salesforce object.

    Args:
        object_name: The API name of the Salesforce object (e.g., 'Account', 'Contact')

    Returns:
        Dictionary containing object name and list of field definitions.
    """
    sf = get_salesforce_client()

    # Get the object's describe information
    sobject = getattr(sf, object_name)
    describe = sobject.describe()

    # Extract field information
    fields = []
    for field in describe["fields"]:
        field_info = {
            "name": field["name"],
            "label": field["label"],
            "type": field["type"],
            "length": field.get("length"),
            "precision": field.get("precision"),
            "scale": field.get("scale"),
            "required": not field["nillable"],
            "unique": field["unique"],
            "createable": field["createable"],
            "updateable": field["updateable"],
            "calculated": field["calculated"],
            "defaultValue": field.get("defaultValue"),
        }

        # Add picklist values if applicable
        if field["type"] == "picklist" or field["type"] == "multipicklist":
            field_info["picklistValues"] = [
                {"label": pv["label"], "value": pv["value"]}
                for pv in field.get("picklistValues", [])
            ]

        # Add reference information if it's a lookup/master-detail
        if field.get("referenceTo"):
            field_info["referenceTo"] = field["referenceTo"]

        fields.append(field_info)

    return {
        "name": describe["name"],
        "label": describe["label"],
        "fields": fields
    }


@mcp.tool()
def execute_soql_query(query: str) -> dict[str, Any]:
    """
    Execute a SOQL query against Salesforce.

    Args:
        query: The SOQL query string (e.g., 'SELECT Id, Name FROM Account LIMIT 10')

    Returns:
        Dictionary containing query, rows, row_count, and columns.

    IMPORTANT: Before constructing SOQL queries, please read the official documentation:
        https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm
        Understanding the syntax and best practices will help generate more accurate queries.

    Important SOQL Rules:
        1. CANNOT use SELECT * - You MUST specify column names explicitly
        2. Aggregate queries (using COUNT, SUM, AVG, etc.) CANNOT use LIMIT
    """
    sf = get_salesforce_client()

    # Execute the query
    result = sf.query(query)

    # Extract records and remove 'attributes' field from each record
    rows = []
    for record in result["records"]:
        clean_record = {k: v for k, v in record.items() if k != "attributes"}
        rows.append(clean_record)

    # Extract column names from the first record
    columns = []
    if rows:
        columns = list(rows[0].keys())

    # Handle aggregate queries (e.g., SELECT COUNT() FROM Account)
    # When totalSize > 0 but columns and rows are empty
    if result["totalSize"] > 0 and not columns and not rows:
        columns = ["cnt"]
        rows = [{"cnt": result["totalSize"]}]

    # Format the response
    return {
        "query": query,
        "rows": rows,
        "row_count": result["totalSize"],
        "columns": columns,
    }


if __name__ == "__main__":
    mcp.run()
