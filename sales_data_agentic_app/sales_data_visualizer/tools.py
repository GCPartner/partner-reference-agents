import os
import zlib
import json
import base64
import re
from typing import Dict, List, Any
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
from google.adk.tools.tool_context import ToolContext

CHART_SERVICE_URL = os.environ.get(
    "CHART_SERVICE_URL", 
    "https://chart-service-121968733869.us-central1.run.app"
)

_pool = None

def encode_a2ui_payload(payload: dict) -> str:
    """Compresses and base64-encodes the A2UI JSON payload to prevent LLM copy and truncation errors."""
    import zlib
    import base64
    json_str = json.dumps(payload)
    compressed = zlib.compress(json_str.encode('utf-8'))
    b64_str = base64.b64encode(compressed).decode('utf-8')
    return f"---a2ui_B64---\n{b64_str}"

def get_secret(secret_name: str) -> str:
    """Retrieves a secret from environment variables, local files, or Secret Manager."""
    val = os.environ.get(secret_name)
    if val:
        return val

    secret_file_path = f"secrets/{secret_name}"
    if os.path.exists(secret_file_path):
        try:
            with open(secret_file_path, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading local secret file {secret_name}: {e}")

    try:
        from google.cloud import secretmanager
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "agentspace-demo-1145-b")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Could not load secret {secret_name} from Secret Manager: {e}")

    return ""

def get_connection_pool():
    """Initializes and returns a SQLAlchemy connection pool to Cloud SQL."""
    global _pool
    if _pool:
        return _pool

    connection_name = get_secret("DB_CONNECTION_NAME")
    db_user = get_secret("DB_USER")
    db_pass = get_secret("DB_PASSWORD")
    db_name = get_secret("DB_NAME")

    if not all([connection_name, db_user, db_pass, db_name]):
        raise ValueError(
            "Database connection parameters are missing. Please configure "
            "DB_CONNECTION_NAME, DB_USER, DB_PASSWORD, and DB_NAME."
        )

    connector = Connector()

    def getconn():
        return connector.connect(
            connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PUBLIC,
        )

    _pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return _pool

