from e2b import AsyncSandbox
from typing import Optional, Dict, List
import logging
import asyncio

logger = logging.getLogger(__name__)

class E2BSandboxManager:
    """Manages E2B sandbox lifecycle"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.sandboxes: Dict[str, AsyncSandbox] = {}
    
    async def create_sandbox(
        self,
        sandbox_id: str,
        timeout_seconds: int = 300,
    ) -> AsyncSandbox:
        """Create a new E2B sandbox"""
        try:
            logger.info(f"Creating E2B sandbox: {sandbox_id}")
            
            sandbox = await AsyncSandbox.create(
                api_key=self.api_key,
                timeout=timeout_seconds,
            )
            
            self.sandboxes[sandbox_id] = sandbox
            logger.info(f"Sandbox created: {sandbox.sandbox_id}")
            return sandbox
            
        except Exception as e:
            logger.error(f"Failed to create sandbox {sandbox_id}: {str(e)}")
            raise
    
    async def get_sandbox(self, sandbox_id: str) -> Optional[AsyncSandbox]:
        """Get existing sandbox"""
        return self.sandboxes.get(sandbox_id)
    
    async def cleanup_sandbox(self, sandbox_id: str) -> bool:
        """Terminate and cleanup sandbox"""
        try:
            if sandbox_id not in self.sandboxes:
                logger.warning(f"Sandbox not found: {sandbox_id}")
                return False
            
            sandbox = self.sandboxes[sandbox_id]
            await sandbox.kill()
            del self.sandboxes[sandbox_id]
            
            logger.info(f"Sandbox cleaned up: {sandbox_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up sandbox {sandbox_id}: {str(e)}")
            self.sandboxes.pop(sandbox_id, None)
            return False
    
    async def write_file(
        self,
        sandbox: AsyncSandbox,
        file_path: str,
        content: str
    ) -> None:
        """Write a single file to sandbox"""
        try:
            logger.debug(f"Writing file: {file_path}")
            await sandbox.files.write(file_path, content)
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {str(e)}")
            raise
    
    async def write_files(
        self,
        sandbox: AsyncSandbox,
        files: List[Dict[str, str]]  # [{"path": "...", "content": "..."}]
    ) -> None:
        """Write multiple files to sandbox"""
        try:
            logger.info(f"Writing {len(files)} files to sandbox")
            
            # Convert to E2B format
            file_list = [
                {"path": f["path"], "data": f["content"]}
                for f in files
            ]
            
            await sandbox.files.write(file_list)
            logger.info(f"Successfully wrote {len(files)} files")
            
        except Exception as e:
            logger.error(f"Failed to write files: {str(e)}")
            raise
    
    async def run_command(
        self,
        sandbox: AsyncSandbox,
        command: str,
        cwd: str = "/home/user/project",
        timeout: float = 60.0
    ) -> Dict[str, any]:
        """Execute command in sandbox"""
        try:
            logger.info(f"Executing command: {command}")
            
            result = await sandbox.commands.run(
                cmd=command,
                cwd=cwd,
                timeout=timeout,
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "success": result.exit_code == 0
            }
            
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise
    
    async def start_server(
        self,
        sandbox: AsyncSandbox,
        port: int = 3000,
        command: str = "npm start"
    ) -> str:
        """Start HTTP server and return public URL"""
        try:
            logger.info(f"Starting server on port {port}")
            
            # Start server in background
            await sandbox.commands.run(
                cmd=command,
                cwd="/home/user/project",
                background=True,
            )
            
            # Wait for server to be ready
            await asyncio.sleep(5)
            
            # Get public URL
            host = sandbox.getHost(port)
            public_url = f"https://{host}"
            
            logger.info(f"Server started at: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to start server: {str(e)}")
            raise
