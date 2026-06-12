import json
import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# Standard colors for Chart.js datasets
COLORS = [
    "#4285F4", "#34A853", "#FBBC05", "#EA4335", "#1A73E8", 
    "#12B5CB", "#E8710A", "#9334E6", "#FC5C9C", "#137333"
]

def parse_and_describe_csv(csv_path: str, tool_context: ToolContext = None) -> str:
    """Parses an uploaded CSV file, detects columns for State, Revenue, and Offering,
    and returns a summary describing the structure and suggested chart types.
    
    Args:
        csv_path: Path to the CSV file to parse.
    """
    if not csv_path.startswith("gs://") and not os.path.exists(csv_path):
        return f"Error: CSV file not found at path '{csv_path}'."
    
    try:
        df = pd.read_csv(csv_path)
        cols = list(df.columns)
        num_rows = len(df)
        
        # Detect state column
        state_col = None
        for col in cols:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ["state", "region", "province", "territory", "location"]):
                state_col = col
                break
        
        # Detect revenue/metric column
        revenue_col = None
        for col in cols:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ["revenue", "sales", "amount", "performance", "income", "usd", "val", "value"]):
                revenue_col = col
                break
                
        # Detect service/offering column
        offering_col = None
        for col in cols:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ["offering", "service", "product", "line", "type", "category"]):
                offering_col = col
                break
        
        # Fallbacks if detection fails
        if not state_col:
            # First object/string column
            str_cols = df.select_dtypes(include=["object"]).columns
            if len(str_cols) > 0:
                state_col = str_cols[0]
        
        if not revenue_col:
            # First numeric column
            num_cols = df.select_dtypes(include=["number"]).columns
            if len(num_cols) > 0:
                revenue_col = num_cols[0]
                
        if not offering_col:
            # Second object column if it exists and differs from state_col
            str_cols = df.select_dtypes(include=["object"]).columns
            for col in str_cols:
                if col != state_col:
                    offering_col = col
                    break
        
        # Inferred mapping dictionary
        mapping = {
            "state_col": state_col,
            "revenue_col": revenue_col,
            "offering_col": offering_col
        }
        
        # Determine chart suggestions
        suggestions = ["bar"]
        if state_col and df[state_col].nunique() > 1:
            suggestions.append("pie")
        if offering_col and df[offering_col].nunique() > 1:
            suggestions.append("grouped_bar")
            
        # Store in session state via ToolContext
        if tool_context:
            tool_context.state["csv_file_path"] = csv_path
            tool_context.state["schema_mapping"] = mapping
            tool_context.state["suggested_chart_types"] = suggestions
            tool_context.state["schema_confirmed"] = False
            
        summary = {
            "status": "success",
            "columns": cols,
            "num_rows": num_rows,
            "mapping": mapping,
            "suggested_charts": suggestions,
            "state_uniques": int(df[state_col].nunique()) if state_col else 0,
            "offering_uniques": int(df[offering_col].nunique()) if offering_col else 0
        }
        
        return json.dumps(summary)
        
    except Exception as e:
        logger.error(f"Error parsing CSV: {e}")
        return json.dumps({"status": "error", "message": str(e)})


