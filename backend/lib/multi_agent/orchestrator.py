import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from openai import AsyncOpenAI

from models.session import (
    Project, PipelineStage, Task, TaskTree, TaskType, TaskStatus,
    FileManifest, TestResult, AgentRun,
)
from lib.sandbox.e2b_client import E2BSandboxClient
from lib.runtime.executor import Executor
from lib.deploy.deployer import Deployer
from lib.streaming.sse import SSEManager
from lib.tools.file_tools import FileTools
from lib.guardrails.command_filter import validate_command

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Multi-agent pipeline orchestrator for ARK IDE.

    Coordinates 5 specialized agents through the full build lifecycle:
      Stage 1 - Planner:   Decomposes goal into TaskTree
      Stage 2 - Builder:   Generates all source files
      Stage 3 - Tester:    Runs test suite, parses results
      Stage 4 - Deployer:  Starts app in E2B sandbox
      Stage 5 - Monitor:   Health-checks and reports
    """

    SYSTEM_PROMPTS = {
        "planner": (
            "You are an expert software architect. Given a project goal, produce a "
            "detailed JSON task tree. Respond ONLY with valid JSON matching the schema provided."
        ),
        "builder": (
            "You are an expert full-stack developer. Generate complete, production-ready "
            "source files. No placeholders, no TODOs. Every file must be fully implemented."
        ),
        "tester": (
            "You are a QA engineer. Analyze test output and extract structured results. "
            "Respond ONLY with valid JSON."
        ),
        "deployer": (
            "You are a DevOps engineer. Determine the correct commands to install dependencies "
            "and start the application. Respond ONLY with valid JSON."
        ),
        "monitor": (
            "You are a site reliability engineer. Analyze deployment status and provide "
            "a concise health report. Respond ONLY with valid JSON."
        ),
    }

    def __init__(
        self,
        sse_manager: SSEManager,
        db=None,
        openai_api_key: Optional[str] = None,
        e2b_api_key: Optional[str] = None,
    ):
        self._sse = sse_manager
        self._db = db
        self._openai = AsyncOpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY", "")
        )
        self._e2b_api_key = e2b_api_key or os.getenv("E2B_API_KEY", "")
        self._model = "gpt-4o"
        self._file_tools = FileTools()

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    async def run(self, project: Project) -> Project:
        """Execute the full pipeline for a project."""
        logger.info(f"Pipeline starting for project {project.id}: {project.goal!r}")

        sandbox = E2BSandboxClient(api_key=self._e2b_api_key)
        try:
            await sandbox.create()
            project.sandbox_id = sandbox.sandbox_id
            executor = Executor(sandbox)

            project = await self._stage_plan(project, executor)
            if project.stage == PipelineStage.FAILED:
                return project

            project = await self._stage_build(project, executor)
            if project.stage == PipelineStage.FAILED:
                return project

            project = await self._stage_test(project, executor)

            project = await self._stage_deploy(project, executor, sandbox)
            if project.stage == PipelineStage.FAILED:
                return project

            project = await self._stage_monitor(project, executor)

            project.stage = PipelineStage.COMPLETE
            deploy_url = project.deploy_info.deploy_url if project.deploy_info else None
            await self._emit(
                project.id, "pipeline_complete", "orchestrator", 5,
                "Pipeline complete",
                {"project_id": project.id, "deploy_url": deploy_url}
            )
            logger.info(f"Pipeline complete for project {project.id}")

        except Exception as e:
            logger.exception(f"Pipeline crashed for project {project.id}: {e}")
            project.stage = PipelineStage.FAILED
            project.error = str(e)
            await self._emit(
                project.id, "error", "orchestrator", 0,
                f"Pipeline failed: {e}", {"error": str(e)}
            )
        finally:
            await sandbox.close()
            await self._persist(project)

        return project

    # ------------------------------------------------------------------ #
    #  Stage 1 - Planning                                                  #
    # ------------------------------------------------------------------ #

    async def _stage_plan(self, project: Project, executor: Executor) -> Project:
        """Stage 1: Decompose goal into a TaskTree using the Planner agent."""
        project.stage = PipelineStage.PLANNING
        run = self._start_run(project, "planner", 1)
        await self._emit(project.id, "stage_start", "planner", 1, "Planning project structure...")

        schema = {
            "project_name": "string",
            "tech_stack": ["string"],
            "tasks": [
                {
                    "id": "string",
                    "type": "create_file|run_command|install_deps|write_tests",
                    "description": "string",
                    "file_path": "string or null",
                    "command": "string or null",
                    "depends_on": ["task_id"]
                }
            ],
            "test_command": "string",
            "run_command": "string",
            "estimated_files": "integer"
        }

        schema_str = json.dumps(schema, indent=2)
        prompt_lines = [
            "Project goal: " + project.goal,
            "",
            "Produce a complete task tree as JSON matching this schema:",
            schema_str,
            "",
            "Rules:",
            "- Include all files needed for a working application",
            "- install_deps tasks must come before create_file tasks that need them",
            "- Include write_tests tasks for core functionality",
            "- test_command and run_command must be valid shell commands",
            "- Respond ONLY with the JSON object, no markdown fences",
        ]
        prompt = "\n".join(prompt_lines)

        try:
            raw = await self._llm_call("planner", prompt, max_tokens=3000)
            data = self._parse_json(raw)

            tasks = []
            for t in data.get("tasks", []):
                tasks.append(Task(
                    id=t.get("id", str(uuid.uuid4())[:8]),
                    type=TaskType(t.get("type", "create_file")),
                    description=t.get("description", ""),
                    file_path=t.get("file_path"),
                    command=t.get("command"),
                    depends_on=t.get("depends_on", []),
                ))

            project.task_tree = TaskTree(
                project_name=data.get("project_name", "project"),
                tech_stack=data.get("tech_stack", []),
                tasks=tasks,
                test_command=data.get("test_command", "echo no-tests"),
                run_command=data.get("run_command", "echo no-run"),
                estimated_files=data.get("estimated_files", len(tasks)),
            )
            project.name = project.task_tree.project_name

            self._complete_run(run, {
                "task_count": len(tasks),
                "tech_stack": project.task_tree.tech_stack
            })
            await self._emit(
                project.id, "stage_complete", "planner", 1,
                "Plan ready: " + str(len(tasks)) + " tasks, stack: " + ", ".join(project.task_tree.tech_stack),
                {"task_tree": project.task_tree.model_dump()}
            )
            logger.info(f"Planning complete: {len(tasks)} tasks for {project.name}")

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            self._fail_run(run, str(e))
            project.stage = PipelineStage.FAILED
            project.error = f"Planning failed: {e}"
            await self._emit(project.id, "error", "planner", 1, f"Planning failed: {e}")

        return project

    # ------------------------------------------------------------------ #
    #  Stage 2 - Building                                                  #
    # ------------------------------------------------------------------ #

    async def _stage_build(self, project: Project, executor: Executor) -> Project:
        """Stage 2: Generate all source files using the Builder agent."""
        project.stage = PipelineStage.BUILDING
        run = self._start_run(project, "builder", 2)
        await self._emit(project.id, "stage_start", "builder", 2, "Building project files...")

        if not project.task_tree:
            project.stage = PipelineStage.FAILED
            project.error = "No task tree available for building"
            return project

        tt = project.task_tree
        files_generated: Dict[str, str] = {}
        completed_tasks: List[str] = []
        ordered = self._topological_sort(tt.tasks)

        for task in ordered:
            await self._emit(
                project.id, "task_start", "builder", 2,
                f"Task: {task.description}",
                {"task_id": task.id, "task_type": task.type}
            )
            task.status = TaskStatus.RUNNING

            try:
                if task.type == TaskType.INSTALL_DEPS:
                    cmd = task.command or ""
                    valid, _ = validate_command(cmd)
                    if valid and cmd:
                        result = await executor.run(cmd, timeout=120, allow_failure=True)
                        task.output = result.output[:500]
                    task.status = TaskStatus.COMPLETE

                elif task.type == TaskType.CREATE_FILE and task.file_path:
                    content = await self._generate_file(task, tt, files_generated, project.goal)
                    files_generated[task.file_path] = content
                    await executor.write_file(task.file_path, content)
                    task.output = f"Written: {task.file_path} ({len(content)} chars)"
                    task.status = TaskStatus.COMPLETE
                    entry = FileManifest(
                        path=task.file_path,
                        content=content,
                        size=len(content.encode("utf-8")),
                    )
                    project.file_manifest.append(entry)
                    await self._emit(
                        project.id, "file_created", "builder", 2,
                        f"Created: {task.file_path}",
                        {"path": task.file_path, "size": entry.size}
                    )

                elif task.type == TaskType.WRITE_TESTS and task.file_path:
                    content = await self._generate_test_file(task, tt, files_generated, project.goal)
                    files_generated[task.file_path] = content
                    await executor.write_file(task.file_path, content)
                    task.output = f"Tests written: {task.file_path}"
                    task.status = TaskStatus.COMPLETE
                    project.file_manifest.append(FileManifest(
                        path=task.file_path,
                        content=content,
                        size=len(content.encode("utf-8")),
                    ))

                elif task.type == TaskType.RUN_COMMAND and task.command:
                    valid, _ = validate_command(task.command)
                    if valid:
                        result = await executor.run(task.command, timeout=60, allow_failure=True)
                        task.output = result.output[:500]
                    task.status = TaskStatus.COMPLETE

                else:
                    task.status = TaskStatus.COMPLETE

                completed_tasks.append(task.id)

            except Exception as e:
                logger.warning(f"Task {task.id} failed: {e}")
                task.status = TaskStatus.FAILED
                task.error = str(e)
                await self._emit(
                    project.id, "task_failed", "builder", 2,
                    f"Task failed: {task.description} — {e}",
                    {"task_id": task.id, "error": str(e)}
                )

        total = len(tt.tasks)
        done = len(completed_tasks)
        self._complete_run(run, {"files_created": len(project.file_manifest), "tasks_done": done})
        await self._emit(
            project.id, "stage_complete", "builder", 2,
            f"Build complete: {len(project.file_manifest)} files created ({done}/{total} tasks)",
            {"files": [f.path for f in project.file_manifest]}
        )
        logger.info(f"Build complete: {len(project.file_manifest)} files for {project.name}")
        return project

    # ------------------------------------------------------------------ #
    #  Stage 3 - Testing                                                   #
    # ------------------------------------------------------------------ #

    async def _stage_test(self, project: Project, executor: Executor) -> Project:
        """Stage 3: Run test suite and parse results using the Tester agent."""
        project.stage = PipelineStage.TESTING
        run = self._start_run(project, "tester", 3)
        await self._emit(project.id, "stage_start", "tester", 3, "Running tests...")

        test_command = project.task_tree.test_command if project.task_tree else "echo no-tests"

        try:
            result = await executor.run_tests(test_command, timeout=120)
            raw_output = result.output[:3000]

            parse_prompt = (
                "Parse this test output and return JSON with keys: "
                "passed (int), failed (int), errors (int), coverage (float 0-100), success (bool).\n"
                + "Test output:\n" + raw_output + "\n\n"
                + "Respond ONLY with JSON, no markdown."
            )
            raw_json = await self._llm_call("tester", parse_prompt, max_tokens=300)
            data = self._parse_json(raw_json)

            project.test_results = TestResult(
                passed=int(data.get("passed", 0)),
                failed=int(data.get("failed", 0)),
                errors=int(data.get("errors", 0)),
                coverage=float(data.get("coverage", 0.0)),
                output=raw_output,
                success=bool(data.get("success", result.success)),
            )

            self._complete_run(run, {"passed": project.test_results.passed,
                                     "failed": project.test_results.failed})
            status_msg = (
                f"Tests: {project.test_results.passed} passed, "
                f"{project.test_results.failed} failed, "
                f"{project.test_results.errors} errors"
            )
            await self._emit(
                project.id, "stage_complete", "tester", 3,
                status_msg,
                {"test_results": project.test_results.model_dump()}
            )
            logger.info(f"Testing complete: {status_msg}")

        except Exception as e:
            logger.warning(f"Testing stage error (non-fatal): {e}")
            project.test_results = TestResult(
                output=f"Test execution error: {e}",
                success=False,
            )
            self._fail_run(run, str(e))
            await self._emit(
                project.id, "stage_complete", "tester", 3,
                f"Tests skipped: {e}",
                {"test_results": project.test_results.model_dump()}
            )

        return project

    # ------------------------------------------------------------------ #
    #  Stage 4 - Deploying                                                 #
    # ------------------------------------------------------------------ #

    async def _stage_deploy(
        self, project: Project, executor: Executor, sandbox: E2BSandboxClient
    ) -> Project:
        """Stage 4: Deploy the application in the E2B sandbox."""
        project.stage = PipelineStage.DEPLOYING
        run = self._start_run(project, "deployer", 4)
        await self._emit(project.id, "stage_start", "deployer", 4, "Deploying application...")
        try:
            deployer = Deployer(sandbox)
            run_command = project.task_tree.run_command if project.task_tree else "echo no-run"
            tech_stack = project.task_tree.tech_stack if project.task_tree else []
            result = await deployer.deploy(
                run_command=run_command,
                tech_stack=tech_stack,
                project_name=project.name or "project",
            )
            from models.session import DeployInfo
            project.deploy_info = DeployInfo(
                sandbox_id=sandbox.sandbox_id,
                preview_url=result.preview_url,
                deploy_url=result.deploy_url or result.preview_url,
                port=result.port,
                status=result.status,
                deployed_at=datetime.utcnow(),
            )
            self._complete_run(run, {
                "deploy_url": project.deploy_info.deploy_url,
                "port": result.port,
                "status": result.status,
            })
            await self._emit(
                project.id, "stage_complete", "deployer", 4,
                f"Deployed at {project.deploy_info.deploy_url}",
                {"deploy_info": project.deploy_info.model_dump()}
            )
            logger.info(f"Deploy complete: {project.deploy_info.deploy_url}")
        except Exception as e:
            logger.error(f"Deploy failed: {e}")
            self._fail_run(run, str(e))
            project.stage = PipelineStage.FAILED
            project.error = f"Deploy failed: {e}"
            await self._emit(project.id, "error", "deployer", 4, f"Deploy failed: {e}")
        return project

    # ------------------------------------------------------------------ #
    #  Stage 5 - Monitoring                                                #
    # ------------------------------------------------------------------ #

    async def _stage_monitor(self, project: Project, executor: Executor) -> Project:
        """Stage 5: Health-check the deployed application."""
        project.stage = PipelineStage.MONITORING
        run = self._start_run(project, "monitor", 5)
        await self._emit(project.id, "stage_start", "monitor", 5, "Monitoring deployment health...")
        try:
            await asyncio.sleep(3)
            port = project.deploy_info.port if project.deploy_info else 3000
            health_cmd = (
                "curl -s -o /dev/null -w '%{http_code}' "
                f"http://localhost:{port}/ || echo 000"
            )
            result = await executor.run(health_cmd, timeout=15, allow_failure=True)
            http_code = result.stdout.strip() if result.stdout else "000"
            deploy_url = project.deploy_info.deploy_url if project.deploy_info else "unknown"
            monitor_prompt = (
                "Application health check result:\n"
                + f"HTTP status code: {http_code}\n"
                + f"Deploy URL: {deploy_url}\n"
                + f"Port: {port}\n\n"
                + "Return JSON with keys: healthy (bool), status (string), message (string), "
                + "recommendations (list of strings). Respond ONLY with JSON."
            )
            raw = await self._llm_call("monitor", monitor_prompt, max_tokens=400)
            data = self._parse_json(raw)
            healthy = data.get("healthy", http_code.startswith("2"))
            status_msg = data.get("message", f"HTTP {http_code}")
            if project.deploy_info:
                project.deploy_info.status = "healthy" if healthy else "degraded"
            self._complete_run(run, {"healthy": healthy, "http_code": http_code})
            await self._emit(
                project.id, "stage_complete", "monitor", 5,
                status_msg,
                {"healthy": healthy, "http_code": http_code,
                 "recommendations": data.get("recommendations", [])}
            )
            logger.info(f"Monitor complete: healthy={healthy}, http={http_code}")
        except Exception as e:
            logger.warning(f"Monitor stage error (non-fatal): {e}")
            self._fail_run(run, str(e))
            await self._emit(
                project.id, "stage_complete", "monitor", 5,
                f"Health check skipped: {e}", {}
            )
        return project

    # ------------------------------------------------------------------ #
    #  File generation helpers                                             #
    # ------------------------------------------------------------------ #

    async def _generate_file(
        self,
        task: Task,
        tt: TaskTree,
        existing_files: Dict[str, str],
        goal: str,
    ) -> str:
        """Generate a single source file using the Builder LLM agent."""
        lang = FileTools.get_language(task.file_path or "")
        stack_str = ", ".join(tt.tech_stack)
        context_parts = []
        for fpath, content in list(existing_files.items())[-5:]:
            truncated = FileTools.truncate_for_context(content, max_tokens=300)
            context_parts.append("// " + fpath + "\n" + truncated)
        context_str = "\n".join(context_parts) if context_parts else "(no files yet)"
        prompt_lines = [
            "Project goal: " + goal,
            "Tech stack: " + stack_str,
            "File to create: " + (task.file_path or ""),
            "Task description: " + task.description,
            "Language: " + lang,
            "",
            "Recently created files for context:",
            context_str,
            "",
            "Write the COMPLETE, production-ready content for " + (task.file_path or "") + ".",
            "Rules:",
            "- No placeholders, no TODOs, no ellipsis",
            "- Include all imports, error handling, and edge cases",
            "- Follow " + lang + " best practices",
            "- Output ONLY the file content, no markdown fences, no explanation",
        ]
        prompt = "\n".join(prompt_lines)
        content = await self._llm_call("builder", prompt, max_tokens=4000)
        return self._strip_code_fences(content)

    async def _generate_test_file(
        self,
        task: Task,
        tt: TaskTree,
        existing_files: Dict[str, str],
        goal: str,
    ) -> str:
        """Generate a test file using the Builder LLM agent."""
        lang = FileTools.get_language(task.file_path or "")
        stack_str = ", ".join(tt.tech_stack)
        source_context = ""
        if task.file_path:
            test_path = task.file_path
            source_guess = (
                test_path.replace(".test.", ".")
                .replace(".spec.", ".")
                .replace("__tests__/", "")
            )
            if source_guess in existing_files:
                src = FileTools.truncate_for_context(existing_files[source_guess], 800)
                source_context = "Source file (" + source_guess + "):\n" + src
        prompt_lines = [
            "Project goal: " + goal,
            "Tech stack: " + stack_str,
            "Test file to create: " + (task.file_path or ""),
            "Task description: " + task.description,
            "",
            source_context,
            "",
            "Write COMPLETE test file for " + (task.file_path or "") + ".",
            "Rules:",
            "- Use the standard test framework for " + lang + " (jest/pytest/go test)",
            "- Cover happy paths, edge cases, and error conditions",
            "- No placeholders or TODOs",
            "- Output ONLY the file content, no markdown fences",
        ]
        prompt = "\n".join(prompt_lines)
        content = await self._llm_call("builder", prompt, max_tokens=3000)
        return self._strip_code_fences(content)

    # ------------------------------------------------------------------ #
    #  LLM helpers                                                         #
    # ------------------------------------------------------------------ #

    async def _llm_call(
        self,
        agent: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ) -> str:
        """Make a single LLM call with the given agent system prompt."""
        system = self.SYSTEM_PROMPTS.get(agent, "You are a helpful assistant.")
        response = await self._openai.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, stripping markdown fences if present."""
        import re
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            inner = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.startswith("```") and in_block:
                    break
                if in_block:
                    inner.append(line)
            text = "\n".join(inner)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'{.*}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            logger.warning(f"Failed to parse JSON from LLM: {text[:200]}")
            return {}

    @staticmethod
    def _strip_code_fences(content: str) -> str:
        """Remove markdown code fences from LLM-generated file content."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            content = "\n".join(lines)
        return content

    # ------------------------------------------------------------------ #
    #  Task ordering                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _topological_sort(tasks: List[Task]) -> List[Task]:
        """Sort tasks in dependency order using Kahn algorithm."""
        task_map = {t.id: t for t in tasks}
        in_degree: Dict[str, int] = {t.id: 0 for t in tasks}
        dependents: Dict[str, List[str]] = {t.id: [] for t in tasks}

        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id in task_map:
                    in_degree[task.id] += 1
                    dependents[dep_id].append(task.id)

        queue = [t for t in tasks if in_degree[t.id] == 0]
        result: List[Task] = []

        while queue:
            task = queue.pop(0)
            result.append(task)
            for dep_id in dependents[task.id]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    queue.append(task_map[dep_id])

        # Append remaining tasks (handles cycles gracefully)
        result_ids = {t.id for t in result}
        for task in tasks:
            if task.id not in result_ids:
                result.append(task)

        return result

    # ------------------------------------------------------------------ #
    #  AgentRun lifecycle                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _start_run(project: Project, agent: str, stage: int) -> AgentRun:
        run = AgentRun(agent=agent, stage=stage)
        project.agent_runs.append(run)
        return run

    @staticmethod
    def _complete_run(run: AgentRun, output: Optional[Dict[str, Any]] = None):
        run.completed_at = datetime.utcnow()
        run.status = "complete"
        run.output = output or {}

    @staticmethod
    def _fail_run(run: AgentRun, error: str):
        run.completed_at = datetime.utcnow()
        run.status = "failed"
        run.error = error

    # ------------------------------------------------------------------ #
    #  SSE emission                                                        #
    # ------------------------------------------------------------------ #

    async def _emit(
        self,
        project_id: str,
        event_type: str,
        agent: str = "",
        stage: int = 0,
        message: str = "",
        data: Optional[Dict[str, Any]] = None,
    ):
        """Emit an SSE event and update project in DB."""
        await self._sse.emit(
            project_id=project_id,
            event_type=event_type,
            agent=agent,
            stage=stage,
            message=message,
            data=data,
        )

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    async def _persist(self, project: Project):
        """Persist project state to MongoDB if db is available."""
        if self._db is None:
            return
        try:
            project.updated_at = datetime.utcnow()
            doc = project.model_dump()
            await self._db.projects.replace_one(
                {"id": project.id},
                doc,
                upsert=True,
            )
            logger.debug(f"Project {project.id} persisted to DB")
        except Exception as e:
            logger.error(f"Failed to persist project {project.id}: {e}")
