import subprocess
from typing import Dict, Any, List
from pathlib import Path

class GitTool:
    """Git operations tool"""
    
    @staticmethod
    async def git_status(workspace_path: str) -> Dict[str, Any]:
        """Get git status"""
        result = subprocess.run(
            ['git', 'status', '--short'],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status = line[:2]
                filepath = line[3:]
                files.append({'status': status, 'file': filepath})
        
        return {
            'files': files,
            'clean': len(files) == 0
        }
    
    @staticmethod
    async def git_diff(workspace_path: str, file_path: str = None) -> Dict[str, Any]:
        """Get git diff"""
        cmd = ['git', 'diff']
        if file_path:
            cmd.append(file_path)
        
        result = subprocess.run(
            cmd,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            'diff': result.stdout,
            'has_changes': bool(result.stdout.strip())
        }
    
    @staticmethod
    async def git_log(workspace_path: str, limit: int = 10) -> Dict[str, Any]:
        """Get git log"""
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%ae|%ad|%s'],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) == 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })
        
        return {'commits': commits}
    
    @staticmethod
    async def git_add(workspace_path: str, file_path: str) -> Dict[str, Any]:
        """Stage file for commit"""
        result = subprocess.run(
            ['git', 'add', file_path],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            'success': result.returncode == 0,
            'stderr': result.stderr
        }
    
    @staticmethod
    async def git_commit(workspace_path: str, message: str) -> Dict[str, Any]:
        """Commit staged changes"""
        result = subprocess.run(
            ['git', 'commit', '-m', message],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'stderr': result.stderr
        }

git_tool = GitTool()
