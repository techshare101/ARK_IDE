from lib.agents.base_agent import BaseAgent
from models.project import Project, Artifact, PipelineStage, TaskStatus
from lib.sandbox.e2b_manager import E2BSandboxManager
import logging

logger = logging.getLogger(__name__)

class BuilderAgent(BaseAgent):
    """Executes build tasks and generates code"""
    
    def __init__(self, api_key: str, sandbox_manager: E2BSandboxManager):
        super().__init__(api_key, PipelineStage.BUILDING)
        self.sandbox_manager = sandbox_manager
    
    async def execute(self, project: Project, **kwargs) -> Project:
        """Execute all tasks in the execution plan"""
        try:
            if not project.execution_plan:
                raise ValueError("No execution plan found")
            
            await self.emit_event(
                project.id,
                "build_started",
                {"task_count": len(project.execution_plan.tasks)}
            )
            
            # Create sandbox
            sandbox = await self.sandbox_manager.create_sandbox(
                project.id,
                timeout_seconds=600  # 10 minutes
            )
            project.sandbox_id = sandbox.sandbox_id
            
            # Execute tasks in order (respecting dependencies)
            completed_tasks = set()
            total_tasks = len(project.execution_plan.tasks)
            
            for idx, task in enumerate(project.execution_plan.tasks):
                # Check dependencies
                if not self._dependencies_met(task, completed_tasks):
                    logger.warning(f"Skipping task {task.id} - dependencies not met")
                    continue
                
                task.status = TaskStatus.IN_PROGRESS
                
                await self.emit_event(
                    project.id,
                    "build_progress",
                    {
                        "current_task": idx + 1,
                        "total_tasks": total_tasks,
                        "task_description": task.description,
                        "percent": int((idx / total_tasks) * 100)
                    }
                )
                
                # Execute task based on type
                try:
                    if task.task_type == "create_file":
                        await self._create_file(sandbox, task, project)
                    elif task.task_type == "run_command":
                        await self._run_command(sandbox, task, project)
                    elif task.task_type == "install_packages":
                        await self._install_packages(sandbox, task, project)
                    else:
                        raise ValueError(f"Unknown task type: {task.task_type}")
                    
                    task.status = TaskStatus.COMPLETED
                    completed_tasks.add(task.id)
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    logger.error(f"Task failed: {task.description} - {str(e)}")
                    raise
            
            project.current_stage = PipelineStage.TESTING
            
            await self.emit_event(
                project.id,
                "build_complete",
                {
                    "tasks_completed": len(completed_tasks),
                    "artifacts_created": len(project.artifacts)
                }
            )
            
            return project
            
        except Exception as e:
            logger.error(f"BuilderAgent failed: {str(e)}")
            return await self.on_error(project, e)
    
    def _dependencies_met(self, task, completed_tasks: set) -> bool:
        """Check if all task dependencies are completed"""
        return all(dep in completed_tasks for dep in task.dependencies)
    
    async def _create_file(self, sandbox, task, project: Project):
        """Create a file in the sandbox"""
        path = task.arguments.get("path")
        content = task.arguments.get("content", "")
        
        if not path:
            raise ValueError("File path not specified")
        
        await self.sandbox_manager.write_file(sandbox, path, content)
        
        # Record artifact
        artifact = Artifact(
            artifact_type="file",
            name=path,
            content=content,
            metadata={"task_id": task.id}
        )
        project.artifacts.append(artifact)
        
        await self.emit_event(
            project.id,
            "file_created",
            {
                "filename": path,
                "size": len(content)
            }
        )
    
    async def _run_command(self, sandbox, task, project: Project):
        """Run a command in the sandbox"""
        command = task.arguments.get("command")
        cwd = task.arguments.get("cwd", "/home/user/project")
        
        if not command:
            raise ValueError("Command not specified")
        
        result = await self.sandbox_manager.run_command(
            sandbox,
            command,
            cwd=cwd,
            timeout=120.0
        )
        
        task.result = result
        
        if not result["success"]:
            raise Exception(f"Command failed: {result['stderr']}")
        
        await self.emit_event(
            project.id,
            "command_executed",
            {
                "command": command,
                "exit_code": result["exit_code"],
                "stdout": result["stdout"][:200]  # First 200 chars
            }
        )
    
    async def _install_packages(self, sandbox, task, project: Project):
        """Install packages"""
        packages = task.arguments.get("packages", [])
        manager = task.arguments.get("manager", "npm")
        
        if manager == "npm":
            command = f"npm install {' '.join(packages)}"
        elif manager == "pip":
            command = f"pip install {' '.join(packages)}"
        else:
            raise ValueError(f"Unknown package manager: {manager}")
        
        result = await self.sandbox_manager.run_command(
            sandbox,
            command,
            timeout=180.0
        )
        
        if not result["success"]:
            raise Exception(f"Package installation failed: {result['stderr']}")
        
        await self.emit_event(
            project.id,
            "packages_installed",
            {
                "manager": manager,
                "packages": packages
            }
        )
