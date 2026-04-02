from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import os
from typing import Dict, Any, Optional

class Planner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.system_message = """You are an AI agent planner. Your job is to decide the next action.

You can use these tools:
- list_files: List files in a directory
- read_file: Read file contents
- write_file: Write/create a file
- run_command: Execute shell commands (requires approval)

Respond with ONLY valid JSON in this exact format:
{
  "thought": "your reasoning about what to do next",
  "action": "tool" or "done" or "error",
  "tool_name": "name_of_tool" (only if action is "tool"),
  "tool_args": {"arg1": "value1"} (only if action is "tool"),
  "summary": "task completion summary" (only if action is "done")
}

Rules:
1. Always think before acting
2. Use tools systematically to accomplish the user's goal
3. When task is complete, set action to "done" with a summary
4. If you encounter an unrecoverable error, set action to "error"
5. For run_command, explain why it's needed - it requires user approval
"""
    
    async def plan_next_step(self, 
                            session_id: str,
                            user_prompt: str, 
                            history: list,
                            tool_schemas: list) -> Dict[str, Any]:
        """Plan the next step based on current state"""
        
        # Build context message
        context_parts = [f"User request: {user_prompt}\n"]
        
        if history:
            context_parts.append("\nExecution history:")
            for i, step in enumerate(history[-10:]):  # Last 10 steps
                context_parts.append(f"\nStep {i + 1}:")
                context_parts.append(f"Type: {step.get('type')}")
                if step.get('content'):
                    context_parts.append(f"Content: {step.get('content')}")
                if step.get('tool_call'):
                    tc = step['tool_call']
                    context_parts.append(f"Tool: {tc.get('tool_name')}")
                    context_parts.append(f"Result: {tc.get('result')}")
        
        context_parts.append("\nDecide the next action:")
        context = "\n".join(context_parts)
        
        # Create chat instance
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"planner-{session_id}",
            system_message=self.system_message
        ).with_model("openai", "gpt-5.2")
        
        # Get response
        user_message = UserMessage(text=context)
        response = await chat.send_message(user_message)
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            response_text = response.strip()
            
            # Handle markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # Try to fix incomplete JSON by adding closing braces
            open_braces = response_text.count('{') - response_text.count('}')
            if open_braces > 0:
                response_text += '}' * open_braces
            
            decision = json.loads(response_text)
            
            # Validate structure
            if "action" not in decision:
                raise ValueError("Missing 'action' field in response")
            
            # Ensure required fields based on action
            if decision.get("action") == "tool":
                if "tool_name" not in decision or "tool_args" not in decision:
                    # Try to infer from thought
                    return {
                        "thought": decision.get("thought", "Continuing..."),
                        "action": "error",
                        "error": "Incomplete tool specification. Please be more specific."
                    }
            
            return decision
            
        except json.JSONDecodeError as e:
            # Fallback: Try to continue with a safe action
            return {
                "thought": "Previous response was malformed. Let me try a simpler approach.",
                "action": "tool",
                "tool_name": "list_files",
                "tool_args": {"path": "."}
            }
        except Exception as e:
            return {
                "thought": "Error in planner",
                "action": "error",
                "error": str(e)
            }
