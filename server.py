from fastmcp import FastMCP
from github import Github, GithubException
import os
import base64
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("GitHub MCP")
_github_client = None

def get_github_client():
    global _github_client
    if _github_client is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN not set")
        _github_client = Github(token)
    return _github_client

@mcp.tool()
def create_or_update_file(repo: str, path: str, content: str, message: str, branch: str = "main"):
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
        return {"success": True, "action": action, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_file_contents(repo: str, path: str, branch: str = "main"):
    try:
        g = get_github_client()
        repository = g.get_repo(repo)
        file = repository.get_contents(path, ref=branch)
        content = base64.b64decode(file.content).decode('utf-8')
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def connection_status():
    try:
        g = get_github_client()
        user = g.get_user()
        return {"success": True, "username": user.login}
    except Exception as e:
        return {"success": False, "error": str(e)}
