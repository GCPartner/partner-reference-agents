"""Apex Capital Institutional Research — Shared Brand Theme & CSS/Bridge Helpers for SEC EDGAR MCP Apps."""

from __future__ import annotations

import os
from typing import Dict

MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"

DEFAULT_PUBLIC_API_BASE_URL = os.environ.get(
    "MCP_PUBLIC_BASE_URL",
    "",
).rstrip("/")

# Mandatory: Lock to the approved Light Mode institutional theme from mcp_apps_ux_design.md
# so hostContext.theme ("dark") from the MCP Host does not override the approved design.
LOCK_DESIGN_THEME = True

APEX_BRAND_THEME: Dict[str, str] = {
    "brand_name": "Apex Capital Institutional Research",
    "default_theme": "light",
    # Light Mode Tokens (:root) — Exact match to mcp_apps_ux_design.md & approved wireframes
    "header_bg": "#0f172a",          # Deep Institutional Navy top bar & inset control banner
    "header_text": "#f8fafc",        # Crisp Alabaster header text
    "bg_canvas": "#f1f5f9",          # Slate 100 outer workbench canvas background
    "bg_surface": "#ffffff",         # Pure White card, table, and chart surface
    "bg_surface_alt": "#f8fafc",     # Slate 50 table header rows & subtle hover/zebra
    "bg_median_row": "#e2e8f0",      # Slate 200 peer median summary row background
    "border_color": "#cbd5e1",       # Slate 300 1px crisp structural hairlines
    "border_subtle": "#e2e8f0",      # Slate 200 subtle row divider
    "text_primary": "#0f172a",       # Deep Institutional Navy primary figures & headings
    "text_muted": "#475569",         # Slate 600 subtitles, axis labels, XBRL tags
    "navy_bar": "#0f172a",           # Deep Institutional Navy for Revenue chart bars
    "primary_color": "#1e3a8a",      # Royal Institutional Navy for active tab underline & primary actions
    "primary_light": "#dbeafe",      # Navy tint for active pills/badges
    "emerald_color": "#059669",      # Financial Emerald for Gross Profit / Op Income bars & positive growth
    "emerald_dark": "#047857",       # Deep Financial Emerald for Operating Income bar series
    "emerald_bg": "#d1fae5",         # Soft Emerald badge background
    "crimson_color": "#dc2626",      # Drawdown Crimson for negative deltas & risk alerts
    "crimson_bg": "#fee2e2",         # Soft Crimson badge background
    "gold_accent": "#d97706",        # Slate Gold for Net Income bars, FCF, thermometer & gold CTA buttons
    "gold_button_bg": "#d4a017",     # Solid Slate Gold button fill (Ask AI buttons in wireframe)
    "gold_bg": "#fef3c7",            # Soft Gold badge & note callout background
    # Dark Mode Tokens ([data-theme="dark"] — only activated if user clicks manual toggle)
    "dark_header_bg": "#020617",
    "dark_header_text": "#f8fafc",
    "dark_bg_canvas": "#090d16",
    "dark_bg_surface": "#0f172a",
    "dark_bg_surface_alt": "#1e293b",
    "dark_bg_median_row": "#1e293b",
    "dark_border_color": "#334155",
    "dark_border_subtle": "#1e293b",
    "dark_text_primary": "#f8fafc",
    "dark_text_muted": "#94a3b8",
    "dark_navy_bar": "#3b82f6",
    "dark_primary_color": "#3b82f6",
    "dark_primary_light": "#172554",
    "dark_emerald_color": "#10b981",
    "dark_emerald_dark": "#059669",
    "dark_emerald_bg": "rgba(16, 185, 129, 0.16)",
    "dark_crimson_color": "#f87171",
    "dark_crimson_bg": "rgba(248, 113, 113, 0.16)",
    "dark_gold_accent": "#fbbf24",
    "dark_gold_button_bg": "#d97706",
    "dark_gold_bg": "rgba(251, 191, 36, 0.16)",
    # Typography & Corner Radius
    "font_sans": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "font_mono": "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    "radius_sm": "6px",
    "radius_md": "6px",
}


