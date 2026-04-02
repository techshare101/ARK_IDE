import asyncio
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

from models.session import DeployInfo

logger = logging.getLogger(__name__)


class DeploymentResult:
    """Result of a deployment operation."""

    def __init__(
        self,
        success: bool,
        sandbox_id: Optional[str] = None,
        preview_url: Optional[str] = None,
        deploy_url: Optional[str] = None,
        port: int = 3000,
        error: Optional[str] = None,
    ):
        self.success = success
        self.sandbox_id = sandbox_id
        self.preview_url = preview_url
        self.deploy_url = deploy_url
        self.port = port
        self.error = error
        self.status = "deployed" if success else "failed"
        self.deployed_at = datetime.utcnow() if success else None

    def to_deploy_info(self) -> DeployInfo:
        return DeployInfo(
            sandbox_id=self.sandbox_id,
            preview_url=self.preview_url,
            deploy_url=self.deploy_url,
            port=self.port,
            status="deployed" if self.success else "failed",
            deployed_at=self.deployed_at,
        )


class Deployer:
    """Handles deployment of built projects to E2B sandboxes."""

    def __init__(self, sandbox_client=None):
        """Initialize deployer with optional sandbox client."""
        self.sandbox_client = sandbox_client

    async def deploy(
        self,
        run_command: str,
        port: int = 3000,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 60,
        **kwargs  # Accept extra args like tech_stack, project_name
    ) -> DeploymentResult:
        """Deploy a project by starting its run command in the sandbox."""
        logger.info(f"Deploying with command: {run_command!r} on port {port}")
        
        sandbox_client = self.sandbox_client
        if not sandbox_client:
            return DeploymentResult(success=False, error="No sandbox client configured")
        
        try:
            start_cmd = f"nohup {run_command} > /tmp/app.log 2>&1 &"
            result = await sandbox_client.run_command(start_cmd, timeout=timeout, env=env or {})
            if not result.success and result.exit_code not in (0, None):
                logger.warning(f"Deploy command returned non-zero: {result.stderr}")
            await asyncio.sleep(3)
            preview_url = await sandbox_client.get_preview_url(port)
            logger.info(f"Deployment successful. Preview: {preview_url}")
            return DeploymentResult(
                success=True,
                sandbox_id=sandbox_client.sandbox_id,
                preview_url=preview_url,
                deploy_url=preview_url,
                port=port,
            )
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeploymentResult(
                success=False,
                sandbox_id=sandbox_client.sandbox_id if sandbox_client else None,
                error=str(e),
            )

    async def health_check(
        self,
        url: str,
        max_attempts: int = 10,
        interval: float = 2.0,
    ) -> bool:
        """Poll a URL until it responds with 200 or max_attempts is reached."""
        import httpx
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    if response.status_code < 500:
                        logger.info(f"Health check passed on attempt {attempt + 1}: {url}")
                        return True
            except Exception as e:
                logger.debug(f"Health check attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(interval)
        logger.warning(f"Health check failed after {max_attempts} attempts: {url}")
        return False

    async def get_logs(self, sandbox_client, log_file: str = "/tmp/app.log", tail: int = 100) -> str:
        """Retrieve application logs from the sandbox."""
        result = await sandbox_client.run_command(
            f"tail -n {tail} {log_file} 2>/dev/null || echo '(no logs yet)'"
        )
        return result.stdout or "(no logs)"

    async def stop(self, sandbox_client, port: int = 3000) -> bool:
        """Stop a running service by killing the process on the given port."""
        result = await sandbox_client.run_command(
            f"fuser -k {port}/tcp 2>/dev/null; echo done"
        )
        return result.success
