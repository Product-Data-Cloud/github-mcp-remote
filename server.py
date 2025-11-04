import asyncio
import logging
import os
from fastmcp import FastMCP
from github import Github, GithubException
import base64
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# GITHUB MCP V2.0 - PRACTICAL EDITION
# ============================================================================
# Features:
# - Level 1: Rate limiting, caching, error handling
# - Level 2: 9 tools, file size checks, token optimization
# ============================================================================

mcp = FastMCP("GitHub MCP V2.0 Practical")
_github_client = None

# ============================================================================
# LEVEL 1: PERFORMANCE FEATURES
# ============================================================================

# Rate limiting: 100 requests/hour per tool
RATE_LIMIT = 100
RATE_WINDOW = 3600  # 1 hour in seconds
rate_limiter = defaultdict(list)

# Caching: 5 minutes for file contents
CACHE_TTL = 300  # 5 minutes
cache = {}

def check_rate_limit(tool_name: str) -> bool:
    """Check if tool is within rate limit"""
    now = time.time()
    # Clean old entries
    rate_limiter[tool_name] = [t for t in rate_limiter[tool_name] if now - t < RATE_WINDOW]
    
    if len(rate_limiter[tool_name]) >= RATE_LIMIT:
        return False
    
    rate_limiter[tool_name].append(now)
    return True

def get_cached(key: str) -> Optional[Dict]:
    """Get value from cache if not expired"""
    if key in cache:
        value, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return value
        else:
            del cache[key]
    return None

def set_cache(key: str, value: Dict):
    """Set value in cache with current timestamp"""
    cache[key] = (value, time.time())

# ============================================================================
# GITHUB CLIENT
# ============================================================================

def get_github_client():
    global _github_client
    if _github_client is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN not set")
        _github_client = Github(token)
    return _github_client

# ============================================================================
# LEVEL 2: ENHANCED TOOLS (9 total)
# ============================================================================

