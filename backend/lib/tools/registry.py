from typing import Dict, Callable, Any
import os
import subprocess
from pathlib import Path

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register the core 4 tools"""
        self.register("list_files", self.list_files)
        self.register("read_file", self.read_file)
        self.register("write_file", self.write_file)
        self.register("run_command", self.run_command)
    
    def register(self, name: str, func: Callable):
        """Register a new tool"""
        self.tools[name] = func
    
    def get_tool_schemas(self) -> list:
        """Get JSON schemas for all tools (for LLM function calling)"""
        return [
            {
                "name": "list_files",
                "description": "List files and directories in a given path",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (relative to workspace)"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to list recursively",
                            "default": False
                        }
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
                        "path": {
                            "type": "string",
                            "description": "File path to read (relative to workspace)"
                        }
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
                        "path": {
                            "type": "string",
                            "description": "File path to write (relative to workspace)"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "run_command",
                "description": "Execute a shell command (requires approval)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory for command execution",
                            "default": "."
                        }
                    },
                    "required": ["command"]
                }
            }
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Execute a tool with given arguments"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        try:
            result = await self.tools[tool_name](arguments, workspace_path)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Tool implementations
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
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"path": args["path"], "bytes_written": len(content), "success": True}
    
    async def run_command(self, args: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Execute shell command"""
        command = args["command"]
        cwd = Path(workspace_path) / args.get("cwd", ".")
        
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
            "success": result.returncode == 0
        }

# Global registry instance
tool_registry = ToolRegistry()
