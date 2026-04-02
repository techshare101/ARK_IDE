import difflib
from typing import Dict, List, Any
from pathlib import Path

class DiffEngine:
    """Generate and format file diffs"""
    
    @staticmethod
    def generate_unified_diff(
        original_content: str,
        new_content: str,
        filename: str = "file"
    ) -> str:
        """Generate unified diff format"""
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    @staticmethod
    def generate_side_by_side_diff(
        original_content: str,
        new_content: str
    ) -> List[Dict[str, Any]]:
        """Generate side-by-side diff data for UI"""
        original_lines = original_content.splitlines()
        new_lines = new_content.splitlines()
        
        differ = difflib.Differ()
        diff = list(differ.compare(original_lines, new_lines))
        
        result = []
        for line in diff:
            if line.startswith('  '):
                result.append({
                    'type': 'unchanged',
                    'content': line[2:],
                    'old_line': line[2:],
                    'new_line': line[2:]
                })
            elif line.startswith('- '):
                result.append({
                    'type': 'removed',
                    'content': line[2:],
                    'old_line': line[2:],
                    'new_line': None
                })
            elif line.startswith('+ '):
                result.append({
                    'type': 'added',
                    'content': line[2:],
                    'old_line': None,
                    'new_line': line[2:]
                })
        
        return result
    
    @staticmethod
    def get_file_change_summary(diffs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary statistics for file changes"""
        return {
            'additions': sum(1 for d in diffs if d['type'] == 'added'),
            'deletions': sum(1 for d in diffs if d['type'] == 'removed'),
            'unchanged': sum(1 for d in diffs if d['type'] == 'unchanged')
        }

diff_engine = DiffEngine()