def generate_chart_ui(
    csv_path: str, 
    chart_type: str, 
    group_by: str, 
    filter_state: Optional[str] = None, 
    tool_context: ToolContext = None
) -> str:
    """Generates the A2UI message payload containing WebFrameSrcdoc with Chart.js config.
    
    Args:
        csv_path: Path to the CSV file.
        chart_type: Type of chart ('pie', 'bar', 'grouped_bar').
        group_by: Column to group by ('State' or 'Offering').
        filter_state: Optional filter to slice data by a single state.
    """
    if not csv_path.startswith("gs://") and not os.path.exists(csv_path):
        return "Error: CSV file not found."
        
    try:
        df = pd.read_csv(csv_path)
        
        # Get schema mapping from state or parse again if missing
        mapping = {}
        if tool_context and "schema_mapping" in tool_context.state:
            mapping = tool_context.state["schema_mapping"]
        else:
            # Simple inline inference fallback
            mapping = json.loads(parse_and_describe_csv(csv_path))["mapping"]
            
        state_col = mapping.get("state_col")
        revenue_col = mapping.get("revenue_col")
        offering_col = mapping.get("offering_col")
        
        if not state_col or not revenue_col:
            return "Error: Cannot identify State or Revenue columns."
            
        title = "Company Annual Performance"
        
        # Validate and normalize chart_type
        if chart_type not in ["pie", "bar", "grouped_bar"]:
            chart_type = "pie"
            
        # Filter if a state filter is applied
        if filter_state:
            df = df[df[state_col] == filter_state]
            title = f"Performance breakdown in {filter_state}"
            
        chart_data = {}
        js_chart_type = "pie"
        
        # Case 1: Pie Chart
        if chart_type == "pie":
            group_col = state_col if group_by == "State" else offering_col
            if not group_col:
                group_col = state_col
                
            agg = df.groupby(group_col)[revenue_col].sum().reset_index()
            agg = agg.sort_values(by=revenue_col, ascending=False)
            
            if len(agg) > 5:
                top_5 = agg.head(5)
                other_sum = agg.iloc[5:][revenue_col].sum()
                other_row = pd.DataFrame([{group_col: "Other", revenue_col: other_sum}])
                agg = pd.concat([top_5, other_row], ignore_index=True)
                
            labels = agg[group_col].tolist()
            data = agg[revenue_col].tolist()
            
            chart_data = {
                "labels": labels,
                "datasets": [{
                    "data": [float(v) for v in data],
                    "backgroundColor": COLORS[:len(labels)],
                    "borderWidth": 1
                }]
            }
            js_chart_type = "pie"
            
        # Case 2: Grouped Bar Chart (breakdown of service offerings in each state)
        elif chart_type == "grouped_bar" and offering_col:
            pivot = df.pivot_table(index=state_col, columns=offering_col, values=revenue_col, aggfunc="sum").fillna(0)
            
            pivot["Total"] = pivot.sum(axis=1)
            pivot = pivot.sort_values(by="Total", ascending=False).head(6).drop(columns=["Total"])
            
            labels = pivot.index.tolist()
            datasets = []
            
            for i, col in enumerate(pivot.columns):
                datasets.append({
                    "label": str(col),
                    "data": [float(v) for v in pivot[col].tolist()],
                    "backgroundColor": COLORS[i % len(COLORS)]
                })
                
            chart_data = {
                "labels": labels,
                "datasets": datasets
            }
            js_chart_type = "bar"
            title = "Performance by Service Offering in Top States"
            
        # Case 3: Standard Bar Chart
        else:
            group_col = state_col if group_by == "State" else offering_col
            if not group_col:
                group_col = state_col
                
            agg = df.groupby(group_col)[revenue_col].sum().reset_index()
            agg = agg.sort_values(by=revenue_col, ascending=False)
            
            if len(agg) > 10:
                agg = agg.head(10)
                title += " (Top 10)"
                
            labels = agg[group_col].tolist()
            data = agg[revenue_col].tolist()
            
            chart_data = {
                "labels": labels,
                "datasets": [{
                    "label": "Revenue (USD)",
                    "data": [float(v) for v in data],
                    "backgroundColor": COLORS[0],
                    "borderWidth": 1
                }]
            }
            js_chart_type = "bar"
            
        # Generate the WebFrame HTML content
        html_content = get_html_template(chart_data, js_chart_type)
        
        # Build A2UI Components list
        surface_id = "performance_charts"
        
        # Generate Quick-Action toggle buttons
        buttons = []
        btn_ids = []
        suggestions = ["pie", "bar", "grouped_bar"]
            
        for s in suggestions:
            btn_label_id = f"btn_lbl_{s}"
            btn_id = f"btn_{s}"
            
            label_text = f"Show as {s.replace('_', ' ').title()}"
            
            # Define button action payload
            action = {
                "name": "submit",
                "context": [
                    {"key": "message", "value": {"literalString": f"Display the data as a {s.replace('_', ' ')}."}},
                    {"key": "action", "value": {"literalString": "changeChartType"}},
                    {"key": "chart_type", "value": {"literalString": s}}
                ]
            }
            
            buttons.extend([
                {
                    "id": btn_label_id,
                    "component": {
                        "Text": {
                            "text": {"literalString": label_text.replace("Grouped Bar", "Breakdown")}
                        }
                    }
                },
                {
                    "id": btn_id,
                    "component": {
                        "Button": {
                            "child": btn_label_id,
                            "primary": (s == chart_type),
                            "action": action
                        }
                    }
                }
            ])
            btn_ids.append(btn_id)
            
        components = [
            {
                "id": "chart_container",
                "component": {
                    "Column": {
                        "children": {"explicitList": ["chart_title", "toggle_row", "chart_frame"]}
                    }
                }
            },
            {
                "id": "chart_title",
                "component": {
                    "Text": {
                        "text": {"literalString": title},
                        "usageHint": "h3"
                    }
                }
            },
            {
                "id": "toggle_row",
                "component": {
                    "Row": {
                        "children": {"explicitList": btn_ids},
                        "gap": "10px"
                    }
                }
            },
            {
                "id": "chart_frame",
                "component": {
                    "WebFrameSrcdoc": {
                        "view_type": "AnalyticsChart",
                        "height": 400,
                        "srcdoc": html_content
                    }
                }
            }
        ]
        
        # Append dynamic buttons
        components.extend(buttons)
        
        # Save current state parameters
        if tool_context:
            tool_context.state["current_chart_type"] = chart_type
            tool_context.state["current_group_by"] = group_by
            if filter_state:
                tool_context.state["current_filter_state"] = filter_state
                
        a2ui_payload = {
            "a2ui_messages": [
                {"beginRendering": {"surfaceId": "performance_charts", "root": "chart_container"}},
                {"surfaceUpdate": {"surfaceId": "performance_charts", "components": components}}
            ]
        }
        
        json_str = json.dumps(a2ui_payload)
        
        # Store in session state for validation/retrieval
        if tool_context:
            tool_context.state["a2ui_json"] = json_str
            
        return f"{title} rendered in dashboard.\n---a2ui_JSON---\n{json_str}\n"
        
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return f"Error generating chart: {str(e)}"


