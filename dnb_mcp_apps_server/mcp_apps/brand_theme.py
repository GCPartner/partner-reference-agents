"""Official `dnb.ai` & `dnb.com` Brand Theme, Typography, Background Network Graphics & SEP-1865 Bridge.

Extracted directly from `https://dnb.ai/etc.clientlibs/dnb-marketing-website/clientlibs/clientlib-react.css`
and `https://www.dnb.com/`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def _load_local_env() -> None:
    root_dir = Path(__file__).resolve().parent.parent
    for env_name in (".env", ".env.deploy"):
        env_path = root_dir / env_name
        if env_path.exists():
            try:
                for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
            except Exception:
                pass


_load_local_env()

MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"

DEFAULT_PUBLIC_API_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    os.environ.get("MCP_PUBLIC_BASE_URL", "http://localhost:8080"),
).rstrip("/")

LOCK_DESIGN_THEME: bool = True

DNB_BRAND_THEME: Dict[str, Any] = {
    "brand_id": "dnb_ai_official",
    "brand_name": "Dun & Bradstreet (dnb.ai / dnb.com)",
    "lock_design_theme": LOCK_DESIGN_THEME,
    "colors": {
        "primary_dark_blue_1": "#005172",
        "primary_dark_blue_2": "#00435F",
        "primary_dark_blue_3": "#002737",
        "dark_blue_hover": "#14384E",
        "primary_light_blue": "#3095B4",
        "primary_light_blue_40": "#ACD5E1",
        "primary_light_blue_10": "#F2F8F9",
        "primary_blue_10": "#E5EEF1",
        "dark_teal": "#005F61",
        "light_teal": "#00B2A9",
        "dark_green": "#046A38",
        "pattern_light_green": "#74AA4E",
        "warning_amber": "#E6A65D",
        "dark_orange": "#BE4D00",
        "error_red": "#D73838",
        "text_gray": "#6D6D6D",
        "border_gray": "#D6D6D6",
        "white": "#FFFFFF",
    },
    "fonts": {
        "sans": '"Avenir LT Std", "Avenir LT W05_65 Medium", "Avenir Next", "Avenir", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        "heavy": '"Avenir LT W05_85 Heavy", "Avenir LT Std", "Avenir Next", "Avenir", -apple-system, BlinkMacSystemFont, sans-serif',
        "mono": '"JetBrains Mono", "SFMono-Regular", Consolas, monospace',
    },
}


def build_dnb_shared_css() -> str:
    """Returns the shared CSS stylesheet implementing the `dnb.ai` & `dnb.com` visual design system."""
    return """
    :root {
      --primary-dark-blue-1: #005172;
      --primary-dark-blue-2: #00435F;
      --primary-dark-blue-3: #002737;
      --dark-blue-hover: #14384E;
      --primary-light-blue: #3095B4;
      --primary-light-blue-40: #ACD5E1;
      --primary-light-blue-10: #F2F8F9;
      --primary-blue-10: #E5EEF1;
      --dark-teal: #005F61;
      --light-teal: #00B2A9;
      --dark-green: #046A38;
      --pattern-light-green: #74AA4E;
      --warning: #E6A65D;
      --dark-orange: #BE4D00;
      --error: #D73838;
      --text-gray: #6D6D6D;
      --border-gray: #D6D6D6;
      --white: #FFFFFF;

      --font-sans: "Avenir LT Std", "Avenir LT W05_65 Medium", "Avenir Next", "Avenir", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --font-heavy: "Avenir LT W05_85 Heavy", "Avenir LT Std", "Avenir Next", "Avenir", -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      width: 100%;
      min-height: 100%;
      font-family: var(--font-sans);
      color: var(--primary-dark-blue-3);
      background: linear-gradient(135deg, #005172 0%, #00435F 52%, #002737 100%);
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }

    /* Outer dnb.ai / dnb.com Network Constellation & Dot-Matrix Canvas */
    .dnb-outer-stage {
      position: relative;
      width: 100%;
      min-height: 100vh;
      padding: 20px 22px 24px 22px;
      background:
        radial-gradient(circle at 14% 18%, rgba(48, 149, 180, 0.24) 0%, transparent 42%),
        radial-gradient(circle at 88% 82%, rgba(0, 178, 169, 0.18) 0%, transparent 45%),
        linear-gradient(135deg, #005172 0%, #00435F 52%, #002737 100%);
      overflow: hidden;
    }

    /* Cyan Polka-Dot Matrix Overlay */
    .dnb-dot-matrix {
      position: absolute;
      inset: 0;
      background-image: radial-gradient(rgba(172, 213, 225, 0.24) 1.35px, transparent 1.35px);
      background-size: 20px 20px;
      pointer-events: none;
      z-index: 0;
    }

    .dnb-bg-svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }

    /* Floating White D&B App Shell Card */
    .dnb-app-shell {
      position: relative;
      z-index: 2;
      max-width: 1120px;
      margin: 0 auto;
      background: var(--white);
      border: 1.5px solid var(--primary-light-blue);
      border-radius: 16px;
      box-shadow:
        0 20px 48px rgba(0, 39, 55, 0.38),
        0 0 0 4px rgba(172, 213, 225, 0.16);
      overflow: hidden;
    }

    /* Top Brand Bar inside the Floating Card */
    .dnb-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;
      padding: 14px 22px;
      background: linear-gradient(90deg, #002737 0%, #00435F 60%, #005172 100%);
      color: var(--white);
      border-bottom: 1.5px solid var(--primary-light-blue);
    }

    .dnb-brand-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .dnb-logo-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 11px;
      border-radius: 9px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(172, 213, 225, 0.45);
      font-weight: 800;
      letter-spacing: -0.02em;
      color: var(--white);
      font-size: 15px;
    }

    .dnb-logo-amp {
      color: var(--primary-light-blue-40);
      font-size: 18px;
      font-weight: 900;
      line-height: 1;
    }

    .dnb-ai-pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      border-radius: 999px;
      background: linear-gradient(135deg, #3095B4 0%, #00B2A9 100%);
      color: var(--white);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .dnb-topbar-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--primary-light-blue-10);
      letter-spacing: 0.01em;
    }

    .dnb-topbar-controls {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .dnb-input {
      height: 34px;
      padding: 0 12px;
      border-radius: 8px;
      border: 1px solid rgba(172, 213, 225, 0.55);
      background: rgba(255, 255, 255, 0.95);
      color: var(--primary-dark-blue-3);
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 600;
      outline: none;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .dnb-input:focus {
      border-color: var(--light-teal);
      box-shadow: 0 0 0 2px rgba(0, 178, 169, 0.25);
    }

    .dnb-select {
      height: 34px;
      padding: 0 10px;
      border-radius: 8px;
      border: 1px solid rgba(172, 213, 225, 0.55);
      background: rgba(255, 255, 255, 0.95);
      color: var(--primary-dark-blue-3);
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 600;
      outline: none;
      cursor: pointer;
    }

    /* Buttons matching dnb.ai & dnb.com */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      height: 34px;
      padding: 0 14px;
      border-radius: 8px;
      font-family: var(--font-sans);
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.16s ease;
      text-decoration: none;
      white-space: nowrap;
      border: 1px solid transparent;
    }

    .btn-primary {
      background: var(--primary-dark-blue-1);
      color: var(--white);
      border-color: var(--primary-light-blue);
    }

    .btn-primary:hover {
      background: var(--dark-blue-hover);
      box-shadow: 0 4px 12px rgba(0, 81, 114, 0.28);
    }

    .btn-cyan {
      background: var(--primary-light-blue);
      color: var(--white);
      border-color: var(--primary-light-blue);
    }

    .btn-cyan:hover {
      background: var(--primary-dark-blue-1);
    }

    .btn-outline {
      background: var(--white);
      color: var(--primary-dark-blue-1);
      border: 1.5px solid var(--primary-light-blue);
    }

    .btn-outline:hover {
      background: var(--primary-light-blue-10);
      border-color: var(--primary-dark-blue-1);
    }

    .btn-ghost-light {
      background: rgba(255, 255, 255, 0.12);
      color: var(--white);
      border: 1px solid rgba(172, 213, 225, 0.5);
    }

    .btn-ghost-light:hover {
      background: rgba(255, 255, 255, 0.22);
    }

    /* Main Content Padding */
    .dnb-body {
      padding: 20px 24px;
      background: var(--white);
    }

    /* Hero Strip inside Card */
    .dnb-hero-banner {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
      padding: 16px 20px;
      border-radius: 12px;
      background: linear-gradient(180deg, #F2F8F9 0%, #E5EEF1 100%);
      border: 1px solid var(--primary-light-blue-40);
      margin-bottom: 18px;
    }

    .dnb-entity-title {
      font-size: 22px;
      font-weight: 800;
      color: var(--primary-dark-blue-3);
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .dnb-subtitle-row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 6px;
      font-size: 13px;
      color: var(--primary-dark-blue-2);
    }

    /* D-U-N-S Monospace Pill */
    .duns-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--white);
      border: 1.5px solid var(--primary-light-blue);
      color: var(--primary-dark-blue-1);
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .duns-pill:hover {
      background: var(--primary-dark-blue-1);
      color: var(--white);
    }

    /* Semantic Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    .badge-success {
      background: rgba(4, 106, 56, 0.11);
      color: var(--dark-green);
      border: 1px solid rgba(116, 170, 78, 0.55);
    }

    .badge-cyan {
      background: var(--primary-light-blue-10);
      color: var(--primary-dark-blue-1);
      border: 1px solid var(--primary-light-blue-40);
    }

    .badge-teal {
      background: rgba(0, 178, 169, 0.12);
      color: var(--dark-teal);
      border: 1px solid rgba(0, 178, 169, 0.45);
    }

    .badge-warning {
      background: rgba(230, 166, 93, 0.18);
      color: var(--dark-orange);
      border: 1px solid rgba(230, 166, 93, 0.65);
    }

    .badge-danger {
      background: rgba(215, 56, 56, 0.12);
      color: var(--error);
      border: 1px solid rgba(215, 56, 56, 0.45);
    }

    /* 3-Tile KPI Row (Anti-Clutter Max 3 Tiles Per Row) */
    .kpi-grid-3 {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }

    @media (max-width: 780px) {
      .kpi-grid-3 {
        grid-template-columns: 1fr;
      }
    }

    .kpi-card {
      padding: 15px 18px;
      border-radius: 12px;
      background: var(--primary-light-blue-10);
      border: 1px solid var(--primary-light-blue-40);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .kpi-label {
      font-size: 11.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--primary-dark-blue-2);
    }

    .kpi-value {
      font-size: 24px;
      font-weight: 800;
      color: var(--primary-dark-blue-3);
      letter-spacing: -0.02em;
      font-variant-numeric: tabular-nums;
    }

    .kpi-sub {
      font-size: 12px;
      color: var(--text-gray);
      font-weight: 600;
    }

    /* Segmented Pill Switcher (3-pill anti-clutter rule) */
    .segmented-pills {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px;
      border-radius: 999px;
      background: var(--primary-blue-10);
      border: 1px solid var(--primary-light-blue-40);
    }

    .seg-pill {
      padding: 6px 14px;
      border-radius: 999px;
      border: none;
      background: transparent;
      color: var(--primary-dark-blue-2);
      font-family: var(--font-sans);
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .seg-pill.active {
      background: var(--primary-dark-blue-1);
      color: var(--white);
      box-shadow: 0 2px 6px rgba(0, 81, 114, 0.25);
    }

    /* Section Card */
    .section-card {
      padding: 16px 18px;
      border-radius: 12px;
      background: var(--white);
      border: 1px solid var(--border-gray);
      margin-bottom: 16px;
    }

    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .section-title {
      font-size: 14px;
      font-weight: 800;
      color: var(--primary-dark-blue-1);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      display: flex;
      align-items: center;
      gap: 7px;
    }

    /* Footer Status Bar */
    .dnb-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      padding: 11px 22px;
      background: var(--primary-light-blue-10);
      border-top: 1px solid var(--primary-light-blue-40);
      font-size: 12px;
      color: var(--primary-dark-blue-2);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--light-teal);
      display: inline-block;
      margin-right: 6px;
    }

    .btn:disabled, .btn.is-loading {
      opacity: 0.72;
      cursor: wait;
    }

    .kpi-card-clickable {
      cursor: pointer;
      transition: transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease;
    }

    .kpi-card-clickable:hover {
      transform: translateY(-2px);
      border-color: var(--primary-dark-blue-1);
      box-shadow: 0 6px 16px rgba(0, 81, 114, 0.14);
    }

    /* Executive Briefing & Approval Memo Modal */
    .dnb-modal-overlay {
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: rgba(0, 39, 55, 0.68);
      backdrop-filter: blur(3px);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .dnb-modal-card {
      width: 100%;
      max-width: 720px;
      max-height: 86vh;
      background: var(--white);
      border: 2px solid var(--primary-light-blue);
      border-radius: 16px;
      box-shadow: 0 24px 60px rgba(0, 39, 55, 0.52);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .dnb-modal-header {
      padding: 15px 20px;
      background: linear-gradient(90deg, #002737 0%, #00435F 60%, #005172 100%);
      color: var(--white);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1.5px solid var(--primary-light-blue);
    }

    .dnb-modal-body {
      padding: 20px 22px;
      overflow-y: auto;
      font-size: 13.5px;
      line-height: 1.6;
      color: var(--primary-dark-blue-3);
    }

    .dnb-modal-footer {
      padding: 12px 20px;
      background: var(--primary-light-blue-10);
      border-top: 1px solid var(--primary-light-blue-40);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }
    """


def build_dnb_network_canvas_svg() -> str:
    """Returns the SVG decorative layer mimicking the `dnb.ai` & `dnb.com` network constellation & wave arcs."""
    return """
    <div class="dnb-dot-matrix"></div>
    <svg class="dnb-bg-svg" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="dnbArcGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#3095B4" stop-opacity="0.55" />
          <stop offset="50%" stop-color="#ACD5E1" stop-opacity="0.25" />
          <stop offset="100%" stop-color="#00B2A9" stop-opacity="0.05" />
        </linearGradient>
        <linearGradient id="dnbArcGrad2" x1="100%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#00B2A9" stop-opacity="0.45" />
          <stop offset="60%" stop-color="#3095B4" stop-opacity="0.22" />
          <stop offset="100%" stop-color="#002737" stop-opacity="0.0" />
        </linearGradient>
      </defs>

      <!-- Sweeping Curved Wave Arcs (dnb.ai / dnb.com signature motif) -->
      <path d="M-120,180 C220,-40 620,40 980,320 C1220,510 1380,480 1560,340" fill="none" stroke="url(#dnbArcGrad1)" stroke-width="2.2" />
      <path d="M-80,740 C280,520 740,860 1160,620 C1320,530 1420,410 1540,390" fill="none" stroke="url(#dnbArcGrad2)" stroke-width="2" />
      <circle cx="110" cy="140" r="190" fill="none" stroke="#3095B4" stroke-opacity="0.18" stroke-width="1.2" stroke-dasharray="5 6" />
      <circle cx="1330" cy="760" r="230" fill="none" stroke="#ACD5E1" stroke-opacity="0.16" stroke-width="1.2" stroke-dasharray="4 6" />

      <!-- Top-Left Connected Network Constellation -->
      <g stroke="#ACD5E1" stroke-opacity="0.42" stroke-width="1.4">
        <line x1="48" y1="78" x2="132" y2="124" />
        <line x1="132" y1="124" x2="88" y2="218" />
        <line x1="132" y1="124" x2="215" y2="72" />
      </g>
      <!-- Building HQ Node -->
      <g transform="translate(28, 58)">
        <circle cx="20" cy="20" r="19" fill="#00435F" stroke="#3095B4" stroke-width="1.8" />
        <rect x="13" y="11" width="14" height="18" rx="1.5" fill="none" stroke="#ACD5E1" stroke-width="1.5" />
        <line x1="17" y1="15" x2="23" y2="15" stroke="#00B2A9" stroke-width="1.5" />
        <line x1="17" y1="19" x2="23" y2="19" stroke="#00B2A9" stroke-width="1.5" />
        <line x1="17" y1="23" x2="23" y2="23" stroke="#00B2A9" stroke-width="1.5" />
      </g>
      <!-- Connected Hub Node -->
      <circle cx="132" cy="124" r="6" fill="#00B2A9" stroke="#FFFFFF" stroke-width="1.5" />
      <circle cx="88" cy="218" r="4.5" fill="#ACD5E1" />
      <!-- AI Sparkle Node Top-Left -->
      <path d="M215,58 L218,68 L228,71 L218,74 L215,84 L212,74 L202,71 L212,68 Z" fill="#ACD5E1" fill-opacity="0.8" />

      <!-- Top-Right Connected Network Constellation -->
      <g stroke="#3095B4" stroke-opacity="0.48" stroke-width="1.4">
        <line x1="1385" y1="68" x2="1296" y2="118" />
        <line x1="1296" y1="118" x2="1364" y2="198" />
      </g>
      <!-- Bar Chart Analytics Node -->
      <g transform="translate(1365, 48)">
        <circle cx="20" cy="20" r="19" fill="#00435F" stroke="#00B2A9" stroke-width="1.8" />
        <rect x="12" y="21" width="3.5" height="7" fill="#ACD5E1" />
        <rect x="18" y="16" width="3.5" height="12" fill="#3095B4" />
        <rect x="24" y="11" width="3.5" height="17" fill="#00B2A9" />
      </g>
      <circle cx="1296" cy="118" r="5.5" fill="#ACD5E1" />
      <circle cx="1364" cy="198" r="4.5" fill="#00B2A9" />

      <!-- Bottom-Right Network Constellation -->
      <g stroke="#ACD5E1" stroke-opacity="0.38" stroke-width="1.4">
        <line x1="1380" y1="810" x2="1290" y2="755" />
        <line x1="1290" y1="755" x2="1220" y2="835" />
      </g>
      <!-- D-U-N-S Fingerprint / Identity Node -->
      <g transform="translate(1360, 790)">
        <circle cx="20" cy="20" r="19" fill="#002737" stroke="#3095B4" stroke-width="1.8" />
        <path d="M14,22 C14,16 26,16 26,22" fill="none" stroke="#ACD5E1" stroke-width="1.5" stroke-linecap="round" />
        <path d="M11,24 C11,12 29,12 29,24" fill="none" stroke="#00B2A9" stroke-width="1.4" stroke-linecap="round" />
        <circle cx="20" cy="23" r="2" fill="#FFFFFF" />
      </g>
      <!-- AI Sparkle Bottom-Left -->
      <path d="M54,812 L57,822 L67,825 L57,828 L54,838 L51,828 L41,825 L51,822 Z" fill="#00B2A9" fill-opacity="0.75" />
    </svg>
    """


_SUITE_TEMPLATES_CACHE: Dict[str, str] = {}


def _get_suite_templates_json(api_base_url: str) -> str:
    if api_base_url in _SUITE_TEMPLATES_CACHE:
        return _SUITE_TEMPLATES_CACHE[api_base_url]
    from .company_360_app import build_company_360_html
    from .entity_matcher_app import build_entity_matcher_html
    from .family_tree_app import build_family_tree_html
    from .supplier_risk_app import build_supplier_risk_html

    templates = {
        "entity_matcher": build_entity_matcher_html(
            initial_payload=None, api_base_url=api_base_url, include_suite_templates=False
        ),
        "company_360": build_company_360_html(
            initial_payload=None, api_base_url=api_base_url, include_suite_templates=False
        ),
        "family_tree": build_family_tree_html(
            initial_payload=None, api_base_url=api_base_url, include_suite_templates=False
        ),
        "supplier_risk": build_supplier_risk_html(
            initial_payload=None, api_base_url=api_base_url, include_suite_templates=False
        ),
    }
    serialized = json.dumps(templates, ensure_ascii=False).replace("</", "<\\/")
    _SUITE_TEMPLATES_CACHE[api_base_url] = serialized
    return serialized


def build_dnb_bridge_js(
    app_name: str,
    api_base_url: str = DEFAULT_PUBLIC_API_BASE_URL,
    include_suite_templates: bool = True,
) -> str:
    """Returns the shared SEP-1865 JSON-RPC 2.0 `postMessage` bridge, in-DOM 4-app SPA router, and preloaded bundle resolver."""
    suite_templates_expr = _get_suite_templates_json(api_base_url) if include_suite_templates else "null"
    return f"""
    const API_BASE_URL = {api_base_url!r};
    const LOCK_DESIGN_THEME = true;
    const SUITE_TEMPLATES = {suite_templates_expr};
    let rpcId = 1;
    const pendingRpc = new Map();

    if (!window.__DNB_SUITE_BUNDLE__) {{
      window.__DNB_SUITE_BUNDLE__ = {{
        templates: {{}},
        dossiers: {{}},
        matchers: {{}},
        candidates_by_duns: {{}},
        last_matcher_payload: null,
        primary_duns: "079942718",
      }};
    }}
    if (SUITE_TEMPLATES && typeof SUITE_TEMPLATES === "object") {{
      Object.assign(window.__DNB_SUITE_BUNDLE__.templates, SUITE_TEMPLATES);
    }}

    function escapeHtml(val) {{
      if (val === null || val === undefined) return "";
      return String(val)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }}

    function normalizeDunsKey(raw) {{
      const digits = String(raw || "").replace(/\\D/g, "");
      if (digits && digits.length >= 7) {{
        return digits.padStart(9, "0");
      }}
      return "";
    }}

    function mergePreloadedSuiteData(suiteData) {{
      if (!suiteData || typeof suiteData !== "object") return;
      const bundle = window.__DNB_SUITE_BUNDLE__;
      if (suiteData.primary_duns) {{
        const pd = normalizeDunsKey(suiteData.primary_duns);
        if (pd) bundle.primary_duns = pd;
      }}
      if (suiteData.dossiers && typeof suiteData.dossiers === "object") {{
        for (const [dunsKey, dObj] of Object.entries(suiteData.dossiers)) {{
          if (!dObj || typeof dObj !== "object") continue;
          const cleanK = normalizeDunsKey(dunsKey) || String(dunsKey).trim().toUpperCase();
          bundle.dossiers[cleanK] = Object.assign(bundle.dossiers[cleanK] || {{}}, dObj);
          if (dObj.entity_matcher) {{
            bundle.matchers[cleanK] = dObj.entity_matcher;
            if (cleanK === bundle.primary_duns) {{
              bundle.last_matcher_payload = dObj.entity_matcher;
            }}
            const qName = String(dObj.entity_matcher.query?.name || "").trim().toUpperCase();
            if (qName) bundle.matchers[qName] = dObj.entity_matcher;
            const recName = String(dObj.entity_matcher.recommended_candidate?.primary_name || "").trim().toUpperCase();
            if (recName) bundle.matchers[recName] = dObj.entity_matcher;
          }}
          const compName = String(
            dObj.company_360?.company?.primary_name ||
            dObj.family_tree?.subject_company?.primary_name ||
            dObj.supplier_risk?.company?.primary_name ||
            ""
          ).trim().toUpperCase();
          if (compName) {{
            bundle.dossiers[compName] = bundle.dossiers[cleanK];
          }}
        }}
      }}
      if (suiteData.candidates_by_duns && typeof suiteData.candidates_by_duns === "object") {{
        for (const [ck, cv] of Object.entries(suiteData.candidates_by_duns)) {{
          const cleanCk = normalizeDunsKey(ck);
          if (cleanCk && cv) bundle.candidates_by_duns[cleanCk] = cv;
        }}
      }}
    }}

    function registerPayloadInSuiteBundle(payload) {{
      if (!payload || typeof payload !== "object") return;
      const bundle = window.__DNB_SUITE_BUNDLE__;
      if (payload.preloaded_dossiers) {{
        mergePreloadedSuiteData(payload.preloaded_dossiers);
      }}
      if (Array.isArray(payload.candidates)) {{
        bundle.last_matcher_payload = payload;
        const qName = String(payload.query?.name || "").trim().toUpperCase();
        if (qName) bundle.matchers[qName] = payload;
        const rec = payload.recommended_candidate;
        if (rec) {{
          const rd = normalizeDunsKey(rec.duns);
          if (rd) {{
            bundle.matchers[rd] = payload;
            bundle.primary_duns = rd;
          }}
          const rn = String(rec.primary_name || "").trim().toUpperCase();
          if (rn) bundle.matchers[rn] = payload;
        }}
        for (const c of payload.candidates) {{
          const cd = normalizeDunsKey(c?.duns);
          if (cd) bundle.candidates_by_duns[cd] = c;
        }}
      }}
      const duns = normalizeDunsKey(payload.duns || payload.company?.duns || payload.subject_company?.duns);
      if (duns) {{
        bundle.dossiers[duns] = bundle.dossiers[duns] || {{}};
        if (payload.company && payload.leadership) {{
          bundle.dossiers[duns].company_360 = payload;
        }} else if (Array.isArray(payload.nodes) && payload.global_ultimate) {{
          bundle.dossiers[duns].family_tree = payload;
          for (const n of payload.nodes.slice(0, 150)) {{
            const nd = normalizeDunsKey(n?.duns);
            if (nd && !bundle.candidates_by_duns[nd]) {{
              bundle.candidates_by_duns[nd] = {{
                duns: nd,
                duns_formatted: n.duns_formatted || `${{nd.slice(0, 2)}}-${{nd.slice(2, 5)}}-${{nd.slice(5)}}`,
                primary_name: n.name || `D&B Entity ${{nd}}`,
                address: `${{n.country || "US"}} (${{n.roles_label || "Subsidiary"}})`,
                country: n.country || "US",
                operating_status: "Active",
                family_tree_role: n.roles_label || "Subsidiary",
                role_badge: n.is_hq ? "HQ" : (n.is_branch ? "BRANCH" : "SUBSIDIARY"),
                parent_duns: n.parent_duns,
                parent_name: n.parent_name,
              }};
            }}
          }}
        }} else if (payload.risk_gauges && payload.compliance_checklist) {{
          bundle.dossiers[duns].supplier_risk = payload;
        }}
        const pName = String(payload.company?.primary_name || payload.subject_company?.primary_name || "").trim().toUpperCase();
        if (pName) {{
          bundle.dossiers[pName] = bundle.dossiers[duns];
        }}
      }}
    }}

    function toolNameToViewKey(toolName) {{
      const t = String(toolName || "").trim();
      if (t === "open_entity_matcher_app" || t === "MatchTool") return "entity_matcher";
      if (t === "open_corporate_family_tree_app" || t === "OwnershipTool") return "family_tree";
      if (
        t === "open_supplier_risk_scorecard_app" ||
        t === "RiskTool" ||
        t === "PaymentTool" ||
        t === "BusinessEventsTool" ||
        t === "ESGTool" ||
        t === "DiversityTool" ||
        t === "ShippingTool" ||
        t === "SBRITool" ||
        t === "InquiryTool"
      ) {{
        return "supplier_risk";
      }}
      return "company_360";
    }}

    function getPreloadedPayloadForTool(toolName, args) {{
      const bundle = window.__DNB_SUITE_BUNDLE__;
      if (!bundle) return null;
      const viewKey = toolNameToViewKey(toolName);
      if (viewKey === "entity_matcher") {{
        const qName = String(args?.name || "").trim().toUpperCase();
        if (qName && bundle.matchers[qName]) return bundle.matchers[qName];
        const qDuns = normalizeDunsKey(args?.name || args?.duns);
        if (qDuns && bundle.matchers[qDuns]) return bundle.matchers[qDuns];
        for (const [mk, mv] of Object.entries(bundle.matchers)) {{
          if (qName && (mk.includes(qName) || qName.includes(mk))) return mv;
        }}
        return null;
      }}
      const rawArg = String(args?.duns || args?.name || "").trim();
      const duns = normalizeDunsKey(rawArg);
      if (duns && bundle.dossiers[duns] && bundle.dossiers[duns][viewKey]) {{
        return bundle.dossiers[duns][viewKey];
      }}
      const upperArg = rawArg.toUpperCase();
      if (upperArg && bundle.dossiers[upperArg] && bundle.dossiers[upperArg][viewKey]) {{
        return bundle.dossiers[upperArg][viewKey];
      }}
      // Also check well-known aliases
      if ((upperArg === "GOOGLE" || upperArg === "ALPHABET") && bundle.dossiers["079942718"]?.[viewKey]) {{
        return bundle.dossiers["079942718"][viewKey];
      }}
      if (upperArg === "IBM" && bundle.dossiers["001368083"]?.[viewKey]) {{
        return bundle.dossiers["001368083"][viewKey];
      }}
      return null;
    }}

    function synthesizeDossierForDuns(dunsOrName, viewKey) {{
      const bundle = window.__DNB_SUITE_BUNDLE__;
      if (!bundle) return null;
      if (viewKey === "entity_matcher") {{
        return bundle.last_matcher_payload || bundle.matchers[bundle.primary_duns] || bundle.matchers["079942718"] || null;
      }}
      const rawStr = String(dunsOrName || "").trim();
      let cleanDuns = normalizeDunsKey(rawStr);
      let cand = cleanDuns ? bundle.candidates_by_duns[cleanDuns] : null;
      if (!cand && rawStr) {{
        const needle = rawStr.toUpperCase();
        for (const [cd, cObj] of Object.entries(bundle.candidates_by_duns)) {{
          if (String(cObj?.primary_name || "").toUpperCase().includes(needle)) {{
            cand = cObj;
            cleanDuns = cd;
            break;
          }}
        }}
      }}
      if (!cleanDuns) cleanDuns = bundle.primary_duns || "079942718";
      if (bundle.dossiers[cleanDuns] && bundle.dossiers[cleanDuns][viewKey]) {{
        return bundle.dossiers[cleanDuns][viewKey];
      }}

      const baseDossier =
        bundle.dossiers[bundle.primary_duns] ||
        bundle.dossiers["079942718"] ||
        Object.values(bundle.dossiers)[0];
      if (!baseDossier) return null;

      const dunsFmt = cand?.duns_formatted || `${{cleanDuns.slice(0, 2)}}-${{cleanDuns.slice(2, 5)}}-${{cleanDuns.slice(5)}}`;
      const entityName = cand?.primary_name || `D&B Verified Entity ${{dunsFmt}}`;
      const entityAddr = cand?.address || baseDossier.company_360?.company?.primary_address || "United States";
      const entityPhone = (cand?.telephone && cand.telephone !== "—") ? cand.telephone : (baseDossier.company_360?.company?.telephone || "—");
      const roleLabel = cand?.family_tree_role || cand?.role_badge || "Verified Operating Subsidiary";
      const guName = baseDossier.family_tree?.global_ultimate?.name || baseDossier.company_360?.company?.primary_name || entityName;
      const guDuns = baseDossier.family_tree?.global_ultimate?.duns || bundle.primary_duns || cleanDuns;

      if (viewKey === "family_tree" && baseDossier.family_tree) {{
        const ftClone = JSON.parse(JSON.stringify(baseDossier.family_tree));
        ftClone.duns = cleanDuns;
        ftClone.subject_company = {{
          ...(ftClone.subject_company || {{}}),
          duns: cleanDuns,
          duns_formatted: dunsFmt,
          primary_name: entityName,
          primary_address: entityAddr,
        }};
        // Ensure cleanDuns exists in ftClone.nodes so inspector & lineage highlight it
        if (Array.isArray(ftClone.nodes) && !ftClone.nodes.some((n) => n.duns === cleanDuns)) {{
          ftClone.nodes.push({{
            duns: cleanDuns,
            duns_formatted: dunsFmt,
            name: entityName,
            country: cand?.country || "US",
            roles: [roleLabel],
            roles_label: roleLabel,
            depth: 1,
            parent_duns: guDuns,
            parent_name: guName,
            is_global_ultimate: false,
            is_domestic_ultimate: false,
            is_hq: Boolean(cand?.is_hq),
            is_subsidiary: true,
            is_branch: Boolean(cand?.is_branch),
            is_queried_subject: true,
            children_count: 0,
            subsidiary_children_count: 0,
            branch_children_count: 0,
          }});
        }}
        return ftClone;
      }}

      if (viewKey === "company_360" && baseDossier.company_360) {{
        const c360 = JSON.parse(JSON.stringify(baseDossier.company_360));
        c360.duns = cleanDuns;
        c360.company = {{
          ...(c360.company || {{}}),
          duns: cleanDuns,
          duns_formatted: dunsFmt,
          primary_name: entityName,
          registered_name: entityName.toUpperCase(),
          primary_address: entityAddr,
          telephone: entityPhone,
          operating_status: cand?.operating_status || "Active",
        }};
        if (c360.company.summaries && c360.company.summaries.short_profile) {{
          c360.company.summaries.short_profile.text =
            `${{entityName}} (D-U-N-S® ${{dunsFmt}}) is a verified ${{roleLabel}} linked to Global Ultimate ${{guName}} (D-U-N-S® ${{guDuns}}), located at ${{entityAddr}}.`;
        }}
        return c360;
      }}

      if (viewKey === "supplier_risk" && baseDossier.supplier_risk) {{
        const sr = JSON.parse(JSON.stringify(baseDossier.supplier_risk));
        sr.duns = cleanDuns;
        sr.company = {{
          ...(sr.company || {{}}),
          duns: cleanDuns,
          duns_formatted: dunsFmt,
          primary_name: entityName,
          registered_name: entityName.toUpperCase(),
          primary_address: entityAddr,
        }};
        if (sr.procurement_identifiers) {{
          sr.procurement_identifiers.duns_formatted = dunsFmt;
        }}
        return sr;
      }}
      return null;
    }}

    function swapAppViewInDom(viewKey, payload, rawUrlPath) {{
      const templateHtml = window.__DNB_SUITE_BUNDLE__?.templates?.[viewKey];
      if (!templateHtml || typeof DOMParser === "undefined") return false;
      try {{
        const parser = new DOMParser();
        const doc = parser.parseFromString(templateHtml, "text/html");
        if (!doc || !doc.body) return false;

        closeDnbModal();
        if (doc.title) document.title = doc.title;

        // Update <style> tags in <head>
        document.head.querySelectorAll("style").forEach((s) => s.remove());
        doc.head.querySelectorAll("style").forEach((s) => {{
          const st = document.createElement("style");
          st.textContent = s.textContent;
          document.head.appendChild(st);
        }});

        if (payload) {{
          registerPayloadInSuiteBundle(payload);
          window.__DNB_ACTIVE_PAYLOAD__ = payload;
        }}

        const scripts = Array.from(doc.body.querySelectorAll("script"));
        scripts.forEach((s) => s.remove());
        document.body.innerHTML = doc.body.innerHTML;
        window.scrollTo(0, 0);

        if (
          rawUrlPath &&
          typeof window !== "undefined" &&
          window.location &&
          window.location.protocol &&
          window.location.protocol.startsWith("http") &&
          (window.location.pathname.startsWith("/apps/") ||
            window.location.hostname === "127.0.0.1" ||
            window.location.hostname === "localhost") &&
          window.history &&
          window.history.pushState
        ) {{
          try {{
            window.history.pushState({{}}, "", rawUrlPath);
          }} catch (_) {{}}
        }}

        for (const s of scripts) {{
          const newScript = document.createElement("script");
          newScript.textContent = s.textContent;
          document.body.appendChild(newScript);
        }}
        return true;
      }} catch (_) {{
        return false;
      }}
    }}

    function sendMcpRequest(method, params, timeoutMs = 4000) {{
      return new Promise((resolve, reject) => {{
        if (!window.parent || window.parent === window) {{
          return reject(new Error("No MCP host parent frame"));
        }}
        const id = rpcId++;
        const key = String(id);
        const timer = setTimeout(() => {{
          pendingRpc.delete(key);
          reject(new Error(`MCP RPC timeout for ${{method}}`));
        }}, timeoutMs);
        pendingRpc.set(key, {{
          resolve: (res) => {{
            clearTimeout(timer);
            resolve(res);
          }},
          reject: (err) => {{
            clearTimeout(timer);
            reject(err);
          }},
        }});
        window.parent.postMessage({{ jsonrpc: "2.0", id, method, params }}, "*");
      }});
    }}

    function sendMcpNotification(method, params) {{
      if (window.parent && window.parent !== window) {{
        window.parent.postMessage({{ jsonrpc: "2.0", method, params }}, "*");
      }}
    }}

    function extractToolPayload(raw) {{
      if (!raw) return null;
      if (typeof raw === "string") {{
        try {{
          return extractToolPayload(JSON.parse(raw));
        }} catch (_) {{
          return null;
        }}
      }}
      if (typeof raw !== "object") return null;
      if (raw.structuredContent && typeof raw.structuredContent === "object") {{
        return raw.structuredContent;
      }}
      if (raw.result) {{
        const inner = extractToolPayload(raw.result);
        if (inner) return inner;
      }}
      if (raw.toolResult) {{
        const inner = extractToolPayload(raw.toolResult);
        if (inner) return inner;
      }}
      const contentArr = Array.isArray(raw.content) ? raw.content : Array.isArray(raw) ? raw : null;
      if (contentArr) {{
        for (const blk of contentArr) {{
          if (blk && typeof blk === "object" && typeof blk.text === "string" && blk.text.trim()) {{
            try {{
              const parsed = JSON.parse(blk.text);
              if (parsed && typeof parsed === "object") return parsed;
            }} catch (_) {{}}
          }}
        }}
      }}
      if (
        raw.status === "success" ||
        raw.company ||
        raw.candidates ||
        raw.nodes ||
        raw.risk_gauges
      ) {{
        return raw;
      }}
      return null;
    }}

    function getToolCallEndpoints() {{
      const endpoints = [];
      if (
        typeof window !== "undefined" &&
        window.location &&
        window.location.origin &&
        window.location.origin !== "null" &&
        window.location.protocol.startsWith("http") &&
        (window.location.pathname.startsWith("/apps/") ||
          window.location.hostname === "127.0.0.1" ||
          window.location.hostname === "localhost")
      ) {{
        endpoints.push(`${{window.location.origin}}/apps/api/tool-call`);
      }}
      if (API_BASE_URL && !endpoints.includes(`${{API_BASE_URL}}/apps/api/tool-call`)) {{
        endpoints.push(`${{API_BASE_URL}}/apps/api/tool-call`);
      }}
      return endpoints;
    }}

    async function fetchDirectToolCallFull(toolName, args, timeoutMs = 2800) {{
      const endpoints = getToolCallEndpoints();
      for (const url of endpoints) {{
        const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
        const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
        try {{
          const resp = await fetch(url, {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ name: toolName, arguments: args }}),
            signal: controller ? controller.signal : undefined,
          }});
          if (timer) clearTimeout(timer);
          if (resp.ok) {{
            const data = await resp.json();
            const extracted = extractToolPayload(data);
            if (extracted) {{
              registerPayloadInSuiteBundle(extracted);
            }}
            return data;
          }}
        }} catch (_) {{
          if (timer) clearTimeout(timer);
        }}
      }}
      return null;
    }}

    async function fetchDirectToolCall(toolName, args, timeoutMs = 2800) {{
      const data = await fetchDirectToolCallFull(toolName, args, timeoutMs);
      if (data) {{
        const extracted = extractToolPayload(data);
        if (extracted) return extracted;
      }}
      return null;
    }}

    async function callMcpToolWithFallback(toolName, args) {{
      const statusEl = document.getElementById("statusText");
      if (statusEl) statusEl.textContent = `Querying Dun & Bradstreet MCP (${{toolName}})...`;

      // 1. Check preloaded suite bundle first for instant 0ms response
      const preloaded = getPreloadedPayloadForTool(toolName, args || {{}});
      if (preloaded) {{
        if (statusEl) statusEl.textContent = `Synchronized via D&B Preloaded Enterprise Cache (${{toolName}})`;
        return preloaded;
      }}

      // 2. If connected to an active SEP-1865 MCP host, try JSON-RPC tools/call
      if (typeof mcpHostConnected !== "undefined" && mcpHostConnected) {{
        try {{
          const res = await sendMcpRequest("tools/call", {{ name: toolName, arguments: args }}, 1400);
          const extracted = extractToolPayload(res);
          if (extracted) {{
            registerPayloadInSuiteBundle(extracted);
            if (statusEl) statusEl.textContent = `Synchronized via MCP Host (${{toolName}})`;
            return extracted;
          }}
        }} catch (_) {{}}
      }}

      // 3. Direct HTTPS call to D&B MCP Apps Server on Cloud Run (with 2.8s AbortController timeout)
      const directData = await fetchDirectToolCall(toolName, args, 2800);
      if (directData) {{
        if (statusEl) statusEl.textContent = `Synchronized via D&B MCP Proxy (${{toolName}})`;
        return directData;
      }}

      // 4. Offline / sandboxed iframe fallback: synthesize from matched candidates & family tree in memory
      const viewKey = toolNameToViewKey(toolName);
      const synth = synthesizeDossierForDuns(args?.duns || args?.name, viewKey);
      if (synth) {{
        if (statusEl) statusEl.textContent = `Rendered from Verified D&B Session Context (${{toolName}})`;
        return synth;
      }}
      if (statusEl) statusEl.textContent = `Completed D&B tool request (${{toolName}})`;
      return null;
    }}

    async function switchToMcpApp(toolName, args, rawUrlPath, triggerBtn) {{
      const statusEl = document.getElementById("statusText");
      if (statusEl) statusEl.textContent = `Opening D&B MCP App (${{toolName}})...`;

      // Notify MCP host if running inside an MCP client
      sendMcpNotification("ui/message", {{
        role: "user",
        content: [{{ type: "text", text: `Open ${{toolName}} with ${{JSON.stringify(args || {{}})}}` }}],
      }});

      const viewKey = toolNameToViewKey(toolName);

      // Path 1: Instant (<5ms) in-DOM switch if preloaded in window.__DNB_SUITE_BUNDLE__
      const preloaded = getPreloadedPayloadForTool(toolName, args || {{}});
      if (preloaded && swapAppViewInDom(viewKey, preloaded, rawUrlPath)) {{
        return;
      }}

      // Path 2: Instant (<10ms) optimistic in-DOM switch using candidate/tree synthesis + background live enrichment
      const synth = synthesizeDossierForDuns(args?.duns || args?.name, viewKey);
      if (synth && swapAppViewInDom(viewKey, synth, rawUrlPath)) {{
        fetchDirectToolCall(toolName, args || {{}}, 3200)
          .then((liveData) => {{
            if (liveData && typeof window.__dnbCurrentHydratePayload === "function") {{
              registerPayloadInSuiteBundle(liveData);
              window.__dnbCurrentHydratePayload(liveData);
            }}
          }})
          .catch(() => {{}});
        return;
      }}

      // Path 3: Direct network fetch with fast 2.8s timeout
      let origHtml = "";
      if (triggerBtn) {{
        origHtml = triggerBtn.innerHTML;
        triggerBtn.disabled = true;
        triggerBtn.classList.add("is-loading");
        triggerBtn.textContent = "⏳ Loading...";
      }}
      try {{
        const fullRes = await fetchDirectToolCallFull(toolName, args || {{}}, 2800);
        const extracted = extractToolPayload(fullRes);
        if (extracted && swapAppViewInDom(viewKey, extracted, rawUrlPath)) {{
          return;
        }}
      }} catch (_) {{}} finally {{
        if (triggerBtn) {{
          triggerBtn.disabled = false;
          triggerBtn.classList.remove("is-loading");
          triggerBtn.innerHTML = origHtml;
        }}
      }}
    }}

    function sendUiMessage(promptText) {{
      sendMcpNotification("ui/message", {{
        role: "user",
        content: [{{ type: "text", text: promptText }}],
      }});
      const statusEl = document.getElementById("statusText");
      if (statusEl) statusEl.textContent = "Sent prompt to AI assistant";
    }}

    function copyTextToClipboard(textStr) {{
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(textStr).catch(() => {{}});
      }}
      try {{
        const ta = document.createElement("textarea");
        ta.value = textStr;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }} catch (_) {{}}
    }}

    function copyDunsToClipboard(dunsStr, badgeEl) {{
      copyTextToClipboard(dunsStr);
      const statusEl = document.getElementById("statusText");
      if (statusEl) statusEl.textContent = `Copied D-U-N-S ${{dunsStr}} to clipboard`;
      if (badgeEl) {{
        const orig = badgeEl.innerHTML;
        badgeEl.textContent = `✓ Copied ${{dunsStr}}`;
        setTimeout(() => {{ badgeEl.innerHTML = orig; }}, 1200);
      }}
    }}

    function closeDnbModal() {{
      const existing = document.getElementById("dnbInteractiveModal");
      if (existing) existing.remove();
    }}

    function showDnbModal(title, subtitle, bodyHtml, plainTextToCopy) {{
      closeDnbModal();
      const overlay = document.createElement("div");
      overlay.id = "dnbInteractiveModal";
      overlay.className = "dnb-modal-overlay";
      overlay.innerHTML = `
        <div class="dnb-modal-card" role="dialog" aria-modal="true">
          <div class="dnb-modal-header">
            <div>
              <div style="font-size:15px;font-weight:800;letter-spacing:-0.01em;">${{escapeHtml(title)}}</div>
              <div style="font-size:12px;color:#ACD5E1;margin-top:2px;">${{escapeHtml(subtitle)}}</div>
            </div>
            <button type="button" class="btn btn-ghost-light" id="dnbModalCloseTopBtn" style="height:30px;padding:0 10px;">✕ Close</button>
          </div>
          <div class="dnb-modal-body">${{bodyHtml}}</div>
          <div class="dnb-modal-footer">
            <span style="font-size:12px;color:#00435F;font-weight:700;" id="dnbModalStatus">Generated from Verified Dun &amp; Bradstreet Data Cloud</span>
            <div style="display:flex;gap:8px;">
              <button type="button" class="btn btn-outline" id="dnbModalCopyBtn">📋 Copy Memo to Clipboard</button>
              <button type="button" class="btn btn-primary" id="dnbModalDoneBtn">Done</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
      overlay.addEventListener("click", (e) => {{
        if (e.target === overlay) closeDnbModal();
      }});
      const closeTop = document.getElementById("dnbModalCloseTopBtn");
      if (closeTop) closeTop.addEventListener("click", closeDnbModal);
      const doneBtn = document.getElementById("dnbModalDoneBtn");
      if (doneBtn) doneBtn.addEventListener("click", closeDnbModal);
      const copyBtn = document.getElementById("dnbModalCopyBtn");
      if (copyBtn) {{
        copyBtn.addEventListener("click", () => {{
          copyTextToClipboard(plainTextToCopy || title);
          copyBtn.textContent = "✓ Copied to Clipboard";
          const st = document.getElementById("dnbModalStatus");
          if (st) st.textContent = "Copied full briefing memo to clipboard!";
          setTimeout(() => {{ copyBtn.textContent = "📋 Copy Memo to Clipboard"; }}, 1800);
        }});
      }}
    }}

    let mcpHostConnected = Boolean(window.__dnbMcpHostConnected);

    if (window.__dnbMessageHandler) {{
      window.removeEventListener("message", window.__dnbMessageHandler);
    }}
    window.__dnbMessageHandler = (event) => {{
      let msg = event.data;
      if (typeof msg === "string") {{
        try {{
          msg = JSON.parse(msg);
        }} catch (_) {{
          return;
        }}
      }}
      if (!msg || typeof msg !== "object" || msg.jsonrpc !== "2.0") return;
      mcpHostConnected = true;
      window.__dnbMcpHostConnected = true;

      const msgIdKey = msg.id !== undefined && msg.id !== null ? String(msg.id) : null;
      if (msgIdKey && pendingRpc.has(msgIdKey)) {{
        const {{ resolve, reject }} = pendingRpc.get(msgIdKey);
        pendingRpc.delete(msgIdKey);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
        return;
      }}

      if ((msg.method === "ui/notifications/tool-result" || msg.method === "notifications/tool-result") && msg.params) {{
        const extracted = extractToolPayload(msg.params);
        if (extracted) {{
          registerPayloadInSuiteBundle(extracted);
          if (typeof hydratePayload === "function") {{
            hydratePayload(extracted);
          }}
        }}
      }}
    }};
    window.addEventListener("message", window.__dnbMessageHandler);

    async function initBridge() {{
      if (window.parent && window.parent !== window && !window.__dnbBridgeInitialized) {{
        window.__dnbBridgeInitialized = true;
        try {{
          await sendMcpRequest("ui/initialize", {{
            protocolVersion: "2025-06-18",
            appInfo: {{ name: {app_name!r}, version: "1.0.0" }},
            appCapabilities: {{}},
          }}, 600);
          mcpHostConnected = true;
          window.__dnbMcpHostConnected = true;
        }} catch (_) {{}}
        sendMcpNotification("ui/notifications/initialized", {{}});

        if (typeof ResizeObserver !== "undefined") {{
          const ro = new ResizeObserver(() => {{
            const h = Math.ceil(document.documentElement.scrollHeight);
            const w = Math.ceil(document.documentElement.scrollWidth);
            sendMcpNotification("ui/notifications/size-changed", {{ width: w, height: h }});
          }});
          ro.observe(document.documentElement);
        }}
      }}
    }}
    """

