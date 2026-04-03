import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SandboxFile:
    """Represents a file written to the sandbox."""
    def __init__(self, path: str, content: str):
        self.path = path
        self.content = content
        self.size = len(content.encode("utf-8"))
        self.written_at = datetime.utcnow()


class CommandResult:
    """Result of a command executed in the sandbox."""
    def __init__(self, stdout: str, stderr: str, exit_code: int, duration_ms: float = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.duration_ms = duration_ms
        self.success = exit_code == 0

    @property
    def output(self) -> str:
        """Combined stdout and stderr."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(f"[stderr] {self.stderr}")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"CommandResult(exit_code={self.exit_code}, stdout={self.stdout[:100]!r})"


class E2BSandboxClient:
    """Client for E2B code interpreter sandbox.

    Provides a safe, isolated environment for executing code generated
    by the ARK IDE pipeline. Falls back to a mock implementation when
    E2B_API_KEY is not configured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY", "")
        self._sandbox = None
        self._sandbox_id: Optional[str] = None
        self._files: Dict[str, SandboxFile] = {}
        self._mock_mode = not bool(self.api_key)
        if self._mock_mode:
            logger.warning("E2B_API_KEY not set — running in mock sandbox mode")

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id

    @property
    def is_mock(self) -> bool:
        return self._mock_mode

    async def create(self, template: str = "base", timeout: int = 300) -> str:
        """Create a new sandbox instance. Returns sandbox_id."""
        if self._mock_mode:
            import uuid
            self._sandbox_id = f"mock-sandbox-{uuid.uuid4().hex[:8]}"
            logger.info(f"Mock sandbox created: {self._sandbox_id}")
            return self._sandbox_id

        try:
            from e2b import AsyncSandbox
            self._sandbox = await AsyncSandbox.create(
                api_key=self.api_key,
                timeout=timeout
            )
            self._sandbox_id = self._sandbox.sandbox_id
            logger.info(f"E2B sandbox created: {self._sandbox_id}")
            return self._sandbox_id
        except ImportError:
            logger.error("e2b not installed. Install with: pip install e2b")
            self._mock_mode = True
            return await self.create(template, timeout)
        except Exception as e:
            logger.error(f"Failed to create E2B sandbox: {e}")
            raise

    async def write_file(self, path: str, content: str) -> SandboxFile:
        """Write a file to the sandbox filesystem."""
        sandbox_file = SandboxFile(path, content)
        self._files[path] = sandbox_file

        if self._mock_mode:
            logger.debug(f"Mock: wrote file {path} ({sandbox_file.size} bytes)")
            return sandbox_file

        try:
            await self._sandbox.files.write(path, content)
            logger.debug(f"Wrote file to sandbox: {path} ({sandbox_file.size} bytes)")
            return sandbox_file
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise

    async def write_files(self, files: Dict[str, str]) -> List[SandboxFile]:
        """Write multiple files to the sandbox concurrently."""
        tasks = [self.write_file(path, content) for path, content in files.items()]
        return await asyncio.gather(*tasks)

    async def run_command(
        self,
        command: str,
        timeout: int = 60,
        workdir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        """Execute a shell command in the sandbox."""
        start = datetime.utcnow()

        if self._mock_mode:
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            mock_output = self._generate_mock_output(command)
            logger.debug(f"Mock command: {command!r} -> exit_code=0")
            return CommandResult(
                stdout=mock_output,
                stderr="",
                exit_code=0,
                duration_ms=duration,
            )

        try:
            result = await self._sandbox.commands.run(
                cmd=command,
                timeout=timeout,
                cwd=workdir or "/home/user",
            )
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            return CommandResult(
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                exit_code=result.exit_code or 0,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            logger.error(f"Command failed: {command!r} -> {e}")
            return CommandResult(
                stdout="",
                stderr=str(e),
                exit_code=1,
                duration_ms=duration,
            )

    async def run_python(self, code: str, timeout: int = 30) -> CommandResult:
        """Execute Python code in the sandbox by writing to temp file."""
        if self._mock_mode:
            mock_stdout = "# Mock Python execution\n# Code length: " + str(len(code)) + " chars\nOK"
            return CommandResult(stdout=mock_stdout, stderr="", exit_code=0)

        try:
            # Write code to temp file and execute
            temp_file = f"/tmp/python_exec_{datetime.utcnow().timestamp()}.py"
            await self.write_file(temp_file, code)
            result = await self.run_command(f"python3 {temp_file}", timeout=timeout)
            return result
        except Exception as e:
            return CommandResult(stdout="", stderr=str(e), exit_code=1)

    async def read_file(self, path: str) -> str:
        """Read a file from the sandbox filesystem."""
        if self._mock_mode:
            if path in self._files:
                return self._files[path].content
            return ""

        try:
            content = await self._sandbox.files.read(path)
            return content
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return ""

    async def list_files(self, path: str = "/") -> List[str]:
        """List files in a sandbox directory."""
        if self._mock_mode:
            return list(self._files.keys())

        # E2B v1.0 doesn't have direct file listing
        # Use shell command instead
        try:
            result = await self.run_command(f"find {path} -maxdepth 1 -type f")
            if result.success:
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return []
        except Exception as e:
            logger.error(f"Failed to list files at {path}: {e}")
            return []

    async def get_preview_url(self, port: int = 3000) -> Optional[str]:
        """Get the preview URL for a running service in the sandbox."""
        if self._mock_mode:
            return f"http://localhost:{port}"

        try:
            host = self._sandbox.get_host(port)
            return f"https://{host}"
        except Exception as e:
            logger.error(f"Failed to get preview URL for port {port}: {e}")
            return None

    async def close(self):
        """Close and destroy the sandbox."""
        if self._mock_mode:
            logger.info(f"Mock sandbox closed: {self._sandbox_id}")
            self._sandbox_id = None
            return

        if self._sandbox:
            try:
                await self._sandbox.kill()
                logger.info(f"E2B sandbox closed: {self._sandbox_id}")
            except Exception as e:
                logger.error(f"Error closing sandbox: {e}")
            finally:
                self._sandbox = None
                self._sandbox_id = None

    def _generate_mock_output(self, command: str) -> str:
        """Generate realistic mock output for common commands."""
        cmd = command.strip().lower()
        if cmd.startswith("npm install") or cmd.startswith("npm i "):
            return "added 142 packages in 3.2s\n\n14 packages are looking for funding\n  run `npm fund` for details"
        if cmd.startswith("pip install"):
            return "Successfully installed packages"
        if cmd.startswith("npm test") or cmd.startswith("npx jest"):
            return "PASS src/App.test.js\n  ✓ renders without crashing (42ms)\n\nTest Suites: 1 passed, 1 total\nTests:       3 passed, 3 total\nTime:        1.234s"
        if cmd.startswith("npm run build"):
            return "Creating an optimized production build...\nCompiled successfully.\n\nFile sizes after gzip:\n  48.23 kB  build/static/js/main.chunk.js"
        if cmd.startswith("npm start") or cmd.startswith("node "):
            return "Server running on port 3000"
        if cmd.startswith("python") or cmd.startswith("python3"):
            return "Script executed successfully"
        if cmd.startswith("ls"):
            return "src/\npackage.json\nREADME.md\nnode_modules/"
        if cmd.startswith("cat"):
            return "(file contents)"
        return f"Command executed: {command}"

    async def __aenter__(self):
        await self.create()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def create_sandbox(api_key: Optional[str] = None) -> E2BSandboxClient:
    """Factory function to create and initialize a sandbox."""
    client = E2BSandboxClient(api_key=api_key)
    await client.create()
    return client