@mcp.tool()
def create_or_update_file(
    repo: str, 
    path: str, 
    content: str, 
    message: str, 
    branch: str = "main"
) -> Dict:
    """Create or update a file in a repository
    
    Args:
        repo: Repository name (e.g., 'Product-Data-Cloud/pdc-monorepo')
        path: File path in repo
        content: File content (max 1MB)
        message: Commit message
        branch: Target branch (default: main)
    """
    if not check_rate_limit("create_or_update_file"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    # File size check (1MB limit)
    if len(content.encode('utf-8')) > 1024 * 1024:
        return {"success": False, "error": "File too large (max 1MB)"}
    
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        
        try:
            file = repository.get_contents(path, ref=branch)
            result = repository.update_file(path, message, content, file.sha, branch=branch)
            action = "updated"
        except GithubException as e:
            if e.status == 404:
                result = repository.create_file(path, message, content, branch=branch)
                action = "created"
            else:
                raise
        
        return {
            "success": True, 
            "action": action, 
            "path": path,
            "size": len(content.encode('utf-8'))
        }
    except Exception as e:
        logger.error(f"Error in create_or_update_file: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_file_contents(repo: str, path: str, branch: str = "main") -> Dict:
    """Get file contents from repository (cached for 5 min)
    
    Args:
        repo: Repository name
        path: File path
        branch: Branch name (default: main)
    """
    if not check_rate_limit("get_file_contents"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    # Check cache first
    cache_key = f"{repo}:{branch}:{path}"
    cached = get_cached(cache_key)
    if cached:
        cached["cached"] = True
        return cached
    
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        file = repository.get_contents(path, ref=branch)
        content = base64.b64decode(file.content).decode('utf-8')
        
        result = {
            "success": True, 
            "content": content,
            "size": len(content.encode('utf-8')),
            "cached": False
        }
        
        # Cache the result
        set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"Error in get_file_contents: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def list_repos(org: str = "Product-Data-Cloud") -> Dict:
    """List all repositories in organization
    
    Args:
        org: Organization name (default: Product-Data-Cloud)
    """
    if not check_rate_limit("list_repos"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    try:
        g = get_github_client()
        organization = g.get_organization(org)
        repos = organization.get_repos()
        
        repo_list = [
            {
                "name": repo.name,
                "url": repo.html_url,
                "description": repo.description,
                "private": repo.private
            }
            for repo in repos
        ]
        
        return {"success": True, "repos": repo_list, "count": len(repo_list)}
        
    except Exception as e:
        logger.error(f"Error in list_repos: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_repo_info(repo: str) -> Dict:
    """Get detailed repository information
    
    Args:
        repo: Repository name (e.g., 'Product-Data-Cloud/pdc-monorepo')
    """
    if not check_rate_limit("get_repo_info"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        
        return {
            "success": True,
            "info": {
                "name": repository.name,
                "description": repository.description,
                "private": repository.private,
                "default_branch": repository.default_branch,
                "stars": repository.stargazers_count,
                "forks": repository.forks_count,
                "open_issues": repository.open_issues_count,
                "size": repository.size,
                "created_at": repository.created_at.isoformat(),
                "updated_at": repository.updated_at.isoformat(),
                "language": repository.language
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_repo_info: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def list_branches(repo: str) -> Dict:
    """List all branches in repository
    
    Args:
        repo: Repository name
    """
    if not check_rate_limit("list_branches"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        branches = repository.get_branches()
        
        branch_list = [
            {
                "name": branch.name,
                "protected": branch.protected,
                "commit_sha": branch.commit.sha
            }
            for branch in branches
        ]
        
        return {"success": True, "branches": branch_list, "count": len(branch_list)}
        
    except Exception as e:
        logger.error(f"Error in list_branches: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_branch(repo: str, branch_name: str, from_branch: str = "main") -> Dict:
    """Create a new branch from existing branch
    
    Args:
        repo: Repository name
        branch_name: Name for new branch
        from_branch: Source branch (default: main)
    """
    if not check_rate_limit("create_branch"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        
        # Get source branch
        source = repository.get_branch(from_branch)
        
        # Create new branch
        ref = repository.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=source.commit.sha
        )
        
        return {
            "success": True,
            "branch": branch_name,
            "from": from_branch,
            "sha": source.commit.sha
        }
        
    except Exception as e:
        logger.error(f"Error in create_branch: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def search_code(query: str, repo: Optional[str] = None) -> Dict:
    """Search for code in repositories
    
    Args:
        query: Search query
        repo: Optional specific repository to search in
    """
    if not check_rate_limit("search_code"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    try:
        g = get_github_client()
        
        # Build search query
        if repo:
            search_query = f"{query} repo:{repo}"
        else:
            search_query = f"{query} org:Product-Data-Cloud"
        
        results = g.search_code(search_query)
        
        # Limit to first 10 results for token efficiency
        code_results = []
        for i, item in enumerate(results):
            if i >= 10:
                break
            code_results.append({
                "name": item.name,
                "path": item.path,
                "repo": item.repository.full_name,
                "url": item.html_url
            })
        
        return {
            "success": True,
            "results": code_results,
            "count": len(code_results),
            "total_count": results.totalCount
        }
        
    except Exception as e:
        logger.error(f"Error in search_code: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_pull_request(
    repo: str,
    title: str,
    head: str,
    base: str = "main",
    body: str = ""
) -> Dict:
    """Create a pull request
    
    Args:
        repo: Repository name
        title: PR title
        head: Head branch (source)
        base: Base branch (target, default: main)
        body: PR description
    """
    if not check_rate_limit("create_pull_request"):
        return {"success": False, "error": "Rate limit exceeded (100/hour)"}
    
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        
        pr = repository.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )
        
        return {
            "success": True,
            "pr_number": pr.number,
            "url": pr.html_url,
            "title": pr.title
        }
        
    except Exception as e:
        logger.error(f"Error in create_pull_request: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def connection_status() -> Dict:
    """Check GitHub connection and rate limit status"""
    try:
        g = get_github_client()
        user = g.get_user()
        rate_limit = g.get_rate_limit()
        
        # Get current rate limiter status
        tool_status = {}
        for tool_name, timestamps in rate_limiter.items():
            now = time.time()
            active = [t for t in timestamps if now - t < RATE_WINDOW]
            tool_status[tool_name] = {
                "used": len(active),
                "limit": RATE_LIMIT,
                "remaining": RATE_LIMIT - len(active)
            }
        
        return {
            "success": True,
            "username": user.login,
            "github_rate_limit": {
                "core": {
                    "limit": rate_limit.core.limit,
                    "remaining": rate_limit.core.remaining,
                    "reset": rate_limit.core.reset.isoformat()
                }
            },
            "mcp_rate_limits": tool_status,
            "cache_entries": len(cache),
            "version": "2.0-practical"
        }
        
    except Exception as e:
        logger.error(f"Error in connection_status: {str(e)}")
        return {"success": False, "error": str(e)}

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info("=" * 60)
    logger.info("GitHub MCP V2.0 PRACTICAL")
    logger.info("=" * 60)
    logger.info(f"Features: Rate limiting, caching, 9 tools")
    logger.info(f"Starting on port {port}")
    logger.info("=" * 60)
    
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
        )
    )
