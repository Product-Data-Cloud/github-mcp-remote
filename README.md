# GitHub MCP Remote

Remote GitHub MCP Server for mobile PDC development.

## Version

**Current:** V2.0 PRACTICAL

## Features

### Level 1: Performance
- Rate limiting (100 req/hour per tool)
- Smart caching (5 min for file reads)
- Enhanced error handling

### Level 2: Extended Tools
- 9 tools (up from 3 in V1.0)
- File size checks (max 1MB)
- Token optimization

## Tools Available

1. `create_or_update_file` - Create/update files (with size check)
2. `get_file_contents` - Read files (with caching)
3. `list_repos` - List organization repositories
4. `get_repo_info` - Get detailed repo information
5. `list_branches` - List all branches
6. `create_branch` - Create new branches
7. `search_code` - Search code in repositories
8. `create_pull_request` - Create pull requests
9. `connection_status` - Check connection and rate limits

## Deployment

**Auto-Deploy:** ✅ ACTIVE

Every push to `main` branch automatically triggers:
1. Build Docker image
2. Push to Container Registry
3. Deploy to Cloud Run (europe-west1)

**Service URL:** https://github-mcp-409811184795.europe-west1.run.app

## Cost

**0€/month** (Google Cloud Free Tier)

---

**Last Updated:** 2025-11-05  
**Status:** Production Ready ✅
