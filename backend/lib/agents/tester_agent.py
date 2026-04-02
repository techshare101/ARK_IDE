from lib.agents.base_agent import BaseAgent
from models.project import Project, Artifact, PipelineStage
from lib.sandbox.e2b_manager import E2BSandboxManager
import logging

logger = logging.getLogger(__name__)

class TesterAgent(BaseAgent):
    """Runs tests and validates generated code"""
    
    def __init__(self, api_key: str, sandbox_manager: E2BSandboxManager):
        super().__init__(api_key, PipelineStage.TESTING)
        self.sandbox_manager = sandbox_manager
    
    async def execute(self, project: Project, **kwargs) -> Project:
        """Run tests on the generated code"""
        try:
            await self.emit_event(
                project.id,
                "test_started",
                {"sandbox_id": project.sandbox_id}
            )
            
            sandbox = await self.sandbox_manager.get_sandbox(project.id)
            if not sandbox:
                raise ValueError("Sandbox not found")
            
            # Determine test command based on tech stack
            test_command = self._get_test_command(project)
            
            if test_command:
                await self.emit_event(
                    project.id,
                    "running_tests",
                    {"command": test_command}
                )
                
                # Run tests
                result = await self.sandbox_manager.run_command(
                    sandbox,
                    test_command,
                    timeout=120.0
                )
                
                # Parse test results
                test_passed = result["success"]
                
                # Record test artifact
                artifact = Artifact(
                    artifact_type="test_result",
                    name="test_results",
                    metadata={
                        "passed": test_passed,
                        "exit_code": result["exit_code"],
                        "stdout": result["stdout"],
                        "stderr": result["stderr"]
                    }
                )
                project.artifacts.append(artifact)
                
                await self.emit_event(
                    project.id,
                    "test_result",
                    {
                        "passed": test_passed,
                        "output": result["stdout"][:500]
                    }
                )
                
                if not test_passed:
                    # Tests failed - should we retry build?
                    project.current_stage = PipelineStage.FAILED
                    project.error = f"Tests failed: {result['stderr']}"
                    return project
            else:
                # No tests to run - skip to deploy
                logger.info("No test command available, skipping tests")
                await self.emit_event(
                    project.id,
                    "test_skipped",
                    {"reason": "No test framework detected"}
                )
            
            project.current_stage = PipelineStage.DEPLOYING
            
            await self.emit_event(
                project.id,
                "test_complete",
                {"status": "passed"}
            )
            
            return project
            
        except Exception as e:
            logger.error(f"TesterAgent failed: {str(e)}")
            return await self.on_error(project, e)
    
    def _get_test_command(self, project: Project) -> str:
        """Determine test command based on tech stack"""
        if not project.execution_plan:
            return ""
        
        tech_stack = project.execution_plan.tech_stack
        
        # Check for common test frameworks
        if "React" in tech_stack or "npm" in str(tech_stack).lower():
            return "npm test -- --passWithNoTests"
        elif "Python" in tech_stack or "pytest" in str(tech_stack).lower():
            return "pytest -v"
        elif "Node.js" in tech_stack:
            return "npm test"
        
        return ""  # No test command
