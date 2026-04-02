from typing import Dict, Callable, Any
import os
import subprocess
from pathlib import Path
from lib.guardrails.command_filter import command_guardrail
from lib.tools.git_tool import git_tool
from lib.tools.web_tool import web_tool
from lib.utils.retry import retry_with_backoff, RetryConfig

class EnhancedToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all available tools"""
        # Core tools
        self.register("list_files", self.list_files)
        self.register("read_file", self.read_file)
        self.register("write_file", self.write_file)
        self.register("run_command", self.run_command)
        
        # Git tools
        self.register("git_status", self.git_status)
        self.register("git_diff", self.git_diff)
        self.register("git_log", self.git_log)
        self.register("git_add", self.git_add)
        self.register("git_commit", self.git_commit)
        
        # Web tools
        self.register("fetch_url", self.fetch_url)
        self.register("web_search", self.web_search)
    
    def register(self, name: str, func: Callable):
        """Register a new tool"""
        self.tools[name] = func
    
    def get_tool_schemas(self) -> list:
        """Get JSON schemas for all tools (for LLM function calling)"""
        return [
            # Core tools
            {
                "name": "list_files",
                "description": "List files and directories in a given path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path to list (relative to workspace)"},
                        "recursive": {"type": "boolean", "description": "Whether to list recursively", "default": False}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read (relative to workspace)"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file (creates or overwrites)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write (relative to workspace)"},
                        "content": {"type": "string", "description": "Content to write to the file"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "run_command",
                "description": "Execute a shell command (requires approval for high-risk commands)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"},
                        "cwd": {"type": "string", "description": "Working directory for command execution", "default": "."}
                    },
                    "required": ["command"]
                }
            },
            # Git tools
            {
                "name": "git_status",
                "description": "Get git repository status showing modified files",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "git_diff",
                "description": "Show git diff for changes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Optional specific file to diff"}
                    }
                }
            },
            {
                "name": "git_log",
                "description": "Show git commit history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of commits to show", "default": 10}
                    }
                }
            },
            {
                "name": "git_add",
                "description": "Stage a file for commit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "File to stage"}
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "git_commit",
                "description": "Commit staged changes with a message",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Commit message"}
                    },
                    "required": ["message"]
                }
            },
            # Web tools
            {
                "name": "fetch_url",
                "description": "Fetch content from a URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch"},
                        "timeout": {"type": "integer", "description": "Request timeout in seconds", "default": 30}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web using DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results to return", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Execute a tool with given arguments"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        try:
            # Apply retry logic with exponential backoff
            config = RetryConfig(max_attempts=3, initial_delay=1.0)
            result = await retry_with_backoff(
                self.tools[tool_name],
                arguments,
                workspace_path,
                config=config
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Core tool implementations
    async def list_files(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """List files in a directory"""
        path = Path(workspace_path) / args["path"]
        recursive = args.get("recursive", False)
        
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if not path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")
        
        files = []
        if recursive:
            for item in path.rglob("*"):
                rel_path = item.relative_to(workspace_path)
                files.append({
                    "path": str(rel_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
        else:
            for item in path.iterdir():
                rel_path = item.relative_to(workspace_path)
                files.append({
                    "path": str(rel_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
        
        return {"files": files, "count": len(files)}
    
    async def read_file(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Read file contents"""
        path = Path(workspace_path) / args["path"]
        
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")
        
        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"path": args["path"], "content": content, "size": len(content)}
    
    async def write_file(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Write content to file"""
        path = Path(workspace_path) / args["path"]
        content = args["content"]
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Store original content for diff if file exists
        original_content = None
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "path": args["path"],
            "bytes_written": len(content),
            "success": True,
            "original_content": original_content
        }
    
    async def run_command(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Execute shell command with guardrails"""
        command = args["command"]
        cwd = Path(workspace_path) / args.get("cwd", ".")
        
        # Apply command guardrails
        is_safe, risk_level, reason = command_guardrail.check_command(command)
        
        if not is_safe:
            raise PermissionError(f"Command blocked: {reason}")
        
        # Sanitize command
        command = command_guardrail.sanitize_command(command)
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
            "risk_level": risk_level
        }
    
    # Git tool wrappers
    async def git_status(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        return await git_tool.git_status(workspace_path)
    
    async def git_diff(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        file_path = args.get("file_path")
        return await git_tool.git_diff(workspace_path, file_path)
    
    async def git_log(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        limit = args.get("limit", 10)
        return await git_tool.git_log(workspace_path, limit)
    
    async def git_add(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        return await git_tool.git_add(workspace_path, args["file_path"])
    
    async def git_commit(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        return await git_tool.git_commit(workspace_path, args["message"])
    
    # Web tool wrappers
    async def fetch_url(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        timeout = args.get("timeout", 30)
        return await web_tool.fetch_url(args["url"], timeout)
    
    async def web_search(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        num_results = args.get("num_results", 5)
        return await web_tool.web_search(args["query"], num_results)

# Global enhanced registry instance
enhanced_tool_registry = EnhancedToolRegistry()
