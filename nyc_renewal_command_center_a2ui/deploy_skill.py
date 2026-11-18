#!/usr/bin/env python3
"""Standalone Gemini Enterprise deployer & connector binder for `nyc-renewal-command-center-a2ui`.

Uses 100% Python 3 standard library (`urllib.request`, `gzip`, `base64`, `argparse`)
with Application Default Credentials (`gcloud auth application-default print-access-token`).
Zero external local folder dependencies and zero hardcoded project numbers or secrets.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import gzip
import json
import os
import pathlib
import re
import subprocess
import urllib.request
from typing import Any

MARKER = "NYC_RENEWAL_A2UI_CLI_B64:"


def _load_dotenv(env_file: pathlib.Path) -> None:
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        key = k.strip()
        val = v.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = val


def _adc_token() -> str:
    return subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        shell=False,
        text=True,
        timeout=20,
    ).strip()


def _api_json(url: str, token: str, proj_num: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Goog-User-Project": proj_num,
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _discover_project_connectors(proj_num: str, token: str) -> dict[str, str]:
    """Auto-discovers Salesforce, Smartsheet, D&B, and Jira MCP dataConnector paths in the target project."""
    found: dict[str, str] = {}
    ar_url = f"https://agentregistry.googleapis.com/v1alpha/projects/{proj_num}/locations/global/mcpServers?pageSize=100"
    with contextlib.suppress(Exception):
        res = _api_json(ar_url, token, proj_num)
        for srv in res.get("mcpServers") or []:
            blob = json.dumps(srv)
            for m in re.finditer(
                r"(projects/\d+/locations/[A-Za-z0-9_-]+/collections/([A-Za-z0-9_.-]+)/dataConnector)",
                blob,
            ):
                conn_path, coll_low = m.group(1), m.group(2).lower()
                if "salesforce" in coll_low:
                    found.setdefault("salesforce", conn_path)
                elif "smartsheet" in coll_low:
                    found.setdefault("smartsheet", conn_path)
                elif ("d-b" in coll_low or "dnb" in coll_low) and "apps" not in coll_low:
                    found.setdefault("dnb", conn_path)
                elif "jira" in coll_low or "atlassian" in coll_low or "rovo" in coll_low:
                    found.setdefault("jira", conn_path)
    return found


def _build_bound_instruction(
    root_dir: pathlib.Path,
    proj_num: str,
    connectors: dict[str, str],
    sf_org_url: str,
) -> tuple[str, str]:
    """Returns (description, markdown_instruction_body) with project connectors injected in memory."""
    skill_dir = root_dir / "nyc_renewal_a2ui_skill"
    cli_text = (skill_dir / "scripts" / "nyc_renewal_a2ui_cli.py").read_text(encoding="utf-8")
    md_full = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

    cli_bound = cli_text.replace(
        'DEFAULT_PROJECT_NUM = os.environ.get("GE_PROJECT_NUMBER") or "000000000000"',
        f'DEFAULT_PROJECT_NUM = os.environ.get("GE_PROJECT_NUMBER") or "{proj_num}"',
    )
    placeholder_map = {
        "salesforce": "projects/{DEFAULT_PROJECT_NUM}/locations/global/collections/salesforce-mcp-connector/dataConnector",
        "smartsheet": "projects/{DEFAULT_PROJECT_NUM}/locations/global/collections/smartsheet-mcp-server/dataConnector",
        "dnb": "projects/{DEFAULT_PROJECT_NUM}/locations/global/collections/d-b-connector/dataConnector",
        "jira": "projects/{DEFAULT_PROJECT_NUM}/locations/global/collections/atlassian-rovo-jira-mcp-server/dataConnector",
    }
    for key, ph in placeholder_map.items():
        if connectors.get(key):
            cli_bound = cli_bound.replace(f'f"{ph}"', f'"{connectors[key]}"')
    if sf_org_url:
        cli_bound = cli_bound.replace('"https://login.salesforce.com"', f'"{sf_org_url.rstrip("/")}"')

    b64 = base64.b64encode(gzip.compress(cli_bound.encode("utf-8"), compresslevel=9)).decode("ascii")
    md_updated = re.sub(rf"{re.escape(MARKER)}[A-Za-z0-9+/=]+", f"{MARKER}{b64}", md_full, count=1)

    desc = "Guided 4-Phase A2UI v0.9 Canvas Renewal Command Center for Gemini Enterprise (Sobi)."
    m_desc = re.search(r"^description:\s*(.+)$", md_updated, re.M)
    if m_desc:
        desc = m_desc.group(1).strip()

    m_fm = re.match(r"^---\n.*?\n---\n+", md_updated, re.S)
    instr_body = md_updated[m_fm.end() :] if m_fm else md_updated
    return desc, instr_body


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    _load_dotenv(root / ".env")

    parser = argparse.ArgumentParser(description="Deploy nyc-renewal-command-center-a2ui to Gemini Enterprise")
    parser.add_argument("--project-number", default=os.environ.get("PROJECT_NUMBER", ""), help="Numeric GCP project number")
    parser.add_argument("--engine-id", default=os.environ.get("ENGINE_ID", "global-gemini-enterprise"), help="Gemini Enterprise Engine ID")
    parser.add_argument("--existing-skill-id", default=os.environ.get("EXISTING_SKILL_ID", ""), help="Optional private-skill-<ID> to patch in place")
    parser.add_argument("--sobi-agent-ids", default=os.environ.get("SOBI_AGENT_IDS", ""), help="Optional comma-separated sobi-<ID> agent IDs to mount onto")
    parser.add_argument("--sf-connector", default=os.environ.get("SALESFORCE_MCP_CONNECTOR", ""))
    parser.add_argument("--ss-connector", default=os.environ.get("SMARTSHEET_MCP_CONNECTOR", ""))
    parser.add_argument("--dnb-connector", default=os.environ.get("DNB_MCP_CONNECTOR", ""))
    parser.add_argument("--jira-connector", default=os.environ.get("JIRA_MCP_CONNECTOR", ""))
    parser.add_argument("--sf-org-url", default=os.environ.get("SALESFORCE_ORG_BASE_URL", ""))
    args = parser.parse_args()

    proj = str(args.project_number or "").strip()
    if not re.fullmatch(r"\d{6,20}", proj) or set(proj) == {"0"}:
        raise SystemExit("Error: Provide a valid --project-number (or set PROJECT_NUMBER in .env).")

    token = _adc_token()
    discovered = _discover_project_connectors(proj, token)
    connectors = {
        "salesforce": args.sf_connector or discovered.get("salesforce", ""),
        "smartsheet": args.ss_connector or discovered.get("smartsheet", ""),
        "dnb": args.dnb_connector or discovered.get("dnb", ""),
        "jira": args.jira_connector or discovered.get("jira", ""),
    }

    desc, instr_body = _build_bound_instruction(root, proj, connectors, args.sf_org_url)
    agents_base = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{proj}/locations/global/"
        f"collections/default_collection/engines/{args.engine_id}/assistants/default_assistant/agents"
    )

    skill_id = str(args.existing_skill_id or "").strip()
    if skill_id:
        agent_id = skill_id if skill_id.startswith("agent-registry-skill-") else f"agent-registry-skill-{skill_id}"
        target_url = f"{agents_base}/{agent_id}"
        cur = _api_json(target_url, token, proj)
        cur["description"] = desc
        cur.setdefault("skillAgentDefinition", {})["instruction"] = instr_body
        patched = _api_json(f"{target_url}?updateMask=description,skillAgentDefinition.instruction", token, proj, method="PATCH", body=cur)
        ar_skill = (patched.get("skillAgentDefinition") or {}).get("agentRegistrySkill") or f"projects/{proj}/locations/global/skills/{skill_id}"
        print(f"Patched Gemini Enterprise skill: {patched.get('name')} -> {ar_skill}")
    else:
        body = {
            "displayName": "nyc-renewal-command-center-a2ui",
            "description": desc,
            "authorizationPolicy": "ALL_USERS",
            "skillAgentDefinition": {"instruction": instr_body},
        }
        created = _api_json(agents_base, token, proj, method="POST", body=body)
        ar_skill = (created.get("skillAgentDefinition") or {}).get("agentRegistrySkill", "")
        print(f"Created Gemini Enterprise skill: {created.get('name')} -> {ar_skill}")

    for raw_sobi in [x.strip() for x in str(args.sobi_agent_ids or "").split(",") if x.strip()]:
        sobi_url = f"{agents_base}/{raw_sobi}"
        sobi_cur = _api_json(sobi_url, token, proj)
        m_def = sobi_cur.setdefault("managedAgentDefinition", {})
        skills_list = list(m_def.get("agentRegistrySkills") or [])
        if ar_skill and ar_skill not in skills_list:
            skills_list.append(ar_skill)
            m_def["agentRegistrySkills"] = skills_list
            _api_json(f"{sobi_url}?updateMask=managedAgentDefinition.agentRegistrySkills", token, proj, method="PATCH", body=sobi_cur)
            print(f"Mounted {ar_skill} onto Sobi agent {raw_sobi}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