def get_html_template(chart_data: dict, chart_type: str) -> str:
    """Returns a self-contained HTML page representing a pure CSS/SVG visualizer (no CDNs)."""
    import math

    # 1. Pie/Doughnut Chart
    if chart_type == "pie":
        labels = chart_data.get("labels", [])
        dataset = chart_data.get("datasets", [{}])[0]
        data = dataset.get("data", [])
        bg_colors = dataset.get("backgroundColor", COLORS)
        
        total = sum(data)
        if total == 0:
            return "<div>No data to display.</div>"
            
        cx, cy, r = 100, 100, 80
        paths = []
        current_angle = -math.pi / 2  # start at 12 o'clock
        
        for i, (label, val) in enumerate(zip(labels, data)):
            percentage = val / total
            angle_delta = percentage * 2 * math.pi
            end_angle = current_angle + angle_delta
            
            # Start and End points for outer arc
            x1 = cx + r * math.cos(current_angle)
            y1 = cy + r * math.sin(current_angle)
            x2 = cx + r * math.cos(end_angle)
            y2 = cy + r * math.sin(end_angle)
            
            large_arc = 1 if percentage > 0.5 else 0
            
            # Draw standard slice path
            path_d = f"M {cx} {cy} L {x1:.2f} {y1:.2f} A {r} {r} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z"
            color = bg_colors[i % len(bg_colors)]
            
            paths.append(f"""
            <path d="{path_d}" fill="{color}" class="pie-slice">
              <title>{label}: ${val:,.2f} ({percentage*100:.1f}%)</title>
            </path>
            """)
            current_angle = end_angle
            
        svg_content = "\n".join(paths)
        
        # Legend items HTML
        legend_items = []
        for i, (label, val) in enumerate(zip(labels, data)):
            color = bg_colors[i % len(bg_colors)]
            legend_items.append(f"""
            <div class="legend-item">
              <span class="legend-color-box" style="background-color: {color};"></span>
              <span class="legend-text">{label} (${val:,.2f})</span>
            </div>
            """)
        legend_html = "\n".join(legend_items)
        
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Security-Policy" content="connect-src 'none'">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 15px;
      background-color: #ffffff;
      overflow: hidden;
    }}
    .chart-layout {{
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: center;
      gap: 30px;
      height: 360px;
    }}
    .svg-area {{
      width: 220px;
      height: 220px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    svg {{
      width: 100%;
      height: 100%;
      filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.06));
    }}
    .pie-slice {{
      cursor: pointer;
      transition: opacity 0.2s ease, transform 0.2s ease;
      transform-origin: 100px 100px;
    }}
    .pie-slice:hover {{
      opacity: 0.85;
      transform: scale(1.03);
    }}
    .legend-area {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 280px;
      font-size: 14px;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 4px;
      transition: background 0.15s ease;
    }}
    .legend-item:hover {{
      background: #f3f4f6;
    }}
    .legend-color-box {{
      width: 12px;
      height: 12px;
      border-radius: 3px;
      flex-shrink: 0;
    }}
    .legend-text {{
      color: #374151;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
  </style>
</head>
<body>
  <div class="chart-layout">
    <div class="svg-area">
      <svg width="100%" height="100%" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        {svg_content}
      </svg>
    </div>
    <div class="legend-area">
      {legend_html}
    </div>
  </div>
</body>
</html>
"""

    # 2 & 3. Standard and Grouped Bar Charts
    else:
        labels = chart_data.get("labels", [])
        datasets = chart_data.get("datasets", [])
        
        # Calculate scales
        all_values = []
        for ds in datasets:
            all_values.extend(ds.get("data", []))
        
        max_val = max(all_values) if all_values else 1.0
        # Round up to clean power of 10 or nice multiple
        y_max = max_val * 1.15
        
        # SVG Viewbox: 600 x 320
        svg_w, svg_h = 600, 320
        margin_l, margin_r, margin_t, margin_b = 70, 30, 40, 50
        graph_w = svg_w - margin_l - margin_r
        graph_h = svg_h - margin_t - margin_b
        
        svg_bars = []
        svg_labels = []
        svg_grid = []
        
        # Draw Y-Axis labels and grid lines
        grid_ticks = 4
        for step in range(grid_ticks + 1):
            ratio = step / grid_ticks
            val_label = ratio * max_val
            y_pos = margin_t + graph_h - (ratio * graph_h)
            
            # Grid Line
            svg_grid.append(f'<line x1="{margin_l}" y1="{y_pos}" x2="{margin_l + graph_w}" y2="{y_pos}" stroke="#e5e7eb" stroke-dasharray="4 4" />')
            
            # Y label
            if val_label >= 1_000_000:
                label_str = f"${val_label/1_000_000:.1f}M"
            elif val_label >= 1_000:
                label_str = f"${val_label/1_000:.0f}K"
            else:
                label_str = f"${val_label:.0f}"
            
            svg_grid.append(f'<text x="{margin_l - 10}" y="{y_pos + 4}" text-anchor="end" font-size="11" fill="#6b7280">{label_str}</text>')
            
        num_groups = len(labels)
        num_datasets = len(datasets)
        
        group_width = graph_w / max(num_groups, 1)
        
        # Build Legend for Grouped Bar
        legend_html = ""
        if num_datasets > 1:
            legend_items = []
            for i, ds in enumerate(datasets):
                color = ds.get("backgroundColor", COLORS[i % len(COLORS)])
                legend_items.append(f"""
                <div class="legend-item-inline">
                  <span class="legend-color-box" style="background-color: {color};"></span>
                  <span>{ds.get("label", "")}</span>
                </div>
                """)
            legend_html = f'<div class="legend-inline">{"".join(legend_items)}</div>'
            
        # Draw Bars
        for g_idx, group_label in enumerate(labels):
            group_x = margin_l + g_idx * group_width
            
            # X Axis Label
            x_label_center = group_x + group_width / 2
            
            # Handle rotating labels if there are many to avoid collision
            rotate_attr = 'transform="rotate(-20, {}, {})"'.format(x_label_center, margin_t + graph_h + 18) if len(labels) > 6 else ''
            
            svg_labels.append(f"""
            <text x="{x_label_center}" y="{margin_t + graph_h + 18}" text-anchor="middle" font-size="12" font-weight="500" fill="#374151" {rotate_attr}>
              {group_label}
            </text>
            """)
            
            # Calculate dynamic bar width
            total_bars_padding = group_width * 0.25
            available_bar_space = group_width - total_bars_padding
            bar_width = available_bar_space / num_datasets
            
            for d_idx, ds in enumerate(datasets):
                val_list = ds.get("data", [])
                val = val_list[g_idx] if g_idx < len(val_list) else 0.0
                
                bar_h = (val / y_max) * graph_h if y_max > 0 else 0
                bar_x = group_x + (total_bars_padding / 2) + d_idx * bar_width
                bar_y = margin_t + graph_h - bar_h
                
                color = ds.get("backgroundColor", COLORS[d_idx % len(COLORS)])
                
                # Rectangle SVG bar with rounded top corners
                svg_bars.append(f"""
                <g class="bar-group">
                  <rect x="{bar_x:.2f}" y="{bar_y:.2f}" width="{bar_width-2:.2f}" height="{bar_h:.2f}" fill="{color}" rx="3" class="bar">
                    <title>{ds.get("label", "Revenue")}: ${val:,.2f}</title>
                  </rect>
                </g>
                """)
                
        svg_content = "\n".join(svg_grid) + "\n" + "\n".join(svg_bars) + "\n" + "\n".join(svg_labels)
        
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Security-Policy" content="connect-src 'none'">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 10px 15px;
      background-color: #ffffff;
      overflow: hidden;
    }}
    .chart-container {{
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 380px;
    }}
    .svg-area {{
      width: 100%;
      height: 320px;
    }}
    svg {{
      width: 100%;
      height: 100%;
    }}
    .bar {{
      cursor: pointer;
      transition: fill 0.2s ease, opacity 0.2s ease;
    }}
    .bar:hover {{
      opacity: 0.85;
      filter: brightness(0.95);
    }}
    .legend-inline {{
      display: flex;
      flex-direction: row;
      justify-content: center;
      gap: 15px;
      margin-bottom: 8px;
      font-size: 13px;
      color: #4b5563;
      flex-wrap: wrap;
    }}
    .legend-item-inline {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .legend-color-box {{
      width: 11px;
      height: 11px;
      border-radius: 2px;
      flex-shrink: 0;
    }}
  </style>
</head>
<body>
  <div class="chart-container">
    {legend_html}
    <div class="svg-area">
      <svg width="100%" height="100%" viewBox="0 0 {svg_w} {svg_h}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
        <!-- Axes -->
        <line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + graph_h}" stroke="#d1d5db" stroke-width="1.5" />
        <line x1="{margin_l}" y1="{margin_t + graph_h}" x2="{margin_l + graph_w}" y2="{margin_t + graph_h}" stroke="#d1d5db" stroke-width="1.5" />
        {svg_content}
      </svg>
    </div>
  </div>
</body>
</html>
"""



def generate_schema_form(csv_path: str, tool_context: ToolContext = None) -> str:
    """Generates the A2UI message payload containing interactive MultipleChoice selectors 
    and a Confirm button to confirm the spreadsheet columns.
    
    Args:
        csv_path: Path to the CSV file to map.
    """
    if not csv_path.startswith("gs://") and not os.path.exists(csv_path):
        return json.dumps({"status": "error", "message": "CSV file not found."})
        
    try:
        df = pd.read_csv(csv_path)
        cols = list(df.columns)
        
        # Detect defaults
        state_col = None
        for col in cols:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ["state", "region", "province", "territory", "location"]):
                state_col = col
                break
        if not state_col and len(cols) > 0:
            state_col = cols[0]
            
        revenue_col = None
        for col in cols:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ["revenue", "sales", "amount", "performance", "income", "usd", "val", "value"]):
                revenue_col = col
                break
        if not revenue_col and len(cols) > 1:
            revenue_col = cols[1]
            
        offering_col = None
        for col in cols:
            col_lower = str(col).lower()
            if any(term in col_lower for term in ["offering", "service", "product", "line", "type", "category"]):
                offering_col = col
                break
        if not offering_col:
            for col in cols:
                if col != state_col and col != revenue_col:
                    offering_col = col
                    break
        if not offering_col and len(cols) > 2:
            offering_col = cols[2]

        options = [{"value": col, "label": {"literalString": col}} for col in cols]
        
        # Save pre-selected values inside the session state
        if tool_context:
            tool_context.state["csv_file_path"] = csv_path
            tool_context.state["selected_state_col"] = state_col
            tool_context.state["selected_revenue_col"] = revenue_col
            tool_context.state["selected_offering_col"] = offering_col
            tool_context.state["schema_confirmed"] = False

        import time
        surface_id = f"schema_form_{int(time.time())}"

        a2ui_payload = {
            "a2ui_messages": [
                {
                    "beginRendering": {
                        "surfaceId": surface_id,
                        "root": "root_col"
                    }
                },
                {
                    "surfaceUpdate": {
                        "surfaceId": surface_id,
                        "components": [
                            {
                                "id": "root_col",
                                "component": {
                                    "Column": {
                                        "children": {
                                            "explicitList": ["title", "card_form"]
                                        }
                                    }
                                }
                            },
                            {
                                "id": "title",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": f"CSV Column Schema Mapping"
                                        },
                                        "usageHint": "h3"
                                    }
                                }
                            },
                            {
                                "id": "card_form",
                                "component": {
                                    "Card": {
                                        "child": "form_col"
                                    }
                                }
                            },
                            {
                                "id": "form_col",
                                "component": {
                                    "Column": {
                                        "children": {
                                            "explicitList": [
                                                "lbl_state", "sel_state",
                                                "lbl_revenue", "sel_revenue",
                                                "lbl_offering", "sel_offering",
                                                "btn_confirm"
                                            ]
                                        }
                                    }
                                }
                            },
                            {
                                "id": "lbl_state",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "State Column (e.g. California, Texas)"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "sel_state",
                                "component": {
                                    "MultipleChoice": {
                                        "options": options,
                                        "selections": {
                                            "path": "selected_state_col"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "lbl_revenue",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Revenue Column (e.g. 150000)"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "sel_revenue",
                                "component": {
                                    "MultipleChoice": {
                                        "options": options,
                                        "selections": {
                                            "path": "selected_revenue_col"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "lbl_offering",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Product/Service Line Column (e.g. Consulting)"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "sel_offering",
                                "component": {
                                    "MultipleChoice": {
                                        "options": options,
                                        "selections": {
                                            "path": "selected_offering_col"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_lbl",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Confirm Schema"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_confirm",
                                "component": {
                                    "Button": {
                                        "child": "btn_lbl",
                                        "primary": True,
                                        "action": {
                                            "name": "submit",
                                            "context": [
                                                {
                                                    "key": "message",
                                                    "value": {
                                                        "literalString": "Schema Mapping Confirmed!"
                                                    }
                                                },
                                                {
                                                    "key": "action",
                                                    "value": {
                                                        "literalString": "confirmSchema"
                                                    }
                                                },
                                                {
                                                    "key": "state_col",
                                                    "value": {
                                                        "path": "selected_state_col"
                                                    }
                                                },
                                                {
                                                    "key": "revenue_col",
                                                    "value": {
                                                        "path": "selected_revenue_col"
                                                    }
                                                },
                                                {
                                                    "key": "offering_col",
                                                    "value": {
                                                        "path": "selected_offering_col"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        json_str = json.dumps(a2ui_payload)
        if tool_context:
            tool_context.state["a2ui_json"] = json_str
            
        return f"---a2ui_JSON---\n{json_str}"
        
    except Exception as e:
        logger.error(f"Error generating schema form: {e}")
        return json.dumps({"status": "error", "message": str(e)})


def generate_chart_selector_ui(tool_context: ToolContext = None) -> str:
    """Generates the A2UI message payload containing chart selection buttons."""
    try:
        import time
        surface_id = f"chart_selector_{int(time.time())}"

        a2ui_payload = {
            "a2ui_messages": [
                {
                    "beginRendering": {
                        "surfaceId": surface_id,
                        "root": "chart_selector_container"
                    }
                },
                {
                    "surfaceUpdate": {
                        "surfaceId": surface_id,
                        "components": [
                            {
                                "id": "chart_selector_container",
                                "component": {
                                    "Column": {
                                        "children": {
                                            "explicitList": ["title", "subtitle", "cards_row"]
                                        }
                                    }
                                }
                            },
                            {
                                "id": "title",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Select Visualization Type"
                                        },
                                        "usageHint": "h3"
                                    }
                                }
                            },
                            {
                                "id": "subtitle",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Choose how you want to visualize your company's performance data."
                                        }
                                    }
                                }
                            },
                            {
                                "id": "cards_row",
                                "component": {
                                    "Row": {
                                        "children": {
                                            "explicitList": ["btn_pie", "btn_bar", "btn_grouped_bar"]
                                        },
                                        "gap": "15px"
                                    }
                                }
                            },
                            {
                                "id": "btn_lbl_pie",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Pie Chart"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_pie",
                                "component": {
                                    "Button": {
                                        "child": "btn_lbl_pie",
                                        "primary": True,
                                        "action": {
                                            "name": "submit",
                                            "context": [
                                                {
                                                    "key": "message",
                                                    "value": {
                                                        "literalString": "Show the Pie Chart."
                                                    }
                                                },
                                                {
                                                    "key": "action",
                                                    "value": {
                                                        "literalString": "changeChartType"
                                                    }
                                                },
                                                {
                                                    "key": "chart_type",
                                                    "value": {
                                                        "literalString": "pie"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_lbl_bar",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Bar Chart"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_bar",
                                "component": {
                                    "Button": {
                                        "child": "btn_lbl_bar",
                                        "primary": True,
                                        "action": {
                                            "name": "submit",
                                            "context": [
                                                {
                                                    "key": "message",
                                                    "value": {
                                                        "literalString": "Show the Bar Chart."
                                                    }
                                                },
                                                {
                                                    "key": "action",
                                                    "value": {
                                                        "literalString": "changeChartType"
                                                    }
                                                },
                                                {
                                                    "key": "chart_type",
                                                    "value": {
                                                        "literalString": "bar"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_lbl_grouped_bar",
                                "component": {
                                    "Text": {
                                        "text": {
                                            "literalString": "Service Breakdown"
                                        }
                                    }
                                }
                            },
                            {
                                "id": "btn_grouped_bar",
                                "component": {
                                    "Button": {
                                        "child": "btn_lbl_grouped_bar",
                                        "primary": True,
                                        "action": {
                                            "name": "submit",
                                            "context": [
                                                {
                                                    "key": "message",
                                                    "value": {
                                                        "literalString": "Show the Service Breakdown Chart."
                                                    }
                                                },
                                                {
                                                    "key": "action",
                                                    "value": {
                                                        "literalString": "changeChartType"
                                                    }
                                                },
                                                {
                                                    "key": "chart_type",
                                                    "value": {
                                                        "literalString": "grouped_bar"
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
        json_str = json.dumps(a2ui_payload)
        if tool_context:
            tool_context.state["a2ui_json"] = json_str
        return f"---a2ui_JSON---\n{json_str}"
    except Exception as e:
        logger.error(f"Error generating chart selector UI: {e}")
        return json.dumps({"status": "error", "message": str(e)})
