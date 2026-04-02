import difflib
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FileDiff:
    """Represents a diff between two versions of a file."""
    path: str
    old_content: str
    new_content: str
    unified_diff: str
    lines_added: int
    lines_removed: int
    is_new_file: bool
    is_deleted: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_changes(self) -> bool:
        return self.old_content != self.new_content

    @property
    def change_summary(self) -> str:
        if self.is_new_file:
            return f"New file: {self.path} (+{self.lines_added} lines)"
        if self.is_deleted:
            return f"Deleted: {self.path} (-{self.lines_removed} lines)"
        return f"Modified: {self.path} (+{self.lines_added}/-{self.lines_removed})"


class FileDiffer:
    """Computes and formats diffs between file versions."""

    def compute_diff(
        self,
        path: str,
        old_content: str,
        new_content: str,
        context_lines: int = 3,
    ) -> FileDiff:
        """Compute a unified diff between two file versions."""
        is_new = not old_content and bool(new_content)
        is_deleted = bool(old_content) and not new_content

        old_lines = old_content.splitlines(keepends=True) if old_content else []
        new_lines = new_content.splitlines(keepends=True) if new_content else []

        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                n=context_lines,
            )
        )

        unified = "".join(diff_lines)
        lines_added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("++"))
        lines_removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("--"))

        return FileDiff(
            path=path,
            old_content=old_content,
            new_content=new_content,
            unified_diff=unified,
            lines_added=lines_added,
            lines_removed=lines_removed,
            is_new_file=is_new,
            is_deleted=is_deleted,
        )

    def compute_multi_diff(
        self,
        old_files: Dict[str, str],
        new_files: Dict[str, str],
    ) -> List[FileDiff]:
        """Compute diffs for multiple files at once."""
        diffs = []
        all_paths = set(old_files.keys()) | set(new_files.keys())

        for path in sorted(all_paths):
            old = old_files.get(path, "")
            new = new_files.get(path, "")
            if old != new:
                diffs.append(self.compute_diff(path, old, new))

        return diffs

    def format_diff_summary(self, diffs: List[FileDiff]) -> str:
        """Format a human-readable summary of multiple diffs."""
        if not diffs:
            return "No changes detected."

        new_files = [d for d in diffs if d.is_new_file]
        deleted = [d for d in diffs if d.is_deleted]
        modified = [d for d in diffs if not d.is_new_file and not d.is_deleted]

        total_added = sum(d.lines_added for d in diffs)
        total_removed = sum(d.lines_removed for d in diffs)

        lines = [
            f"Changes: {len(diffs)} files (+{total_added}/-{total_removed} lines)",
        ]
        if new_files:
            lines.append(f"  New ({len(new_files)}): " + ", ".join(d.path for d in new_files[:5]))
        if modified:
            lines.append(f"  Modified ({len(modified)}): " + ", ".join(d.path for d in modified[:5]))
        if deleted:
            lines.append(f"  Deleted ({len(deleted)}): " + ", ".join(d.path for d in deleted[:5]))

        return "\n".join(lines)

    def apply_patch(
        self,
        original: str,
        patch: str,
    ) -> Optional[str]:
        """Apply a unified diff patch to original content.

        Returns patched content or None if patch fails.
        """
        try:
            original_lines = original.splitlines(keepends=True)
            patched = list(difflib.restore(
                patch.splitlines(keepends=True), 2
            ))
            return "".join(patched)
        except Exception as e:
            logger.error(f"Failed to apply patch: {e}")
            return None

    def similarity_ratio(self, text_a: str, text_b: str) -> float:
        """Compute similarity ratio between two text strings (0.0 to 1.0)."""
        return difflib.SequenceMatcher(None, text_a, text_b).ratio()

    def get_changed_lines(
        self,
        old_content: str,
        new_content: str,
    ) -> Dict[str, List[int]]:
        """Get line numbers of added and removed lines."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        added_lines = []
        removed_lines = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ("replace", "delete"):
                removed_lines.extend(range(i1 + 1, i2 + 1))
            if tag in ("replace", "insert"):
                added_lines.extend(range(j1 + 1, j2 + 1))

        return {"added": added_lines, "removed": removed_lines}
