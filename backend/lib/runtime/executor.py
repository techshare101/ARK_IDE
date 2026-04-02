import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime

from lib.sandbox.e2b_client import E2BSandboxClient, CommandResult
from lib.guardrails.command_filter import validate_command, validate_file_path, validate_package_name

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when a command execution fails validation or runtime."""
    pass


class Executor:
    """Safe command executor that wraps E2B sandbox with guardrail validation."""

    def __init__(self, sandbox: E2BSandboxClient):
        self._sandbox = sandbox
        self._history: List[Dict] = []

    @property
    def history(self) -> List[Dict]:
        return list(self._history)

    async def run(
        self,
        command: str,
        workdir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 60,
        allow_failure: bool = False,
    ) -> CommandResult:
        """Run a shell command after guardrail validation."""
        valid, reason = validate_command(command)
        if not valid:
            raise ExecutionError(f"Command blocked by guardrails: {reason}")

        start = datetime.utcnow()
        logger.info(f"Executing: {command!r}")

        result = await self._sandbox.run_command(
            command,
            timeout=timeout,
            workdir=workdir,
            env=env,
        )

        duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
        self._history.append({
            "command": command,
            "exit_code": result.exit_code,
            "duration_ms": duration_ms,
            "timestamp": start.isoformat(),
        })

        if not result.success and not allow_failure:
            logger.warning(
                f"Command failed (exit {result.exit_code}): {command!r}\nstderr: {result.stderr[:500]}"
            )

        return result

    async def write_file(self, path: str, content: str):
        """Write a file to the sandbox after path validation."""
        valid, reason = validate_file_path(path)
        if not valid:
            raise ExecutionError(f"File path blocked: {reason}")
        return await self._sandbox.write_file(path, content)

    async def write_files(self, files: Dict[str, str]):
        """Write multiple files after validating all paths."""
        for path in files:
            valid, reason = validate_file_path(path)
            if not valid:
                raise ExecutionError(f"File path blocked ({path}): {reason}")
        return await self._sandbox.write_files(files)

    async def install_npm_packages(self, packages: List[str], workdir: Optional[str] = None) -> CommandResult:
        """Install npm packages after name validation."""
        for pkg in packages:
            valid, reason = validate_package_name(pkg)
            if not valid:
                raise ExecutionError(f"Package blocked: {reason}")
        cmd = f"npm install {' '.join(packages)} --save 2>&1"
        return await self.run(cmd, workdir=workdir, timeout=120, allow_failure=False)

    async def install_pip_packages(self, packages: List[str]) -> CommandResult:
        """Install pip packages after name validation."""
        for pkg in packages:
            valid, reason = validate_package_name(pkg)
            if not valid:
                raise ExecutionError(f"Package blocked: {reason}")
        cmd = f"pip install {' '.join(packages)} 2>&1"
        return await self.run(cmd, timeout=120, allow_failure=False)

    async def run_tests(
        self,
        test_command: str,
        workdir: Optional[str] = None,
        timeout: int = 120,
    ) -> CommandResult:
        """Run a test suite command."""
        return await self.run(test_command, workdir=workdir, timeout=timeout, allow_failure=True)

    async def run_build(
        self,
        build_command: str,
        workdir: Optional[str] = None,
        timeout: int = 180,
    ) -> CommandResult:
        """Run a build command."""
        return await self.run(build_command, workdir=workdir, timeout=timeout, allow_failure=False)

    async def check_file_exists(self, path: str) -> bool:
        """Check if a file exists in the sandbox."""
        result = await self._sandbox.run_command(
            f"test -f {path} && echo exists || echo missing"
        )
        return "exists" in result.stdout

    async def read_file(self, path: str) -> str:
        """Read a file from the sandbox."""
        valid, reason = validate_file_path(path)
        if not valid:
            raise ExecutionError(f"File path blocked: {reason}")
        return await self._sandbox.read_file(path)

    async def get_directory_tree(self, path: str = ".", max_depth: int = 3) -> str:
        """Get a directory tree listing."""
        result = await self._sandbox.run_command(
            f"find {path} -maxdepth {max_depth} -not -path '*/node_modules/*' "
            f"-not -path '*/.git/*' -not -path '*/__pycache__/*' "
            f"| sort | head -100"
        )
        return result.stdout or "(empty)"

    async def get_package_json(self, workdir: str = ".") -> Optional[Dict]:
        """Read and parse package.json from the sandbox."""
        import json
        content = await self._sandbox.read_file(f"{workdir}/package.json")
        if not content:
            return None
        try:
            return json.loads(content)
        except Exception:
            return None