def execute_read_only_query(sql_query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Executes a read-only SQL query against the consolidated sales database.
    Only SELECT statements are allowed.

    Args:
        sql_query: The SQL query string to execute.

    Returns:
        A dictionary containing 'status' ('success' or 'error') and 'data' (list of records).
    """
    # Programmatic SQL Guardrail
    cleaned_query = re.sub(r"\s+", " ", sql_query).strip().upper()
    
    # Strictly enforce SELECT statement
    if not cleaned_query.startswith("SELECT"):
        return {
            "status": "error",
            "message": "Only SELECT queries are authorized for execution. Mutating commands are strictly prohibited."
        }
        
    # Block blacklisted mutating keywords
    blacklist = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "GRANT", "REVOKE", "TRUNCATE"]
    for keyword in blacklist:
        if re.search(r"\b" + keyword + r"\b", cleaned_query):
            return {
                "status": "error",
                "message": f"Security violation: Mutation keyword '{keyword}' detected. Execution blocked."
            }

    try:
        pool = get_connection_pool()
        with pool.connect() as conn:
            result = conn.execute(sqlalchemy.text(sql_query))
            # Convert SQLAlchemy Row objects to serializable dicts
            records = [dict(row._mapping) for row in result]
            
            # Convert date/decimal objects to string/float for JSON serialization
            for rec in records:
                for k, v in rec.items():
                    if isinstance(v, (sqlalchemy.Numeric, float, int)) and not isinstance(v, int):
                        rec[k] = float(v)
                    elif hasattr(v, "isoformat"):
                        rec[k] = v.isoformat()
                    elif hasattr(v, "decimal"):
                        rec[k] = float(v)
                    elif type(v).__name__ == "Decimal":
                        rec[k] = float(v)

            return {
                "status": "success",
                "data": records
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database execution failed: {str(e)}"
        }

def generate_chart_url(
    chart_type: str, 
    data: List[Dict[str, Any]], 
    x_key: str, 
    y_key: str, 
    chart_title: str = "",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Generates a secure A2UI WebFrameUrl component containing an interactive chart.

    Args:
        chart_type: The type of chart ('bar', 'pie', 'line').
        data: The list of dictionaries containing the data.
        x_key: The dictionary key representing the X-axis labels (e.g. 'location').
        y_key: The dictionary key representing the Y-axis numeric values (e.g. 'sales').
        chart_title: The title of the chart.

    Returns:
        A dictionary containing the A2UI WebFrameUrl component block.
    """
    if not data:
        return {
            "status": "error",
            "message": "No data provided to generate chart."
        }
        
    chart_type = chart_type.lower()
    if chart_type not in ["bar", "pie", "line"]:
        chart_type = "bar"

    # Extract labels and values
    labels = []
    values = []
    
    for row in data:
        labels.append(str(row.get(x_key, "")))
        try:
            val = float(row.get(y_key, 0.0))
        except (ValueError, TypeError):
            val = 0.0
        values.append(val)

    # Curated premium palettes
    # 1. Multi-color palette for Pie Charts
    multi_colors = [
        "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", 
        "#ec4899", "#14b8a6", "#f43f5e", "#6366f1", "#06b6d4"
    ]
    # 2. Solid primary color for Bar/Line Charts (Blue)
    single_color = "#3b82f6"

    dataset = {
        "label": y_key.replace("_", " ").title(),
        "data": values
    }

    if chart_type == "pie":
        dataset["backgroundColor"] = multi_colors[:len(labels)]
    else:
        dataset["backgroundColor"] = [single_color] * len(labels)
        dataset["borderColor"] = single_color
        if chart_type == "line":
            dataset["fill"] = False
            dataset["tension"] = 0.2

    # Assemble Chart.js payload
    payload = {
        "t": chart_type,
        "h": chart_title,
        "l": labels,
        "d": [dataset]
    }

    try:
        # Compress using zlib and encode using base64url
        json_bytes = json.dumps(payload).encode("utf-8")
        compressed = zlib.compress(json_bytes)
        encoded_data = base64.urlsafe_b64encode(compressed).decode("utf-8")
        
        # Construct the final A2UI WebFrameUrl schema
        url = f"{CHART_SERVICE_URL}/render?data={encoded_data}"
        
        a2ui_payload = {
            "a2ui_messages": [
                {
                    "beginRendering": {
                        "surfaceId": "sales_chart",
                        "root": "chart_webframe"
                    }
                },
                {
                    "surfaceUpdate": {
                        "surfaceId": "sales_chart",
                        "components": [
                            {
                                "id": "chart_webframe",
                                "component": {
                                    "WebFrameUrl": {
                                        "url": {
                                            "literalString": url
                                        },
                                        "height": 420
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        return encode_a2ui_payload(a2ui_payload)
    except Exception as e:
        return f"Failed to generate chart: {str(e)}"

def show_greeting_ui(user_query: str, tool_context: ToolContext = None) -> str:
    """Generates the A2UI JSON payload for the interactive onboarding card with clickable shortcut buttons.
    
    You MUST call this tool when the user greets you or starts the conversation. You must pass the user's query string to this tool.
    """
    components = [
        {
            "id": "card",
            "component": {
                "Card": {
                    "child": "col"
                }
            }
        },
        {
            "id": "col",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            "title",
                            "desc",
                            "row"
                        ]
                    }
                }
            }
        },
        {
            "id": "title",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Sales Data Visualizer"
                    },
                    "usageHint": "h3"
                }
            }
        },
        {
            "id": "desc",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "I translate your sales questions into SQL queries and render interactive charts. Click a shortcut to start:"
                    },
                    "usageHint": "body"
                }
            }
        },
        {
            "id": "row",
            "component": {
                "Row": {
                    "children": {
                        "explicitList": [
                            "b1",
                            "b2",
                            "b3"
                        ]
                    },
                    "distribution": "spaceEvenly"
                }
            }
        },
        {
            "id": "b1",
            "component": {
                "Button": {
                    "child": "l1",
                    "primary": True,
                    "action": {
                        "name": "submit",
                        "context": [
                            {
                                "key": "message",
                                "value": {
                                    "literalString": "Show me a pie chart of data from top 5 states"
                                }
                            }
                        ]
                    }
                }
            }
        },
        {
            "id": "l1",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Top 5 States (Pie)"
                    }
                }
            }
        },
        {
            "id": "b2",
            "component": {
                "Button": {
                    "child": "l2",
                    "primary": True,
                    "action": {
                        "name": "submit",
                        "context": [
                            {
                                "key": "message",
                                "value": {
                                    "literalString": "Show me the total sales by product line in a bar graph"
                                }
                            }
                        ]
                    }
                }
            }
        },
        {
            "id": "l2",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Product Sales (Bar)"
                    }
                }
            }
        },
        {
            "id": "b3",
            "component": {
                "Button": {
                    "child": "l3",
                    "primary": True,
                    "action": {
                        "name": "submit",
                        "context": [
                            {
                                "key": "message",
                                "value": {
                                    "literalString": "Show me the sales trend for product line 'Electronics' over the last year"
                                }
                            }
                        ]
                    }
                }
            }
        },
        {
            "id": "l3",
            "component": {
                "Text": {
                    "text": {
                        "literalString": "Electronics Trend (Line)"
                    }
                }
            }
        }
    ]

    payload = {
        "a2ui_messages": [
            {
                "beginRendering": {
                    "surfaceId": "sales_greeting",
                    "root": "card"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "sales_greeting",
                    "components": components
                }
            }
        ]
    }

    return encode_a2ui_payload(payload)
