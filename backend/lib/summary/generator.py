from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from typing import List, Dict, Any

class ExecutionSummaryGenerator:
    """Generate execution summaries using LLM"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.system_message = """You are an execution summary generator.

Your job is to create a concise, user-friendly summary of an agent's execution.

Given the execution history, generate a 1-2 sentence summary that:
1. States what was accomplished
2. Mentions key actions taken
3. Indicates success or failure
4. Is written for non-technical users

Examples:
- "Fixed 3 build errors in 2 files. Build now passes successfully."
- "Listed 47 files in the project directory and identified 3 configuration files."
- "Failed to execute command after 3 attempts due to permission error."

Respond with ONLY the summary, no extra text.
"""
    
    async def generate_summary(
        self,
        session_id: str,
        user_prompt: str,
        steps: List[Dict[str, Any]],
        final_status: str
    ) -> str:
        """Generate execution summary from session data"""
        
        # Build context
        context_parts = [
            f"User requested: {user_prompt}",
            f"Final status: {final_status}",
            f"Total steps: {len(steps)}",
            "\nKey actions:"
        ]
        
        # Extract key actions
        for i, step in enumerate(steps[-10:]):  # Last 10 steps
            if step.get('type') == 'tool':
                tool_call = step.get('tool_call', {})
                tool_name = tool_call.get('tool_name', 'unknown')
                result = tool_call.get('result', {})
                success = result.get('success', False)
                
                status_icon = '✓' if success else '✗'
                context_parts.append(f"  {status_icon} {tool_name}")
        
        context = "\n".join(context_parts)
        
        try:
            # Generate summary
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"summary-{session_id}",
                system_message=self.system_message
            ).with_model("openai", "gpt-5.2")
            
            user_message = UserMessage(text=context)
            summary = await chat.send_message(user_message)
            
            return summary.strip()
            
        except Exception as e:
            # Fallback to simple summary
            tool_count = sum(1 for s in steps if s.get('type') == 'tool')
            
            if final_status == "completed":
                return f"Completed task with {tool_count} tool executions in {len(steps)} steps."
            elif final_status == "failed":
                return f"Task failed after {len(steps)} steps and {tool_count} tool attempts."
            else:
                return f"Task {final_status} after {len(steps)} steps."
