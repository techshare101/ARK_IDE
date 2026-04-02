import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class FileTools:
    """Utility functions for file operations used by pipeline agents."""

    # File extensions that are considered text/source files
    TEXT_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
        ".md", ".txt", ".rst", ".sh", ".bash", ".zsh", ".env",
        ".sql", ".graphql", ".proto", ".xml", ".svg", ".gitignore",
        ".dockerignore", ".editorconfig", ".eslintrc", ".prettierrc",
        ".babelrc", ".nvmrc", ".npmrc",
    }

    # Files that should never be overwritten
    PROTECTED_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        "secrets.json",
        "credentials.json",
    }

    @staticmethod
    def is_text_file(path: str) -> bool:
        """Check if a file path is a text/source file."""
        ext = Path(path).suffix.lower()
        return ext in FileTools.TEXT_EXTENSIONS

    @staticmethod
    def is_protected(path: str) -> bool:
        """Check if a file path is protected from overwriting."""
        name = Path(path).name
        return name in FileTools.PROTECTED_FILES

    @staticmethod
    def normalize_path(path: str, base_dir: str = "") -> str:
        """Normalize a file path, optionally relative to a base directory."""
        path = path.strip().lstrip("/")
        if base_dir:
            return os.path.join(base_dir, path)
        return path

    @staticmethod
    def get_language(path: str) -> str:
        """Get the programming language for a file based on its extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".sh": "bash",
            ".bash": "bash",
            ".sql": "sql",
            ".md": "markdown",
            ".graphql": "graphql",
            ".proto": "protobuf",
            ".xml": "xml",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".cs": "csharp",
        }
        ext = Path(path).suffix.lower()
        return ext_map.get(ext, "text")

    @staticmethod
    def estimate_tokens(content: str) -> int:
        """Rough estimate of token count for a string (4 chars per token)."""
        return len(content) // 4

    @staticmethod
    def truncate_for_context(content: str, max_tokens: int = 2000) -> str:
        """Truncate file content to fit within a token budget."""
        max_chars = max_tokens * 4
        if len(content) <= max_chars:
            return content
        half = max_chars // 2
        truncated = len(content) - max_chars
        separator = f"\n\n... [{truncated} chars truncated] ...\n\n"
        return content[:half] + separator + content[-half:]

    @staticmethod
    def parse_json_safe(content: str) -> Optional[Dict]:
        """Parse JSON content, returning None on failure."""
        try:
            return json.loads(content)
        except Exception:
            return None

    @staticmethod
    def build_file_tree(files: Dict[str, str], indent: int = 2) -> str:
        """Build a visual file tree from a dict of path -> content."""
        tree: Dict = {}
        for path in sorted(files.keys()):
            parts = path.strip("/").split("/")
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = None  # leaf

        def render(node: Dict, prefix: str = "") -> List[str]:
            lines = []
            items = sorted(node.items(), key=lambda x: (x[1] is None, x[0]))
            for i, (name, children) in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{name}")
                if children is not None:
                    extension = "    " if is_last else "│   "
                    lines.extend(render(children, prefix + extension))
            return lines

        return "\n".join(render(tree))

    @staticmethod
    def group_by_directory(files: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """Group files by their parent directory."""
        groups: Dict[str, Dict[str, str]] = {}
        for path, content in files.items():
            directory = str(Path(path).parent)
            if directory not in groups:
                groups[directory] = {}
            groups[directory][path] = content
        return groups

    @staticmethod
    def get_entry_point(files: Dict[str, str], tech_stack: List[str]) -> Optional[str]:
        """Detect the likely entry point file for a project."""
        stack_lower = [t.lower() for t in tech_stack]

        # React / Next.js
        if any(t in stack_lower for t in ["react", "next", "nextjs"]):
            for candidate in ["src/index.tsx", "src/index.jsx", "src/index.js",
                              "pages/index.tsx", "app/page.tsx", "index.tsx"]:
                if candidate in files:
                    return candidate

        # Node.js / Express
        if any(t in stack_lower for t in ["node", "express", "fastify"]):
            for candidate in ["src/index.js", "src/server.js", "index.js",
                              "server.js", "app.js", "src/app.js"]:
                if candidate in files:
                    return candidate

        # Python / FastAPI / Flask / Django
        if any(t in stack_lower for t in ["python", "fastapi", "flask", "django"]):
            for candidate in ["main.py", "app.py", "server.py", "manage.py",
                              "src/main.py", "src/app.py"]:
                if candidate in files:
                    return candidate

        # Go
        if "go" in stack_lower:
            for candidate in ["main.go", "cmd/main.go", "cmd/server/main.go"]:
                if candidate in files:
                    return candidate

        # Fallback: find any main/index/app file
        for name in ["main", "index", "app", "server"]:
            for path in files:
                if Path(path).stem.lower() == name:
                    return path

        return None

    @staticmethod
    def detect_port(files: Dict[str, str]) -> int:
        """Detect the port a project likely runs on from its source files."""
        import re
        port_patterns = [
            r"PORT\s*=\s*(\d{4,5})",
            r"port[\s:=]+(\d{4,5})",
            r"listen\((\d{4,5})",
            r":\s*(\d{4,5})",
        ]
        for content in files.values():
            for pattern in port_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    port = int(match.group(1))
                    if 1024 <= port <= 65535:
                        return port
        return 3000  # default

    @staticmethod
    def count_lines(files: Dict[str, str]) -> Dict[str, int]:
        """Count lines of code per file."""
        return {path: len(content.splitlines()) for path, content in files.items()}

    @staticmethod
    def total_size_bytes(files: Dict[str, str]) -> int:
        """Calculate total size of all files in bytes."""
        return sum(len(c.encode("utf-8")) for c in files.values())
