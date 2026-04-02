import logging
import os
import re
from typing import List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class CodeSummarizer:
    """Generates human-readable summaries of code and build outputs."""

    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        self._client = openai_client or AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        self._model = "gpt-4o-mini"

    async def summarize_build(
        self,
        project_name: str,
        tech_stack: List[str],
        files_created: List[str],
        test_output: str = "",
        deploy_url: Optional[str] = None,
    ) -> str:
        """Generate a concise build summary for the user."""
        files_list = "\n".join(f"  - {f}" for f in files_created[:20])
        if len(files_created) > 20:
            files_list += f"\n  ... and {len(files_created) - 20} more files"

        stack_str = ", ".join(tech_stack)
        test_str = test_output[:500] if test_output else "No tests run"
        deploy_str = deploy_url or "Not deployed"
        prompt = (
            "Summarize this software build in 3-5 sentences for a developer.\n"
            f"Project: {project_name}\n"
            f"Tech Stack: {stack_str}\n"
            f"Files Created ({len(files_created)} total):\n{files_list}\n"
            f"Test Output: {test_str}\n"
            f"Deploy URL: {deploy_str}\n"
            "Be concise, highlight what was built, key technologies used, and current status."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate build summary: {e}")
            stack_joined = ", ".join(tech_stack)
            tests_passed = "Tests passed. " if "passed" in test_output.lower() else ""
            deployed = "Deployed to " + deploy_url if deploy_url else "Ready for deployment."
            return (
                f"Built {project_name} using {stack_joined}. "
                f"Created {len(files_created)} files. "
                f"{tests_passed}{deployed}"
            )

    async def summarize_error(
        self,
        error: str,
        context: str = "",
        stage: str = "",
    ) -> str:
        """Generate a user-friendly error explanation."""
        ctx_str = context[:300] if context else "N/A"
        prompt = (
            "Explain this software build error in plain English (2-3 sentences).\n"
            "Provide one specific fix suggestion.\n"
            f"Stage: {stage or 'unknown'}\n"
            f"Context: {ctx_str}\n"
            f"Error: {error[:1000]}"
        )
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to summarize error: {e}")
            return f"Build failed at {stage} stage: {error[:200]}"

    async def summarize_test_results(
        self,
        output: str,
        passed: int,
        failed: int,
        errors: int,
    ) -> str:
        """Generate a test results summary."""
        total = passed + failed + errors
        if total == 0:
            return "No tests were executed."
        status = "all passing" if failed == 0 and errors == 0 else f"{failed} failing, {errors} errors"
        coverage_hint = ""
        match = re.search(r"(\d+(?:\.\d+)?)%", output)
        if match and "coverage" in output.lower():
            coverage_hint = f" Code coverage: {match.group(1)}%."
        all_green = failed == 0 and errors == 0
        verdict = "All checks green — ready for deployment." if all_green else "Fix failing tests before deploying."
        return f"Test suite: {passed}/{total} tests passing ({status}).{coverage_hint} {verdict}"

    async def generate_readme(
        self,
        project_name: str,
        goal: str,
        tech_stack: List[str],
        files: List[str],
        run_command: str,
        test_command: str,
        deploy_url: Optional[str] = None,
    ) -> str:
        """Generate a README.md for the project."""
        stack_str = ", ".join(tech_stack)
        files_str = ", ".join(files[:10])
        deploy_line = "Live URL: " + deploy_url if deploy_url else ""
        prompt = (
            "Generate a professional README.md for this project.\n"
            f"Project Name: {project_name}\n"
            f"Goal: {goal}\n"
            f"Tech Stack: {stack_str}\n"
            f"Key Files: {files_str}\n"
            f"Run Command: {run_command}\n"
            f"Test Command: {test_command}\n"
            f"{deploy_line}\n"
            "Include: title, description, tech stack badges, installation, usage, testing, and license sections.\n"
            "Use proper markdown formatting."
        )
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.4,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate README: {e}")
            stack_lines = "\n".join(f"- {t}" for t in tech_stack)
            return (
                f"# {project_name}\n\n"
                f"{goal}\n\n"
                f"## Tech Stack\n{stack_lines}\n\n"
                f"## Run\n```\n{run_command}\n```\n\n"
                f"## Test\n```\n{test_command}\n```\n"
            )
