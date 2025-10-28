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
def get_soql_help() -> dict[str, Any]:
    """
    Get comprehensive help documentation for SOQL (Salesforce Object Query Language).

    Returns:
        Dictionary containing SOQL syntax guide, examples, best practices, and common patterns.

    Reference: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_sosl_intro.htm
    """
    help_content = {
        "title": "SOQL (Salesforce Object Query Language) Reference Guide",
        "official_docs": "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_sosl_intro.htm",

        "overview": {
            "description": "SOQL is a query language similar to SQL for querying Salesforce data. It allows you to search your organization's Salesforce data for specific information.",
            "key_differences_from_sql": [
                "Cannot use SELECT * - must specify fields explicitly",
                "No JOIN keyword - use relationship queries instead",
                "Case-insensitive field and object names",
                "Limited to querying one object type per query (but can traverse relationships)",
                "No CASE WHEN statements - SOQL does not support conditional expressions"
            ]
        },

        "basic_syntax": {
            "structure": "SELECT fields FROM object [WHERE conditions] [ORDER BY field] [LIMIT number]",
            "required_clauses": ["SELECT", "FROM"],
            "optional_clauses": ["WHERE", "ORDER BY", "LIMIT", "OFFSET", "GROUP BY", "HAVING"],
            "examples": [
                {
                    "description": "Simple query",
                    "query": "SELECT Id, Name FROM Account"
                },
                {
                    "description": "Query with WHERE clause",
                    "query": "SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology'"
                },
                {
                    "description": "Query with LIMIT",
                    "query": "SELECT Id, Name FROM Contact LIMIT 10"
                },
                {
                    "description": "Query with ORDER BY",
                    "query": "SELECT Id, Name, CreatedDate FROM Account ORDER BY CreatedDate DESC"
                }
            ]
        },

        "field_selection": {
            "rules": [
                "MUST explicitly list all fields you want to retrieve",
                "Cannot use SELECT *",
                "Field names are case-insensitive but typically use CamelCase",
                "Use dot notation for relationship fields"
            ],
            "examples": [
                {
                    "description": "Select specific fields",
                    "query": "SELECT Id, Name, Email, Phone FROM Contact"
                },
                {
                    "description": "Select relationship field (parent)",
                    "query": "SELECT Id, Name, Account.Name FROM Contact"
                },
                {
                    "description": "Select relationship field (child subquery)",
                    "query": "SELECT Id, Name, (SELECT Id, Name FROM Contacts) FROM Account"
                }
            ]
        },

        "where_clause": {
            "operators": {
                "comparison": ["=", "!=", "<", "<=", ">", ">="],
                "logical": ["AND", "OR", "NOT"],
                "special": ["LIKE", "IN", "NOT IN", "INCLUDES", "EXCLUDES"]
            },
            "operator_notes": {
                "INCLUDES": "ONLY works with multi-select picklist fields. Checks if the field includes specified values (semi-colon separated in data).",
                "EXCLUDES": "ONLY works with multi-select picklist fields. Checks if the field excludes specified values.",
                "important": "INCLUDES and EXCLUDES cannot be used with regular text, number, or single-select picklist fields"
            },
            "examples": [
                {
                    "description": "Equality comparison",
                    "query": "SELECT Id, Name FROM Account WHERE Name = 'Acme'"
                },
                {
                    "description": "LIKE pattern matching",
                    "query": "SELECT Id, Name FROM Account WHERE Name LIKE 'Acme%'"
                },
                {
                    "description": "IN clause",
                    "query": "SELECT Id, Name FROM Account WHERE Industry IN ('Technology', 'Finance')"
                },
                {
                    "description": "Multiple conditions with AND",
                    "query": "SELECT Id, Name FROM Account WHERE Industry = 'Technology' AND AnnualRevenue > 1000000"
                },
                {
                    "description": "Date comparison",
                    "query": "SELECT Id, Name FROM Account WHERE CreatedDate > 2024-01-01T00:00:00Z"
                },
                {
                    "description": "NULL check",
                    "query": "SELECT Id, Name FROM Account WHERE Phone != NULL"
                },
                {
                    "description": "INCLUDES with multi-select picklist",
                    "query": "SELECT Id, Name FROM Product WHERE Features__c INCLUDES ('Feature1', 'Feature2')"
                },
                {
                    "description": "EXCLUDES with multi-select picklist",
                    "query": "SELECT Id, Name FROM Product WHERE Features__c EXCLUDES ('DeprecatedFeature')"
                }
            ]
        },

        "string_escaping_and_security": {
            "description": "Proper string escaping is essential to prevent SOQL injection and handle special characters",
            "single_quote_escaping": {
                "description": "Single quotes in string literals must be escaped",
                "methods": [
                    "Backslash escape: 'O\\'Brien' (preferred)",
                    "Double single quote: 'O''Brien' (alternative)"
                ],
                "examples": [
                    {
                        "description": "Name with apostrophe",
                        "query": "SELECT Id, Name FROM Account WHERE Name = 'O\\'Brien Industries'"
                    },
                    {
                        "description": "Search term with quote",
                        "query": "SELECT Id FROM Contact WHERE LastName LIKE 'D\\'%'"
                    }
                ]
            },
            "like_wildcard_escaping": {
                "description": "Special characters in LIKE patterns must be escaped with backslash",
                "wildcards": {
                    "%": "Matches zero or more characters",
                    "_": "Matches exactly one character",
                    "\\\\": "Literal backslash (escape the backslash itself)"
                },
                "escape_characters": ["\\%", "\\_", "\\\\"],
                "examples": [
                    {
                        "description": "Search for literal percent sign",
                        "query": "SELECT Id FROM Account WHERE Name LIKE '%\\%%'"
                    },
                    {
                        "description": "Search for literal underscore",
                        "query": "SELECT Id FROM Product WHERE Code LIKE 'ABC\\_123%'"
                    }
                ]
            },
            "soql_injection_prevention": {
                "description": "SOQL injection is a serious security risk when building dynamic queries",
                "best_practices": [
                    "NEVER concatenate user input directly into SOQL strings",
                    "Use parameterized queries or bind variables when available in your platform",
                    "Validate and sanitize all user input before using in queries",
                    "Escape single quotes in user-provided strings",
                    "Use allowlist validation for field names and object names (never trust user input for these)",
                    "Limit query permissions using sharing rules and field-level security"
                ],
                "dangerous_example": "// DANGEROUS: SELECT Id FROM Account WHERE Name = '<userInput>'",
                "safe_example": "// SAFE: Escape single quotes: userInput.replace(\"'\", \"\\\\'\") or use platform's bind variables"
            }
        },

        "relationship_queries": {
            "description": "SOQL uses relationship queries instead of JOINs to query related objects",
            "naming_conventions": {
                "description": "Understanding relationship naming is crucial for SOQL queries",
                "rules": [
                    "Standard relationships: use plural forms (Contacts, Opportunities, Cases)",
                    "Custom objects: end with __c (e.g., Custom_Object__c)",
                    "Custom fields: end with __c (e.g., Custom_Field__c)",
                    "Custom relationship fields (lookup/master-detail): use __r NOT __c when querying parent (e.g., Account__r.Name, not Account__c.Name)",
                    "Child-to-parent: RelationshipName__r for custom, RelationshipName for standard",
                    "Parent-to-child: RelationshipName__r (plural) for custom relationships"
                ],
                "examples": [
                    "Standard: SELECT Id, Account.Name FROM Contact (child to parent)",
                    "Custom lookup: SELECT Id, Account__r.Name FROM Custom_Object__c (use __r not __c)",
                    "Custom child records: SELECT Id, (SELECT Id, Name FROM Custom_Children__r) FROM Custom_Parent__c"
                ]
            },
            "parent_to_child": {
                "description": "Query child records from parent (subquery)",
                "syntax": "SELECT Id, (SELECT Id, Field FROM ChildObject) FROM ParentObject",
                "limitation": "Parent-to-child subqueries can only be 1 level deep. You CANNOT nest subqueries within subqueries.",
                "examples": [
                    {
                        "description": "Get Account with related Contacts",
                        "query": "SELECT Id, Name, (SELECT Id, Name, Email FROM Contacts) FROM Account"
                    },
                    {
                        "description": "Subquery with WHERE clause",
                        "query": "SELECT Id, Name, (SELECT Id, Amount FROM Opportunities WHERE StageName = 'Closed Won') FROM Account"
                    }
                ]
            },
            "child_to_parent": {
                "description": "Query parent fields from child record",
                "syntax": "SELECT Id, ParentObject.Field FROM ChildObject",
                "limitation": "Child-to-parent relationship traversal can go up to 5 levels deep using dot notation.",
                "examples": [
                    {
                        "description": "Get Contact with Account name",
                        "query": "SELECT Id, Name, Account.Name, Account.Industry FROM Contact"
                    },
                    {
                        "description": "Multi-level relationship",
                        "query": "SELECT Id, Name, Account.Owner.Name FROM Contact"
                    }
                ]
            }
        },

        "aggregate_functions": {
            "functions": ["COUNT()", "COUNT(field)", "COUNT_DISTINCT()", "SUM()", "AVG()", "MIN()", "MAX()"],
            "important_notes": [
                "Aggregate queries return different result structure",
                "Simple aggregate queries (e.g., SELECT COUNT() FROM Account) return a single result and CANNOT use LIMIT",
                "Aggregate queries WITH GROUP BY CAN use LIMIT to limit the number of groups returned",
                "Must use GROUP BY when mixing aggregate and non-aggregate fields",
                "SOQL does NOT support CASE WHEN statements for conditional aggregation (e.g., COUNT(CASE WHEN ...) is not allowed)",
                "To filter aggregate results, use WHERE clause before aggregation or use GROUP BY with multiple queries"
            ],
            "examples": [
                {
                    "description": "Count all records",
                    "query": "SELECT COUNT() FROM Account"
                },
                {
                    "description": "Count with field",
                    "query": "SELECT COUNT(Id) FROM Account WHERE Industry = 'Technology'"
                },
                {
                    "description": "Group by with aggregate",
                    "query": "SELECT Industry, COUNT(Id) FROM Account GROUP BY Industry"
                },
                {
                    "description": "Multiple aggregates",
                    "query": "SELECT SUM(Amount), AVG(Amount), MAX(Amount) FROM Opportunity WHERE StageName = 'Closed Won'"
                },
                {
                    "description": "Aggregate with alias",
                    "query": "SELECT Industry, COUNT(Id) total FROM Account GROUP BY Industry"
                },
                {
                    "description": "Conditional counting workaround - use separate queries",
                    "query": "-- Query 1: SELECT COUNT(Id) total_count FROM Opportunity WHERE CloseDate = TODAY\n-- Query 2: SELECT COUNT(Id) won_count FROM Opportunity WHERE CloseDate = TODAY AND IsWon = true"
                },
                {
                    "description": "Conditional counting workaround - use GROUP BY",
                    "query": "SELECT IsWon, COUNT(Id) count FROM Opportunity WHERE CloseDate = TODAY GROUP BY IsWon"
                }
            ]
        },

        "sorting_and_limiting": {
            "order_by": {
                "syntax": "ORDER BY field [ASC|DESC] [NULLS FIRST|NULLS LAST]",
                "examples": [
                    {
                        "description": "Sort ascending (default)",
                        "query": "SELECT Id, Name FROM Account ORDER BY Name"
                    },
                    {
                        "description": "Sort descending",
                        "query": "SELECT Id, Name FROM Account ORDER BY CreatedDate DESC"
                    },
                    {
                        "description": "Multiple sort fields",
                        "query": "SELECT Id, Name FROM Account ORDER BY Industry, Name"
                    },
                    {
                        "description": "Handle NULL values",
                        "query": "SELECT Id, Name FROM Account ORDER BY AnnualRevenue DESC NULLS LAST"
                    }
                ]
            },
            "limit_offset": {
                "description": "Control result set size and pagination",
                "examples": [
                    {
                        "description": "Limit results",
                        "query": "SELECT Id, Name FROM Account LIMIT 10"
                    },
                    {
                        "description": "Pagination with OFFSET",
                        "query": "SELECT Id, Name FROM Account ORDER BY Name LIMIT 10 OFFSET 20"
                    }
                ]
            }
        },

        "date_functions": {
            "date_literals": {
                "fixed": ["TODAY", "YESTERDAY", "TOMORROW", "THIS_WEEK", "LAST_WEEK", "THIS_MONTH", "LAST_MONTH",
                          "THIS_YEAR", "LAST_YEAR", "NEXT_WEEK", "NEXT_MONTH", "NEXT_YEAR",
                          "LAST_90_DAYS", "NEXT_90_DAYS", "THIS_QUARTER", "LAST_QUARTER", "NEXT_QUARTER",
                          "THIS_FISCAL_QUARTER", "LAST_FISCAL_QUARTER", "NEXT_FISCAL_QUARTER",
                          "THIS_FISCAL_YEAR", "LAST_FISCAL_YEAR", "NEXT_FISCAL_YEAR"],
                "parameterized": [
                    "LAST_N_DAYS:n (e.g., LAST_N_DAYS:7 for last 7 days)",
                    "NEXT_N_DAYS:n (e.g., NEXT_N_DAYS:30 for next 30 days)",
                    "LAST_N_WEEKS:n (e.g., LAST_N_WEEKS:4)",
                    "NEXT_N_WEEKS:n (e.g., NEXT_N_WEEKS:2)",
                    "LAST_N_MONTHS:n (e.g., LAST_N_MONTHS:6)",
                    "NEXT_N_MONTHS:n (e.g., NEXT_N_MONTHS:3)",
                    "LAST_N_QUARTERS:n (e.g., LAST_N_QUARTERS:2)",
                    "NEXT_N_QUARTERS:n (e.g., NEXT_N_QUARTERS:1)",
                    "LAST_N_YEARS:n (e.g., LAST_N_YEARS:5)",
                    "NEXT_N_YEARS:n (e.g., NEXT_N_YEARS:2)",
                    "LAST_N_FISCAL_QUARTERS:n",
                    "NEXT_N_FISCAL_QUARTERS:n",
                    "LAST_N_FISCAL_YEARS:n",
                    "NEXT_N_FISCAL_YEARS:n"
                ]
            },
            "date_functions": ["CALENDAR_YEAR()", "CALENDAR_MONTH()", "CALENDAR_QUARTER()", "DAY_IN_MONTH()",
                               "DAY_IN_WEEK()", "DAY_IN_YEAR()", "WEEK_IN_MONTH()", "WEEK_IN_YEAR()",
                               "HOUR_IN_DAY()", "DAY_ONLY()", "CALENDAR_MONTH()", "FISCAL_MONTH()",
                               "FISCAL_QUARTER()", "FISCAL_YEAR()"],
            "examples": [
                {
                    "description": "Query records from today",
                    "query": "SELECT Id, Name FROM Account WHERE CreatedDate = TODAY"
                },
                {
                    "description": "Query records from last month",
                    "query": "SELECT Id, Name FROM Opportunity WHERE CloseDate = LAST_MONTH"
                },
                {
                    "description": "Query records from this year",
                    "query": "SELECT Id, Amount FROM Opportunity WHERE CreatedDate = THIS_YEAR"
                },
                {
                    "description": "Date range query",
                    "query": "SELECT Id, Name FROM Account WHERE CreatedDate >= 2024-01-01 AND CreatedDate < 2024-12-31"
                }
            ]
        },

        "common_patterns": {
            "examples": [
                {
                    "description": "Get recently created records",
                    "query": "SELECT Id, Name FROM Account WHERE CreatedDate = LAST_N_DAYS:7 ORDER BY CreatedDate DESC"
                },
                {
                    "description": "Get recently modified records",
                    "query": "SELECT Id, Name, LastModifiedDate FROM Contact WHERE LastModifiedDate = TODAY"
                },
                {
                    "description": "Search with multiple criteria",
                    "query": "SELECT Id, Name, Email FROM Contact WHERE (FirstName LIKE 'John%' OR LastName LIKE 'John%') AND Email != NULL"
                },
                {
                    "description": "Query with picklist values",
                    "query": "SELECT Id, Name FROM Lead WHERE Status IN ('New', 'Working') AND Industry = 'Technology'"
                },
                {
                    "description": "Query custom objects",
                    "query": "SELECT Id, Name, Custom_Field__c FROM Custom_Object__c WHERE Active__c = true"
                }
            ]
        },

        "best_practices": [
            "Always use specific field names instead of SELECT *",
            "Use LIMIT to control result set size and improve performance",
            "Filter with WHERE clause to reduce data transfer",
            "Use indexed fields in WHERE clauses for better performance",
            "Avoid querying inside loops - query once and process results",
            "Be aware of governor limits (50,000 rows per query in most contexts)",
            "Use relationship queries instead of multiple queries when possible",
            "Test queries with small LIMIT first, then increase as needed",
            "Use ORDER BY with LIMIT for consistent pagination results",
            "Consider using aggregate queries for counts instead of retrieving all records",
            "NEVER use WHERE 1=1 - it's unnecessary and inefficient in SOQL queries"
        ],

        "common_errors": [
            {
                "error": "No such column 'FieldName' on entity",
                "solution": "Field name is misspelled or doesn't exist. Use describe_object tool to verify field names."
            },
            {
                "error": "sObject type 'ObjectName' is not supported",
                "solution": "Object name is incorrect or not accessible. Use list_objects tool to see available objects."
            },
            {
                "error": "expecting a semi-colon, found '*'",
                "solution": "Cannot use SELECT *. Must specify fields explicitly."
            },
            {
                "error": "aggregate result cannot be used with LIMIT",
                "solution": "This occurs with simple aggregate queries like SELECT COUNT() FROM Account LIMIT 10. Remove LIMIT from simple aggregate queries. Note: LIMIT CAN be used with GROUP BY aggregate queries."
            },
            {
                "error": "invalid SOQL query",
                "solution": "Check syntax, field names, and object names carefully."
            },
            {
                "error": "unexpected token: 'COUNT(CASE WHEN'",
                "solution": "SOQL does not support CASE WHEN statements. Use GROUP BY to separate conditions, or execute multiple queries with different WHERE clauses. Example: Instead of COUNT(CASE WHEN IsWon = true THEN 1 END), use GROUP BY IsWon or run separate queries."
            }
        ],

        "limitations": [
            "Maximum 50,000 rows returned per query (in most contexts)",
            "No SELECT * support",
            "No CASE WHEN statements or conditional expressions",
            "No conditional aggregation (e.g., COUNT(CASE WHEN ...) not supported)",
            "Parent-to-child subqueries: only 1 level deep (cannot nest subqueries within subqueries)",
            "Child-to-parent relationship traversal: maximum 5 levels (e.g., Account.Owner.Manager.Role.Name)",
            "Cannot use LIMIT with simple aggregate queries (e.g., SELECT COUNT() FROM Account LIMIT 10)",
            "LIMIT CAN be used with GROUP BY aggregate queries",
            "Some fields are not queryable or filterable"
        ],

        "additional_resources": [
            {
                "title": "SOQL SELECT Syntax",
                "url": "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm"
            },
            {
                "title": "SOQL WHERE Clause",
                "url": "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_conditionexpression.htm"
            },
            {
                "title": "Relationship Queries",
                "url": "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_relationships.htm"
            },
            {
                "title": "Aggregate Functions",
                "url": "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_agg_functions.htm"
            },
            {
                "title": "Date Functions and Literals",
                "url": "https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_dateformats.htm"
            }
        ]
    }

    return help_content


@mcp.tool()
def execute_soql_query(query: str) -> dict[str, Any]:
    """
    Execute a SOQL query against Salesforce.

    Args:
        query: The SOQL query string (e.g., 'SELECT Id, Name FROM Account LIMIT 10')

    Returns:
        Dictionary containing query, rows, row_count, and columns.

    IMPORTANT: Before constructing SOQL queries, use the get_soql_help() tool to understand:
        - Basic SOQL syntax and structure
        - How to write WHERE clauses and filters
        - Relationship queries (child-to-parent and parent-to-child)
        - Aggregate functions and GROUP BY
        - Common patterns and best practices

    Reference: https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm

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
