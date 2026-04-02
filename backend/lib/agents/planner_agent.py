from lib.agents.base_agent import BaseAgent
from models.project import Project, ExecutionPlan, Task, PipelineStage, TaskStatus
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import logging

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """Plans project execution by breaking down goals into tasks"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, PipelineStage.PLANNING)
        self.system_prompt = """You are a software architecture planner. Your job is to break down user goals into actionable tasks.

Given a goal, you must output a structured execution plan in JSON format:

{
  "tasks": [
    {
      "description": "Create package.json with dependencies",
      "task_type": "create_file",
      "arguments": {"path": "/home/user/project/package.json", "content": "..."},
      "dependencies": []
    },
    {
      "description": "Install npm packages",
      "task_type": "run_command",
      "arguments": {"command": "npm install"},
      "dependencies": ["task-0"]
    }
  ],
  "architecture_decisions": {
    "framework": "React",
    "styling": "TailwindCSS",
    "backend": "Node.js/Express"
  },
  "estimated_duration_minutes": 10,
  "tech_stack": ["React", "TailwindCSS", "Node.js", "Express"]
}

Task types available:
- create_file: {"path": "...", "content": "..."}
- run_command: {"command": "...", "cwd": "..."}
- install_packages: {"packages": ["pkg1", "pkg2"], "manager": "npm|pip"}

Rules:
1. Create files before running commands that use them
2. Install dependencies before running code
3. Be specific with file paths (start with /home/user/project/)
4. Keep tasks atomic and focused
5. Include realistic code content, not placeholders
6. Max 20 tasks per plan
"""
    
    async def execute(self, project: Project, **kwargs) -> Project:
        """Generate execution plan from goal"""
        try:
            await self.emit_event(
                project.id,
                "planning_started",
                {"goal": project.goal}
            )
            
            # Create LLM chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"planner-{project.id}",
                system_message=self.system_prompt
            ).with_model("openai", "gpt-5.2")
            
            # Build prompt
            prompt = f"""Goal: {project.goal}

Create a detailed execution plan to build this. Output ONLY valid JSON, no markdown.
"""
            
            # Get plan from LLM
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Parse response
            plan_data = self._parse_plan(response)
            
            # Create ExecutionPlan
            tasks = []
            for idx, task_data in enumerate(plan_data.get("tasks", [])):
                task = Task(
                    description=task_data["description"],
                    task_type=task_data["task_type"],
                    arguments=task_data.get("arguments", {}),
                    dependencies=task_data.get("dependencies", [])
                )
                tasks.append(task)
            
            execution_plan = ExecutionPlan(
                goal=project.goal,
                tasks=tasks,
                architecture_decisions=plan_data.get("architecture_decisions", {}),
                estimated_duration_minutes=plan_data.get("estimated_duration_minutes"),
                tech_stack=plan_data.get("tech_stack", [])
            )
            
            project.execution_plan = execution_plan
            project.current_stage = PipelineStage.BUILDING
            
            await self.emit_event(
                project.id,
                "plan_created",
                {
                    "task_count": len(tasks),
                    "tech_stack": execution_plan.tech_stack,
                    "estimated_duration": execution_plan.estimated_duration_minutes
                }
            )
            
            return project
            
        except Exception as e:
            logger.error(f"PlannerAgent failed: {str(e)}")
            return await self.on_error(project, e)
    
    def _parse_plan(self, response: str) -> dict:
        """Parse LLM response into plan dict"""
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan JSON: {str(e)}")
            logger.error(f"Response was: {response}")
            raise ValueError(f"Failed to parse execution plan: {str(e)}")
