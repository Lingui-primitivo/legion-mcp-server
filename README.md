# LEGION AI — MCP Server

Custom MCP connector that lets Claude operate the entire LEGION AI platform.

## Tools Disponíveis

| Tool | Descrição |
|------|-----------|
| `legion_list_leads` | Listar leads do CRM |
| `legion_create_lead` | Criar novo lead |
| `legion_get_pipeline` | Ver pipeline de deals |
| `legion_analyze_call` | Analisar transcrição de call |
| `legion_call_stats` | Estatísticas do Call Intelligence |
| `legion_list_calls` | Listar calls analisadas |
| `legion_boardroom_debate` | Iniciar debate na Sala de Conselho |
| `legion_dashboard_metrics` | Métricas do dashboard |
| `legion_health_check` | Verificar se o sistema está online |
| `legion_recent_deploys` | Ver últimos deploys (commits) |
| `legion_list_issues` | Ver issues/bugs no GitHub |
| `legion_create_issue` | Criar issue/bug report |

## Setup Local

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis
export LEGION_BASE_URL="https://legion-ia-railway-production.up.railway.app"
export LEGION_AUTH_TOKEN="seu_jwt_token"  # do cookie após login
export GITHUB_TOKEN="ghp_..."
export GITHUB_REPO="Lingui-primitivo/LEGION-IA-RAILWAY"

# 3. Testar
python server.py
```

## Usar no Claude Desktop

Adicionar ao `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "legion-ai": {
      "command": "python",
      "args": ["/caminho/para/legion-mcp/server.py"],
      "env": {
        "LEGION_BASE_URL": "https://legion-ia-railway-production.up.railway.app",
        "LEGION_AUTH_TOKEN": "seu_jwt_token",
        "GITHUB_TOKEN": "ghp_...",
        "GITHUB_REPO": "Lingui-primitivo/LEGION-IA-RAILWAY"
      }
    }
  }
}
```

## Usar no Claude.ai (Conector Personalizado)

Deploy como serviço SSE no Railway e adicionar URL no Claude.ai > Settings > Connectors.