def build_shared_css(theme: Dict[str, str]) -> str:
    """Returns the unified Apex Capital Institutional Research CSS stylesheet compliant with mcp_apps_ux_design.md."""
    return f"""
    :root {{
      --header-bg: {theme["header_bg"]};
      --header-text: {theme["header_text"]};
      --bg: {theme["bg_canvas"]};
      --surface: {theme["bg_surface"]};
      --surface-alt: {theme["bg_surface_alt"]};
      --surface-median: {theme["bg_median_row"]};
      --border: {theme["border_color"]};
      --border-subtle: {theme["border_subtle"]};
      --text: {theme["text_primary"]};
      --text-muted: {theme["text_muted"]};
      --navy-bar: {theme["navy_bar"]};
      --primary: {theme["primary_color"]};
      --primary-light: {theme["primary_light"]};
      --emerald: {theme["emerald_color"]};
      --emerald-dark: {theme["emerald_dark"]};
      --emerald-bg: {theme["emerald_bg"]};
      --crimson: {theme["crimson_color"]};
      --crimson-bg: {theme["crimson_bg"]};
      --gold: {theme["gold_accent"]};
      --gold-btn: {theme["gold_button_bg"]};
      --gold-bg: {theme["gold_bg"]};
      --font-sans: {theme["font_sans"]};
      --font-mono: {theme["font_mono"]};
      --radius-sm: {theme["radius_sm"]};
      --radius-md: {theme["radius_md"]};
    }}
    [data-theme="dark"] {{
      --header-bg: {theme["dark_header_bg"]};
      --header-text: {theme["dark_header_text"]};
      --bg: {theme["dark_bg_canvas"]};
      --surface: {theme["dark_bg_surface"]};
      --surface-alt: {theme["dark_bg_surface_alt"]};
      --surface-median: {theme["dark_bg_median_row"]};
      --border: {theme["dark_border_color"]};
      --border-subtle: {theme["dark_border_subtle"]};
      --text: {theme["dark_text_primary"]};
      --text-muted: {theme["dark_text_muted"]};
      --navy-bar: {theme["dark_navy_bar"]};
      --primary: {theme["dark_primary_color"]};
      --primary-light: {theme["dark_primary_light"]};
      --emerald: {theme["dark_emerald_color"]};
      --emerald-dark: {theme["dark_emerald_dark"]};
      --emerald-bg: {theme["dark_emerald_bg"]};
      --crimson: {theme["dark_crimson_color"]};
      --crimson-bg: {theme["dark_crimson_bg"]};
      --gold: {theme["dark_gold_accent"]};
      --gold-btn: {theme["dark_gold_button_bg"]};
      --gold-bg: {theme["dark_gold_bg"]};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      font-size: 12.5px;
      line-height: 1.45;
      padding: 0;
    }}
    /* Top Deep Institutional Navy Bar (#0f172a) */
    .top-banner {{
      background: var(--header-bg);
      color: var(--header-text);
      padding: 10px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    }}
    .brand-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      font-size: 13.5px;
      letter-spacing: 0.02em;
      color: var(--header-text);
    }}
    .brand-logo {{
      width: 24px;
      height: 24px;
      border-radius: 4px;
      background: var(--primary);
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-sans);
      font-weight: 800;
      font-size: 13px;
      border: 1px solid rgba(255, 255, 255, 0.28);
    }}
    /* Inset Rounded Deep Institutional Navy Control Banner (#0f172a) matching Wireframes */
    .control-strip {{
      background: var(--header-bg);
      color: var(--header-text);
      margin: 12px 16px 0 16px;
      padding: 12px 16px;
      border-radius: var(--radius-md);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      box-shadow: 0 2px 6px rgba(15, 23, 42, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    .entity-identity {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .entity-avatar {{
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: #ffffff;
      color: var(--header-bg);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-family: var(--font-mono);
      font-weight: 800;
      font-size: 11px;
      border: 2px solid var(--emerald);
      flex-shrink: 0;
    }}
    .entity-name {{
      font-size: 14px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: 0.02em;
      line-height: 1.2;
    }}
    .entity-sub {{
      font-size: 11px;
      color: #cbd5e1;
      font-family: var(--font-mono);
      margin-top: 2px;
    }}
    .control-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .control-field {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .control-label {{
      font-size: 10.5px;
      color: #cbd5e1;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .input, .select {{
      padding: 6px 10px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: #ffffff;
      color: #0f172a;
      font-size: 12px;
      font-family: var(--font-sans);
      height: 32px;
    }}
    .input-mono {{
      font-family: var(--font-mono);
      font-weight: 700;
    }}
    #tickerInput, .input-uppercase {{
      text-transform: uppercase;
    }}
    .btn {{
      padding: 6px 12px;
      height: 32px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      font-size: 11.5px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      transition: all 0.12s ease;
      white-space: nowrap;
    }}
    .btn:hover {{
      filter: brightness(0.95);
    }}
    .btn-primary {{
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }}
    .btn-neutral {{
      background: #cbd5e1;
      color: #0f172a;
      border-color: #94a3b8;
      font-weight: 700;
    }}
    /* Solid Slate Gold CTA Button matching Wireframe "Ask AI" buttons */
    .btn-gold {{
      background: var(--gold-btn);
      color: #0f172a;
      border-color: var(--gold);
      font-weight: 700;
    }}
    .btn-icon-header {{
      background: rgba(255, 255, 255, 0.1);
      color: #f8fafc;
      border: 1px solid rgba(255, 255, 255, 0.2);
      height: 28px;
      padding: 3px 9px;
      font-size: 11px;
    }}
    .workspace {{
      padding: 12px 16px;
    }}
    /* 6-Card Centered KPI Strip matching Wireframe */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    .kpi-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 10px;
      text-align: center;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }}
    .kpi-label {{
      font-size: 11.5px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 4px;
    }}
    .kpi-val {{
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-size: 21px;
      font-weight: 800;
      color: var(--text);
      letter-spacing: -0.02em;
    }}
    .kpi-sub {{
      margin-top: 4px;
      font-size: 11px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      flex-wrap: wrap;
    }}
    .text-emerald {{ color: var(--emerald); font-weight: 700; font-family: var(--font-mono); }}
    .text-crimson {{ color: var(--crimson); font-weight: 700; font-family: var(--font-mono); }}
    .text-gold {{ color: var(--gold); font-weight: 700; font-family: var(--font-mono); }}
    .text-muted-mono {{ color: var(--text-muted); font-family: var(--font-mono); font-size: 10.5px; }}
    /* Badges & Solid Institutional Pills */
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 2px 7px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      font-size: 10.5px;
      font-weight: 700;
    }}
    .badge-emerald {{ background: var(--emerald-bg); color: var(--emerald); }}
    .badge-crimson {{ background: var(--crimson-bg); color: var(--crimson); }}
    .badge-gold {{ background: var(--gold-bg); color: var(--gold); }}
    .badge-navy {{ background: var(--primary-light); color: var(--primary); }}
    /* Solid Emerald & Crimson Pills matching Peer Comparator Wireframe (e.g. 75.0%, 147.2%, 37.1%) */
    .badge-emerald-solid {{
      background: var(--emerald);
      color: #ffffff;
      padding: 2px 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 11.5px;
    }}
    .badge-crimson-solid {{
      background: var(--crimson);
      color: #ffffff;
      padding: 2px 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 11.5px;
    }}
    .xbrl-pill {{
      display: inline-block;
      background: #f1f5f9;
      border: 1px solid var(--border);
      color: #334155;
      font-family: var(--font-mono);
      font-size: 10.5px;
      padding: 1.5px 7px;
      border-radius: 4px;
      white-space: nowrap;
    }}
    [data-theme="dark"] .xbrl-pill {{
      background: #1e293b;
      color: #cbd5e1;
    }}
    /* Clean Underline Navigation Tabs matching Dossier Wireframe */
    .tabs-bar {{
      display: flex;
      gap: 18px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 12px;
      flex-wrap: wrap;
      padding: 0 4px;
    }}
    .tab-btn {{
      padding: 7px 4px 9px 4px;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--text-muted);
      background: transparent;
      border: none;
      border-bottom: 2.5px solid transparent;
      cursor: pointer;
      transition: color 0.12s ease;
    }}
    .tab-btn:hover {{
      color: var(--text);
    }}
    .tab-btn.active {{
      color: var(--text);
      font-weight: 700;
      border-bottom-color: var(--primary);
    }}
    /* Crisp White Surface Panels (#ffffff) */
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 13px 16px;
      margin-bottom: 12px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }}
    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
      padding-bottom: 7px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    .panel-title {{
      font-size: 12.5px;
      font-weight: 700;
      color: var(--text);
      letter-spacing: 0.01em;
    }}
    .panel-subtitle {{
      font-size: 11px;
      font-weight: 500;
      color: var(--text-muted);
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table.fin-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    table.fin-table th {{
      background: var(--surface-alt);
      color: var(--text);
      font-weight: 700;
      font-size: 11px;
      padding: 8px 10px;
      border-top: 1px solid var(--border-subtle);
      border-bottom: 1px solid var(--border);
      text-align: right;
      white-space: nowrap;
    }}
    table.fin-table th:first-child {{
      text-align: left;
    }}
    table.fin-table td {{
      padding: 7.5px 10px;
      border-bottom: 1px solid var(--border-subtle);
      font-family: var(--font-mono);
      font-variant-numeric: tabular-nums;
      text-align: right;
      white-space: nowrap;
      color: var(--text);
    }}
    table.fin-table td:first-child {{
      font-family: var(--font-mono);
      font-weight: 600;
      text-align: left;
    }}
    table.fin-table tr:hover {{
      background: var(--surface-alt);
    }}
    table.fin-table tr.row-highlight {{
      font-weight: 700;
      background: rgba(241, 245, 249, 0.55);
    }}
    table.fin-table tr.median-row {{
      background: var(--surface-median) !important;
      font-weight: 800;
    }}
    .pill-group {{
      display: inline-flex;
      gap: 4px;
      flex-wrap: wrap;
    }}
    .pill {{
      padding: 4px 10px;
      border-radius: 4px;
      border: 1px solid var(--border);
      background: var(--surface-alt);
      color: var(--text-muted);
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
    }}
    .pill.active {{
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
    }}
    .header-pill {{
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.22);
      background: rgba(255, 255, 255, 0.08);
      color: #cbd5e1;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
    }}
    .header-pill.active {{
      background: var(--primary);
      color: #ffffff;
      border-color: #60a5fa;
    }}
    .note-banner {{
      margin-top: 10px;
      padding: 8px 11px;
      border-radius: var(--radius-sm);
      background: var(--gold-bg);
      border-left: 3px solid var(--gold);
      font-size: 11.5px;
      color: var(--text);
    }}
    .footer-bar {{
      padding: 10px 16px;
      border-top: 1px solid var(--border);
      background: var(--surface);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 11.5px;
      font-weight: 600;
      color: var(--text);
    }}
    a.ext-link {{
      color: var(--text);
      text-decoration: none;
      font-weight: 600;
      font-family: var(--font-sans);
    }}
    a.ext-link:hover {{
      color: var(--primary);
      text-decoration: underline;
    }}
    """
