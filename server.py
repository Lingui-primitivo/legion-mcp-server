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

mcp = FastMCP("legion-ai", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))

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
# TOOLS — LEAD ENRICHMENT
# ═══════════════════════════════════════

@mcp.tool()
async def legion_enrich_lead(lead_id: int, cnpj: str = "", website: str = "", linkedin_url: str = "") -> str:
    """Enrich a lead with real data: CNPJ lookup (ReceitaWS), website scraping, and AI analysis.
    Returns company info, pain points, tech stack, competitors, and qualification scores."""
    input_data = {"leadId": lead_id}
    if cnpj:
        input_data["cnpj"] = cnpj
    if website:
        input_data["website"] = website
    if linkedin_url:
        input_data["linkedinUrl"] = linkedin_url
    
    result = await trpc_mutation("enrichment.smartEnrich", {"json": input_data})
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
# TOOLS — KNOWLEDGE BASE
# ═══════════════════════════════════════

@mcp.tool()
async def legion_knowledge_ask(question: str, agent: str = "") -> str:
    """Ask a question answered by the knowledge base (sales playbooks, product info, FAQs). AI-powered RAG."""
    input_data = {"question": question}
    if agent:
        input_data["agentContext"] = agent
    result = await trpc_mutation("knowledgeBase.ask", {"json": input_data})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_knowledge_add(title: str, content: str, category: str = "sales") -> str:
    """Add a document to the knowledge base. Categories: technical, sales, product, faq, policy, training."""
    result = await trpc_mutation("knowledgeBase.add", {"json": {"title": title, "content": content, "category": category}})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_knowledge_list(category: str = "") -> str:
    """List all knowledge base documents, optionally filtered by category."""
    params = {}
    if category:
        params["category"] = category
    result = await trpc_query("knowledgeBase.list", params)
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — PIPELINE VELOCITY & GOALS
# ═══════════════════════════════════════

@mcp.tool()
async def legion_pipeline_velocity() -> str:
    """Pipeline velocity metrics: deals per stage, average cycle time, conversion rates, flow rate (R$/day)."""
    result = await trpc_query("pipelineVelocity.metrics")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_goal_attainment(period: str = "month") -> str:
    """Quota/goal attainment: revenue vs target, deals closed, leads generated, days remaining, on-track status."""
    result = await trpc_query("goals.attainment", {"period": period})
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — MULTICHANNEL SEQUENCES
# ═══════════════════════════════════════

@mcp.tool()
async def legion_list_sequences() -> str:
    """List all multichannel outreach sequences with steps, enrollments, and stats."""
    result = await trpc_query("sequences.list")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_create_sequence(name: str, description: str = "", steps: str = "") -> str:
    """Create a new multichannel sequence. Steps is a JSON array of steps with channel (email/whatsapp/linkedin/call/delay), message, subject (for email), delayDays."""
    import json as j
    input_data = {"name": name, "description": description}
    if steps:
        input_data["steps"] = j.loads(steps)
    result = await trpc_mutation("sequences.create", {"json": input_data})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_ai_generate_sequence(goal: str, channels: str = "email,whatsapp", total_steps: int = 5, target_audience: str = "", product: str = "") -> str:
    """AI-generate a complete multichannel sequence. Provide the goal (e.g., 'book demos with doctors') and channels."""
    input_data = {
        "goal": goal,
        "channels": channels.split(","),
        "totalSteps": total_steps,
    }
    if target_audience:
        input_data["targetAudience"] = target_audience
    if product:
        input_data["product"] = product
    result = await trpc_mutation("sequences.aiGenerate", {"json": input_data})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_enroll_in_sequence(sequence_id: int, lead_ids: str = "") -> str:
    """Enroll leads into a sequence. lead_ids is comma-separated (e.g., '1,2,3')."""
    ids = [int(x.strip()) for x in lead_ids.split(",") if x.strip()]
    result = await trpc_mutation("sequences.enroll", {"json": {"sequenceId": sequence_id, "leadIds": ids}})
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — REVENUE FORECASTING
# ═══════════════════════════════════════

@mcp.tool()
async def legion_forecast() -> str:
    """Generate AI-powered revenue forecast. Combines CRM deal data with Call Intelligence
    signals (sentiment, BANT scores, objections) to predict deal outcomes and pipeline health."""
    result = await trpc_mutation("forecasting.generate", {"json": {}})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_forecast_summary() -> str:
    """Quick pipeline summary: total deals, win rate, pipeline value, deals closing this month."""
    result = await trpc_query("forecasting.summary")
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — CONTACT DATABASE
# ═══════════════════════════════════════

@mcp.tool()
async def legion_search_contacts(query: str = "", status: str = "", min_score: int = 0) -> str:
    """Search leads/contacts by name, email, phone, company. Filter by status (hot/warm/cold) and minimum score."""
    params = {}
    if query:
        params["query"] = query
    if status:
        params["status"] = status
    if min_score > 0:
        params["minScore"] = min_score
    result = await trpc_query("contactDatabase.search", params)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_bulk_import_leads(leads_json: str) -> str:
    """Bulk import leads. leads_json is a JSON array of objects with name, email, phone, company, status, source."""
    import json as j
    leads_data = j.loads(leads_json)
    result = await trpc_mutation("contactDatabase.bulkImport", {"json": {"leads": leads_data}})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_contact_stats() -> str:
    """Get contact database stats: total, by status, by source, by agent, coverage metrics."""
    result = await trpc_query("contactDatabase.stats")
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — DEAL SCORING
# ═══════════════════════════════════════

@mcp.tool()
async def legion_score_deals() -> str:
    """Score all open deals based on engagement, fit, timing, and competition signals. Updates probabilities."""
    result = await trpc_mutation("dealScoring.scoreAll", {"json": {}})
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — COMPETITIVE INTELLIGENCE
# ═══════════════════════════════════════

@mcp.tool()
async def legion_competitive_overview() -> str:
    """See all competitors mentioned in calls with frequency, objections, and patterns."""
    result = await trpc_query("competitiveIntel.overview")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_battle_card(competitor_name: str) -> str:
    """Generate AI battle card for a competitor: strengths, weaknesses, objection handlers, win strategies."""
    result = await trpc_mutation("competitiveIntel.battleCard", {"json": {"competitorName": competitor_name}})
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def legion_win_loss_analysis() -> str:
    """Win/loss analysis: win rate, average deal sizes, lost reasons breakdown."""
    result = await trpc_query("competitiveIntel.winLoss")
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — AGENT ANALYTICS
# ═══════════════════════════════════════

@mcp.tool()
async def legion_agent_performance(days: int = 30) -> str:
    """AI agent performance dashboard: actions per agent, trends, lead distribution."""
    result = await trpc_query("agentAnalytics.performance", {"days": days})
    return json.dumps(result, indent=2, ensure_ascii=False)


# ═══════════════════════════════════════
# TOOLS — UNIFIED DASHBOARD
# ═══════════════════════════════════════

@mcp.tool()
async def legion_dashboard() -> str:
    """Full platform dashboard: leads, pipeline, call intelligence, sequences — all in one."""
    result = await trpc_query("unifiedDashboard.stats")
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
    mcp.run(transport="sse")
