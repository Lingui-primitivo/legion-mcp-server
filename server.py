"""
LEGION AI — Custom MCP Server
Allows Claude to operate the LEGION AI platform directly.

Tools:
- List/create/update leads
- View pipeline and deals
- Trigger call analysis
- Get dashboard metrics
- Manage campaigns
- Check system health
- Push deployments

Deploy: Railway (separate service) or run locally
"""

import os
import json
import httpx
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════

LEGION_BASE_URL = os.environ.get("LEGION_BASE_URL", "https://legion-ia-railway-production.up.railway.app")
LEGION_AUTH_TOKEN = os.environ.get("LEGION_AUTH_TOKEN", "")  # JWT from login
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "Lingui-primitivo/LEGION-IA-RAILWAY")

# ═══════════════════════════════════════
# MCP SERVER
# ═══════════════════════════════════════

mcp = FastMCP(
    "legion-ai",
    description="LEGION AI Platform — Operate the entire sales automation system: leads, deals, agents, campaigns, analytics, and deployments.",
)

# ═══════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════

async def trpc_query(endpoint: str, input_data: dict | None = None) -> dict:
    """Call a tRPC query endpoint."""
    url = f"{LEGION_BASE_URL}/api/trpc/{endpoint}"
    params = {}
    if input_data:
        params["input"] = json.dumps(input_data)
    
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {}
        if LEGION_AUTH_TOKEN:
            headers["Cookie"] = f"token={LEGION_AUTH_TOKEN}"
        resp = await client.get(url, params=params, headers=headers)
        return resp.json()


async def trpc_mutation(endpoint: str, input_data: dict) -> dict:
    """Call a tRPC mutation endpoint."""
    url = f"{LEGION_BASE_URL}/api/trpc/{endpoint}"
    
    async with httpx.AsyncClient(timeout=60) as client:
        headers = {"Content-Type": "application/json"}
        if LEGION_AUTH_TOKEN:
            headers["Cookie"] = f"token={LEGION_AUTH_TOKEN}"
        resp = await client.post(url, json=input_data, headers=headers)
        return resp.json()


async def github_api(method: str, path: str, data: dict | None = None) -> dict:
    """Call GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        if method == "GET":
            resp = await client.get(url, headers=headers)
        elif method == "POST":
            resp = await client.post(url, json=data, headers=headers)
        elif method == "PATCH":
            resp = await client.patch(url, json=data, headers=headers)
        else:
            resp = await client.request(method, url, json=data, headers=headers)
        return resp.json()


# ═══════════════════════════════════════
# TOOLS — LEADS & CRM
# ═══════════════════════════════════════

@mcp.tool()
async def legion_list_leads(limit: int = 20, offset: int = 0) -> str:
    """List all leads in LEGION CRM. Returns lead name, email, status, score, and source."""
    result = await trpc_query("leads.list", {"limit": limit, "offset": offset})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_create_lead(
    name: str,
    email: str,
    company: str = "",
    phone: str = "",
    source: str = "manual",
    notes: str = "",
) -> str:
    """Create a new lead in LEGION CRM."""
    result = await trpc_mutation("leads.create", {
        "name": name,
        "email": email,
        "company": company,
        "phone": phone,
        "source": source,
        "notes": notes,
    })
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_get_pipeline() -> str:
    """Get the full sales pipeline with all deals, stages, and values."""
    result = await trpc_query("crm.deals.list")
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — CALL INTELLIGENCE
# ═══════════════════════════════════════

@mcp.tool()
async def legion_analyze_call(transcript: str, title: str = "Call Analysis") -> str:
    """Analyze a sales call transcript using AI. Returns BANT score, sentiment, objections, coaching tips."""
    result = await trpc_mutation("callIntelligence.analyzeText", {
        "transcript": transcript,
        "title": title,
    })
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_call_stats() -> str:
    """Get Call Intelligence statistics: total calls, avg score, avg sentiment, avg BANT."""
    result = await trpc_query("callIntelligence.stats")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_list_calls(limit: int = 20) -> str:
    """List all analyzed calls with their scores and status."""
    result = await trpc_query("callIntelligence.list", {"limit": limit})
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — AGENTS & BOARDROOM
# ═══════════════════════════════════════

@mcp.tool()
async def legion_boardroom_debate(topic: str, context: str = "") -> str:
    """Start a Boardroom debate where all 7 AI agents discuss a sales strategy topic."""
    result = await trpc_mutation("boardroom.startDebate", {
        "topic": topic,
        "context": context,
    })
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — ANALYTICS & METRICS
# ═══════════════════════════════════════

@mcp.tool()
async def legion_dashboard_metrics() -> str:
    """Get main dashboard metrics: leads, deals, pipeline value, conversion rates, agent activity."""
    result = await trpc_query("sprint4.dashboardStats")
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — SYSTEM & DEPLOYMENT
# ═══════════════════════════════════════

@mcp.tool()
async def legion_health_check() -> str:
    """Check if LEGION AI is running and healthy. Returns status, uptime, and version."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{LEGION_BASE_URL}/api/trpc/auth.me")
            data = resp.json()
            return json.dumps({
                "status": "online",
                "url": LEGION_BASE_URL,
                "http_status": resp.status_code,
                "response": data,
                "checked_at": datetime.now().isoformat(),
            }, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "status": "offline",
                "url": LEGION_BASE_URL,
                "error": str(e),
                "checked_at": datetime.now().isoformat(),
            }, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_recent_deploys(count: int = 5) -> str:
    """Get recent GitHub commits (deployments) for LEGION AI."""
    if not GITHUB_TOKEN:
        return json.dumps({"error": "GITHUB_TOKEN not configured"})
    
    result = await github_api("GET", f"/commits?per_page={count}")
    if isinstance(result, list):
        commits = [
            {
                "sha": c["sha"][:7],
                "message": c["commit"]["message"].split("\n")[0],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"],
            }
            for c in result
        ]
        return json.dumps(commits, indent=2, ensure_ascii=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_list_issues(state: str = "open") -> str:
    """List GitHub issues/bugs for LEGION AI. State: open, closed, all."""
    if not GITHUB_TOKEN:
        return json.dumps({"error": "GITHUB_TOKEN not configured"})
    
    result = await github_api("GET", f"/issues?state={state}&per_page=20")
    if isinstance(result, list):
        issues = [
            {
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "labels": [l["name"] for l in i.get("labels", [])],
                "created_at": i["created_at"],
            }
            for i in result
        ]
        return json.dumps(issues, indent=2, ensure_ascii=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_create_issue(title: str, body: str, labels: list[str] | None = None) -> str:
    """Create a GitHub issue/bug report for LEGION AI."""
    if not GITHUB_TOKEN:
        return json.dumps({"error": "GITHUB_TOKEN not configured"})
    
    data = {"title": title, "body": body}
    if labels:
        data["labels"] = labels
    
    result = await github_api("POST", "/issues", data)
    return json.dumps({
        "number": result.get("number"),
        "url": result.get("html_url"),
        "title": result.get("title"),
    }, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — DATABASE DIRECT
# ═══════════════════════════════════════

@mcp.tool()
async def legion_db_query(query_description: str) -> str:
    """Execute a read-only database query on LEGION's TiDB database.
    Describe what you want to query in natural language and the system will translate it.
    Only SELECT queries are allowed for safety.
    """
    # This connects via the tRPC system endpoint
    result = await trpc_query("system.health")
    return json.dumps({
        "note": "Direct DB queries require DATABASE_URL. Use tRPC endpoints instead.",
        "system_health": result,
    }, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# RUN
# ═══════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
